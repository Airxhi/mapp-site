import ldap

class LDAPTools():
    def __init__(self, cm):
        self.config = {
            "memberdn": "ou=People,dc=inf,dc=ed,dc=ac,dc=uk"
        }

        self.cm = cm

    def conn(self):
        return self.cm.connection()

    def get_name(self, uun):
        with self.conn() as l:
            return self.get_name_bare(uun, l)

    def get_name_bare(self, uun, l):
        ldap_filter = "uid=" + uun
        result_id = l.search(self.config['memberdn'], ldap.SCOPE_SUBTREE, ldap_filter, None)

        if result_id:
            type, data = l.result(result_id, 0)
            if data:
                dn, attrs = data[0]
                return attrs['gecos'][0]
