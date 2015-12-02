from map import app, flask_redis, ldap

import hashlib
from flask import render_template, request, jsonify, redirect
from flask.ext.login import login_user, logout_user, login_required, current_user


@app.route('/')
@login_required
def index():
    room = flask_redis.hgetall("drillhall")
    dh_machines = flask_redis.lrange(room['key'] + "-machines", 0, -1)
    machines = {m: flask_redis.hgetall(m) for m in dh_machines}
    num_rows = max([int(machines[m]['row']) for m in machines])
    num_cols = max([int(machines[m]['col']) for m in machines])

    rows = []
    for r in xrange(0, num_rows+1):
        unsorted_cells = []
        for c in xrange(0, num_cols+1):
            default_cell = {'hostname': None, 'col': c, 'row': r}
            cell = [v for (k, v) in machines.iteritems() if int(v['row']) == r and int(v['col']) == c]
            if not cell:
                cell = default_cell
            else:
                cell = cell[0]
            unsorted_cells.append(cell)

        cells = unsorted_cells
        rows.append(cells)

    reserved = flask_redis.smembers('reserved-machines')

    return render_template('index.html', room=room, rows=rows, reserved=reserved)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        if ldap.check_credentials(request.form['username'], request.form['password']):
            user=ldap.getuser(request.form['username'])
            login_user(user)
            return redirect("/")

    return render_template("login.html")


@app.route("/logout")
def logout():
    logout_user()
    return redirect("/login")


#@app.route("/who")
#def whois():
#    dh_machines = flask_redis.lrange("drillhall-machines", 0, -1)
#    machines = {m: flask_redis.hgetall(m) for m in dh_machines}

#    return jsonify(users=[v['user'] for (k, v) in machines.iteritems() if "user" in v])


@app.route('/update', methods=['POST'])
def update():
    content = request.json
    host = content['hostname']
    user = content['user']
    ts = content['timestamp']
    active = content['active']

    pipe = flask_redis.pipeline()
    pipe.hset(host, "user", user)
    pipe.hset(host, "timestamp", ts)
    pipe.hset(host, "active", active)
    # Don't have to do this, secret isn't shared over net
    # and is the same for all users
    #pipe.hset(host, "secret", content['secret'])
    pipe.execute()

    return jsonify(status="ok")


@app.route("/friends", methods=['GET', 'POST'])
@login_required
def friends():
    if request.method == "POST":
        formtype = request.form.get('type')
        if formtype == "del":
            remove_friends = request.form.getlist('delfriends')
            flask_redis.srem(current_user.get_id() + "-friends", *remove_friends)
        elif formtype == "add":
            add_friend = request.form.get('newfriend')
            flask_redis.sadd(current_user.get_id() + "-friends", add_friend)

    friends = flask_redis.smembers(current_user.get_id() + "-friends")

    friends_enc = set()
    for friend in friends:
        hasher = hashlib.sha512()
        hasher.update(friend + app.config['CRYPTO_SECRET'])
        #friends_enc.add(hasher.hexdigest())
        friends_enc.add(friend)
    
    return render_template("friends.html", friends=friends)

@app.route("/i/love/you/all")
@login_required
def ily():
    for m in flask_redis.lrange('drillhall-machines', 0,-1):
        u = flask_redis.hget(m, 'user')
        if u:
            flask_redis.sadd(current_user.get_id() + '-friends', u)
    return redirect('/')
