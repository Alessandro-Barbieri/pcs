import unittest

from pcs_test.tools.assertions import (
    AssertPcsMixin,
    ac,
)
from pcs_test.tools.misc import get_test_resource as rc
from pcs_test.tools.misc import (
    get_tmp_file,
    write_file_to_tmpfile,
)
from pcs_test.tools.pcs_runner import (
    PcsRunner,
    pcs,
)

# pylint: disable=invalid-name
# pylint: disable=no-self-use
# pylint: disable=too-many-public-methods
# pylint: disable=too-many-statements

empty_cib = rc("cib-empty.xml")


class ACLTest(unittest.TestCase, AssertPcsMixin):
    def setUp(self):
        self.temp_cib = get_tmp_file("tier1_acl")
        write_file_to_tmpfile(empty_cib, self.temp_cib)
        self.pcs_runner = PcsRunner(self.temp_cib.name)

    def tearDown(self):
        self.temp_cib.close()

    def testEnableDisable(self):
        o, r = pcs(self.temp_cib.name, "acl disable".split())
        assert r == 0
        ac(o, "")

        o, r = pcs(self.temp_cib.name, ["acl"])
        assert r == 0
        ac(o, "ACLs are disabled, run 'pcs acl enable' to enable\n\n")

        o, r = pcs(self.temp_cib.name, "acl enable".split())
        assert r == 0
        ac(o, "")

        o, r = pcs(self.temp_cib.name, ["acl"])
        assert r == 0
        ac(o, "ACLs are enabled\n\n")

        o, r = pcs(self.temp_cib.name, "acl disable".split())
        assert r == 0
        ac(o, "")

        o, r = pcs(self.temp_cib.name, ["acl"])
        assert r == 0
        ac(o, "ACLs are disabled, run 'pcs acl enable' to enable\n\n")

    def testUserGroupCreateDeleteWithRoles(self):
        o, r = pcs(
            self.temp_cib.name,
            "acl role create role1 read xpath /xpath1/ write xpath /xpath2/".split(),
        )
        assert r == 0
        ac(o, "")

        o, r = pcs(
            self.temp_cib.name,
            "acl role create role2 deny xpath /xpath3/ deny xpath /xpath4/".split(),
        )
        assert r == 0
        ac(o, "")

        o, r = pcs(
            self.temp_cib.name,
            "acl role create role3 read xpath /xpath5/ read xpath /xpath6/".split(),
        )
        assert r == 0
        ac(o, "")

        o, r = pcs(self.temp_cib.name, "acl user create user1 roleX".split())
        ac(o, "Error: ACL role 'roleX' does not exist\n")
        self.assertEqual(1, r)

        o, r = pcs(
            self.temp_cib.name,
            "acl user create user1 role1 roleX".split(),
        )
        ac(o, "Error: ACL role 'roleX' does not exist\n")
        self.assertEqual(1, r)

        o, r = pcs(self.temp_cib.name, "acl group create group1 roleX".split())
        ac(o, "Error: ACL role 'roleX' does not exist\n")
        self.assertEqual(1, r)

        o, r = pcs(
            self.temp_cib.name,
            "acl group create group1 role1 roleX".split(),
        )
        ac(o, "Error: ACL role 'roleX' does not exist\n")
        self.assertEqual(1, r)

        o, r = pcs(self.temp_cib.name, ["acl"])
        ac(
            o,
            """\
ACLs are disabled, run 'pcs acl enable' to enable

Role: role1
  Permission: read xpath /xpath1/ (role1-read)
  Permission: write xpath /xpath2/ (role1-write)
Role: role2
  Permission: deny xpath /xpath3/ (role2-deny)
  Permission: deny xpath /xpath4/ (role2-deny-1)
Role: role3
  Permission: read xpath /xpath5/ (role3-read)
  Permission: read xpath /xpath6/ (role3-read-1)
""",
        )
        self.assertEqual(0, r)

        o, r = pcs(
            self.temp_cib.name,
            "acl user create user1 role1 role2".split(),
        )
        assert r == 0
        ac(o, "")

        o, r = pcs(
            self.temp_cib.name,
            "acl group create group1 role1 role3".split(),
        )
        assert r == 0
        ac(o, "")

        o, r = pcs(self.temp_cib.name, ["acl"])
        assert r == 0
        ac(
            o,
            """\
ACLs are disabled, run 'pcs acl enable' to enable

User: user1
  Roles: role1 role2
Group: group1
  Roles: role1 role3
Role: role1
  Permission: read xpath /xpath1/ (role1-read)
  Permission: write xpath /xpath2/ (role1-write)
Role: role2
  Permission: deny xpath /xpath3/ (role2-deny)
  Permission: deny xpath /xpath4/ (role2-deny-1)
Role: role3
  Permission: read xpath /xpath5/ (role3-read)
  Permission: read xpath /xpath6/ (role3-read-1)
""",
        )

        o, r = pcs(self.temp_cib.name, "acl role create group1".split())
        assert r == 1
        ac(o, "Error: 'group1' already exists\n")

        o, r = pcs(self.temp_cib.name, "acl role create role1".split())
        assert r == 1
        ac(o, "Error: 'role1' already exists\n")

        o, r = pcs(self.temp_cib.name, "acl user create user1".split())
        assert r == 1
        ac(o, "Error: 'user1' already exists\n")

        o, r = pcs(self.temp_cib.name, "acl group create group1".split())
        assert r == 1
        ac(o, "Error: 'group1' already exists\n")

        o, r = pcs(self.temp_cib.name, "acl group create role1".split())
        assert r == 1
        ac(o, "Error: 'role1' already exists\n")

        o, r = pcs(
            self.temp_cib.name,
            "acl role assign role1 to noexist".split(),
        )
        assert r == 1
        ac(o, "Error: ACL group/ACL user 'noexist' does not exist\n")

        o, r = pcs(
            self.temp_cib.name,
            "acl role assign noexist to user1".split(),
        )
        assert r == 1
        ac(o, "Error: ACL role 'noexist' does not exist\n")

        o, r = pcs(
            self.temp_cib.name,
            "acl role assign role3 to user1".split(),
        )
        assert r == 0
        ac(o, "")

        o, r = pcs(self.temp_cib.name, ["acl"])
        assert r == 0
        ac(
            o,
            """\
ACLs are disabled, run 'pcs acl enable' to enable

User: user1
  Roles: role1 role2 role3
Group: group1
  Roles: role1 role3
Role: role1
  Permission: read xpath /xpath1/ (role1-read)
  Permission: write xpath /xpath2/ (role1-write)
Role: role2
  Permission: deny xpath /xpath3/ (role2-deny)
  Permission: deny xpath /xpath4/ (role2-deny-1)
Role: role3
  Permission: read xpath /xpath5/ (role3-read)
  Permission: read xpath /xpath6/ (role3-read-1)
""",
        )

        o, r = pcs(
            self.temp_cib.name,
            "acl role unassign noexist from user1".split(),
        )
        assert r == 1
        ac(o, "Error: Role 'noexist' is not assigned to 'user1'\n")

        o, r = pcs(
            self.temp_cib.name,
            "acl role unassign role3 from noexist".split(),
        )
        assert r == 1
        ac(o, "Error: ACL group/ACL user 'noexist' does not exist\n")

        o, r = pcs(
            self.temp_cib.name,
            "acl role unassign role3 from user1".split(),
        )
        assert r == 0
        ac(o, "")

        o, r = pcs(self.temp_cib.name, ["acl"])
        assert r == 0
        ac(
            o,
            """\
ACLs are disabled, run 'pcs acl enable' to enable

User: user1
  Roles: role1 role2
Group: group1
  Roles: role1 role3
Role: role1
  Permission: read xpath /xpath1/ (role1-read)
  Permission: write xpath /xpath2/ (role1-write)
Role: role2
  Permission: deny xpath /xpath3/ (role2-deny)
  Permission: deny xpath /xpath4/ (role2-deny-1)
Role: role3
  Permission: read xpath /xpath5/ (role3-read)
  Permission: read xpath /xpath6/ (role3-read-1)
""",
        )

        o, r = pcs(
            self.temp_cib.name,
            "acl role unassign role2 from user1".split(),
        )
        assert r == 0
        ac(o, "")

        o, r = pcs(
            self.temp_cib.name,
            "acl role unassign role1 from user1".split(),
        )
        assert r == 0
        ac(o, "")

        o, r = pcs(self.temp_cib.name, ["acl"])
        ac(
            o,
            """\
ACLs are disabled, run 'pcs acl enable' to enable

User: user1
  Roles:
Group: group1
  Roles: role1 role3
Role: role1
  Permission: read xpath /xpath1/ (role1-read)
  Permission: write xpath /xpath2/ (role1-write)
Role: role2
  Permission: deny xpath /xpath3/ (role2-deny)
  Permission: deny xpath /xpath4/ (role2-deny-1)
Role: role3
  Permission: read xpath /xpath5/ (role3-read)
  Permission: read xpath /xpath6/ (role3-read-1)
""",
        )
        assert r == 0

        o, r = pcs(self.temp_cib.name, "acl role delete role3".split())
        assert r == 0
        ac(o, "")

        o, r = pcs(self.temp_cib.name, ["acl"])
        ac(
            o,
            """\
ACLs are disabled, run 'pcs acl enable' to enable

User: user1
  Roles:
Group: group1
  Roles: role1
Role: role1
  Permission: read xpath /xpath1/ (role1-read)
  Permission: write xpath /xpath2/ (role1-write)
Role: role2
  Permission: deny xpath /xpath3/ (role2-deny)
  Permission: deny xpath /xpath4/ (role2-deny-1)
""",
        )
        assert r == 0

        o, r = pcs(
            self.temp_cib.name,
            "acl role assign role2 to user1".split(),
        )
        assert r == 0
        ac(o, "")

        o, r = pcs(self.temp_cib.name, ["acl"])
        assert r == 0
        ac(
            o,
            """\
ACLs are disabled, run 'pcs acl enable' to enable

User: user1
  Roles: role2
Group: group1
  Roles: role1
Role: role1
  Permission: read xpath /xpath1/ (role1-read)
  Permission: write xpath /xpath2/ (role1-write)
Role: role2
  Permission: deny xpath /xpath3/ (role2-deny)
  Permission: deny xpath /xpath4/ (role2-deny-1)
""",
        )

        o, r = pcs(self.temp_cib.name, "acl role assign role1 user1".split())
        ac(o, "")
        assert r == 0

        o, r = pcs(self.temp_cib.name, ["acl"])
        ac(
            o,
            """\
ACLs are disabled, run 'pcs acl enable' to enable

User: user1
  Roles: role2 role1
Group: group1
  Roles: role1
Role: role1
  Permission: read xpath /xpath1/ (role1-read)
  Permission: write xpath /xpath2/ (role1-write)
Role: role2
  Permission: deny xpath /xpath3/ (role2-deny)
  Permission: deny xpath /xpath4/ (role2-deny-1)
""",
        )
        assert r == 0

        o, r = pcs(
            self.temp_cib.name,
            "acl role unassign role2 from user1 --autodelete".split(),
        )
        ac(o, "")
        assert r == 0

        o, r = pcs(self.temp_cib.name, ["acl"])
        ac(
            o,
            """\
ACLs are disabled, run 'pcs acl enable' to enable

User: user1
  Roles: role1
Group: group1
  Roles: role1
Role: role1
  Permission: read xpath /xpath1/ (role1-read)
  Permission: write xpath /xpath2/ (role1-write)
Role: role2
  Permission: deny xpath /xpath3/ (role2-deny)
  Permission: deny xpath /xpath4/ (role2-deny-1)
""",
        )
        assert r == 0

        o, r = pcs(
            self.temp_cib.name,
            "acl role unassign role1 from user1 --autodelete".split(),
        )
        ac(o, "")
        assert r == 0

        o, r = pcs(self.temp_cib.name, ["acl"])
        ac(
            o,
            """\
ACLs are disabled, run 'pcs acl enable' to enable

Group: group1
  Roles: role1
Role: role1
  Permission: read xpath /xpath1/ (role1-read)
  Permission: write xpath /xpath2/ (role1-write)
Role: role2
  Permission: deny xpath /xpath3/ (role2-deny)
  Permission: deny xpath /xpath4/ (role2-deny-1)
""",
        )
        assert r == 0

        o, r = pcs(
            self.temp_cib.name,
            "acl user create user1 role1 role2".split(),
        )
        ac(o, "")
        assert r == 0

        o, r = pcs(self.temp_cib.name, ["acl"])
        ac(
            o,
            """\
ACLs are disabled, run 'pcs acl enable' to enable

User: user1
  Roles: role1 role2
Group: group1
  Roles: role1
Role: role1
  Permission: read xpath /xpath1/ (role1-read)
  Permission: write xpath /xpath2/ (role1-write)
Role: role2
  Permission: deny xpath /xpath3/ (role2-deny)
  Permission: deny xpath /xpath4/ (role2-deny-1)
""",
        )
        assert r == 0

        o, r = pcs(
            self.temp_cib.name,
            "acl role delete role1 --autodelete".split(),
        )
        ac(o, "")
        assert r == 0

        o, r = pcs(self.temp_cib.name, ["acl"])
        ac(
            o,
            """\
ACLs are disabled, run 'pcs acl enable' to enable

User: user1
  Roles: role2
Role: role2
  Permission: deny xpath /xpath3/ (role2-deny)
  Permission: deny xpath /xpath4/ (role2-deny-1)
""",
        )
        assert r == 0

        o, r = pcs(self.temp_cib.name, "acl role delete role2".split())
        ac(o, "")
        assert r == 0

        o, r = pcs(self.temp_cib.name, ["acl"])
        ac(
            o,
            """\
ACLs are disabled, run 'pcs acl enable' to enable

User: user1
  Roles:
""",
        )
        assert r == 0

    def testUserGroupCreateDelete(self):
        o, r = pcs(self.temp_cib.name, ["acl"])
        assert r == 0
        ac(o, "ACLs are disabled, run 'pcs acl enable' to enable\n\n")

        o, r = pcs(self.temp_cib.name, "acl user create user1".split())
        ac(o, "")
        assert r == 0

        o, r = pcs(self.temp_cib.name, "acl user create user2".split())
        assert r == 0
        ac(o, "")

        o, r = pcs(self.temp_cib.name, "acl user create user1".split())
        assert r == 1
        ac(o, "Error: 'user1' already exists\n")

        o, r = pcs(self.temp_cib.name, "acl group create group1".split())
        ac(o, "")
        assert r == 0

        o, r = pcs(self.temp_cib.name, "acl group create group2".split())
        assert r == 0
        ac(o, "")

        o, r = pcs(self.temp_cib.name, "acl group create group1".split())
        assert r == 1
        ac(o, "Error: 'group1' already exists\n")

        o, r = pcs(self.temp_cib.name, ["acl"])
        ac(
            o,
            """\
ACLs are disabled, run 'pcs acl enable' to enable

User: user1
  Roles:
User: user2
  Roles:
Group: group1
  Roles:
Group: group2
  Roles:
""",
        )
        assert r == 0

        o, r = pcs(self.temp_cib.name, "acl group delete user1".split())
        assert r == 1
        ac(o, "Error: ACL group 'user1' does not exist\n")

        o, r = pcs(self.temp_cib.name, ["acl"])
        ac(
            o,
            """\
ACLs are disabled, run 'pcs acl enable' to enable

User: user1
  Roles:
User: user2
  Roles:
Group: group1
  Roles:
Group: group2
  Roles:
""",
        )
        assert r == 0

        o, r = pcs(self.temp_cib.name, "acl group delete group2".split())
        ac(o, "")
        assert r == 0

        o, r = pcs(self.temp_cib.name, ["acl"])
        ac(
            o,
            """\
ACLs are disabled, run 'pcs acl enable' to enable

User: user1
  Roles:
User: user2
  Roles:
Group: group1
  Roles:
""",
        )
        assert r == 0

        o, r = pcs(self.temp_cib.name, "acl group remove group1".split())
        ac(o, "")
        assert r == 0

        o, r = pcs(self.temp_cib.name, ["acl"])
        ac(
            o,
            """\
ACLs are disabled, run 'pcs acl enable' to enable

User: user1
  Roles:
User: user2
  Roles:
""",
        )
        assert r == 0

        o, r = pcs(self.temp_cib.name, "acl user delete user1".split())
        ac(o, "")
        assert r == 0

        o, r = pcs(self.temp_cib.name, ["acl"])
        ac(
            o,
            """\
ACLs are disabled, run 'pcs acl enable' to enable

User: user2
  Roles:
""",
        )
        assert r == 0

        o, r = pcs(self.temp_cib.name, "acl user remove user2".split())
        ac(o, "")
        assert r == 0

        o, r = pcs(self.temp_cib.name, ["acl"])
        assert r == 0
        ac(o, "ACLs are disabled, run 'pcs acl enable' to enable\n\n")

    def testRoleCreateDelete(self):
        o, r = pcs(self.temp_cib.name, "acl role create role0 read".split())
        self.assertTrue(o.startswith("\nUsage: pcs acl role create..."))
        self.assertEqual(1, r)

        o, r = pcs(
            self.temp_cib.name,
            "acl role create role0 read //resources".split(),
        )
        self.assertTrue(o.startswith("\nUsage: pcs acl role create..."))
        self.assertEqual(1, r)

        o, r = pcs(
            self.temp_cib.name,
            "acl role create role0 read xpath".split(),
        )
        self.assertTrue(o.startswith("\nUsage: pcs acl role create..."))
        self.assertEqual(1, r)

        o, r = pcs(self.temp_cib.name, "acl role create role0 read id".split())
        self.assertTrue(o.startswith("\nUsage: pcs acl role create..."))
        self.assertEqual(1, r)

        o, r = pcs(
            self.temp_cib.name,
            "acl role create role0 readX xpath //resources".split(),
        )
        self.assertTrue(o.startswith("\nUsage: pcs acl role create..."))
        self.assertEqual(1, r)

        o, r = pcs(
            self.temp_cib.name,
            "acl role create role0 read xpathX //resources".split(),
        )
        self.assertTrue(o.startswith("\nUsage: pcs acl role create..."))
        self.assertEqual(1, r)

        o, r = pcs(
            self.temp_cib.name,
            "acl role create role0 description=test read".split(),
        )
        self.assertTrue(o.startswith("\nUsage: pcs acl role create..."))
        self.assertEqual(1, r)

        o, r = pcs(
            self.temp_cib.name,
            "acl role create role0 description=test read //resources".split(),
        )
        self.assertTrue(o.startswith("\nUsage: pcs acl role create..."))
        self.assertEqual(1, r)

        o, r = pcs(
            self.temp_cib.name,
            "acl role create role0 description=test read xpath".split(),
        )
        self.assertTrue(o.startswith("\nUsage: pcs acl role create..."))
        self.assertEqual(1, r)

        o, r = pcs(
            self.temp_cib.name,
            "acl role create role0 description=test read id".split(),
        )
        self.assertTrue(o.startswith("\nUsage: pcs acl role create..."))
        self.assertEqual(1, r)

        o, r = pcs(
            self.temp_cib.name,
            "acl role create role0 description=test readX xpath //resources".split(),
        )
        self.assertTrue(o.startswith("\nUsage: pcs acl role create..."))
        self.assertEqual(1, r)

        o, r = pcs(
            self.temp_cib.name,
            "acl role create role0 description=test read xpathX //resources".split(),
        )
        self.assertTrue(o.startswith("\nUsage: pcs acl role create..."))
        self.assertEqual(1, r)

        o, r = pcs(
            self.temp_cib.name,
            "acl role create role0 desc=test read".split(),
        )
        self.assertTrue(o.startswith("\nUsage: pcs acl role create..."))
        self.assertEqual(1, r)

        o, r = pcs(
            self.temp_cib.name,
            "acl role create role0 desc=test read //resources".split(),
        )
        self.assertTrue(o.startswith("\nUsage: pcs acl role create..."))
        self.assertEqual(1, r)

        o, r = pcs(
            self.temp_cib.name,
            "acl role create role0 desc=test read xpath".split(),
        )
        self.assertTrue(o.startswith("\nUsage: pcs acl role create..."))
        self.assertEqual(1, r)

        o, r = pcs(
            self.temp_cib.name,
            "acl role create role0 desc=test read id".split(),
        )
        self.assertTrue(o.startswith("\nUsage: pcs acl role create..."))
        self.assertEqual(1, r)

        o, r = pcs(
            self.temp_cib.name,
            "acl role create role0 desc=test readX xpath //resources".split(),
        )
        self.assertTrue(o.startswith("\nUsage: pcs acl role create..."))
        self.assertEqual(1, r)

        o, r = pcs(
            self.temp_cib.name,
            "acl role create role0 desc=test read xpathX //resources".split(),
        )
        self.assertTrue(o.startswith("\nUsage: pcs acl role create..."))
        self.assertEqual(1, r)

        o, r = pcs(self.temp_cib.name, ["acl"])
        ac(o, "ACLs are disabled, run 'pcs acl enable' to enable\n\n")
        self.assertEqual(0, r)

        o, r = pcs(self.temp_cib.name, "acl role create role0".split())
        ac(o, "")
        assert r == 0

        o, r = pcs(self.temp_cib.name, "acl role create role0".split())
        ac(o, "Error: 'role0' already exists\n")
        assert r == 1

        o, r = pcs(
            self.temp_cib.name,
            ["acl", "role", "create", "role0d", "description=empty role"],
        )
        ac(o, "")
        assert r == 0

        o, r = pcs(
            self.temp_cib.name,
            "acl role create role1 read xpath /xpath/".split(),
        )
        ac(o, "")
        assert r == 0

        o, r = pcs(
            self.temp_cib.name,
            [
                "acl",
                "role",
                "create",
                "role2",
                "description=with description",
                "READ",
                "XPATH",
                "/xpath/",
            ],
        )
        assert r == 0
        ac(o, "")

        o, r = pcs(
            self.temp_cib.name,
            (
                "acl role create role3 Read XPath /xpath_query/ wRiTe xpATH "
                "/xpath_query2/ deny xpath /xpath_query3/"
            ).split(),
        )
        assert r == 0
        ac(o, "")

        o, r = pcs(self.temp_cib.name, ["acl"])
        ac(
            o,
            """\
ACLs are disabled, run 'pcs acl enable' to enable

Role: role0
Role: role0d
  Description: empty role
Role: role1
  Permission: read xpath /xpath/ (role1-read)
Role: role2
  Description: with description
  Permission: read xpath /xpath/ (role2-read)
Role: role3
  Permission: read xpath /xpath_query/ (role3-read)
  Permission: write xpath /xpath_query2/ (role3-write)
  Permission: deny xpath /xpath_query3/ (role3-deny)
""",
        )
        assert r == 0

        o, r = pcs(self.temp_cib.name, "acl role delete role2".split())
        assert r == 0
        ac(o, "")

        o, r = pcs(self.temp_cib.name, ["acl"])
        ac(
            o,
            """\
ACLs are disabled, run 'pcs acl enable' to enable

Role: role0
Role: role0d
  Description: empty role
Role: role1
  Permission: read xpath /xpath/ (role1-read)
Role: role3
  Permission: read xpath /xpath_query/ (role3-read)
  Permission: write xpath /xpath_query2/ (role3-write)
  Permission: deny xpath /xpath_query3/ (role3-deny)
""",
        )
        assert r == 0

        o, r = pcs(self.temp_cib.name, "acl role delete role2".split())
        assert r == 1
        ac(o, "Error: ACL role 'role2' does not exist\n")

        o, r = pcs(self.temp_cib.name, "acl role delete role1".split())
        assert r == 0
        ac(o, "")

        o, r = pcs(self.temp_cib.name, "acl role remove role3".split())
        assert r == 0
        ac(o, "")

        o, r = pcs(self.temp_cib.name, "acl role remove role0".split())
        assert r == 0
        ac(o, "")

        o, r = pcs(self.temp_cib.name, "acl role remove role0d".split())
        assert r == 0
        ac(o, "")

        o, r = pcs(self.temp_cib.name, ["acl"])
        ac(o, "ACLs are disabled, run 'pcs acl enable' to enable\n\n")
        assert r == 0

    def testPermissionAddDelete(self):
        o, r = pcs(
            self.temp_cib.name,
            "acl role create role1 read xpath /xpath1/ write xpath /xpath2/".split(),
        )
        ac(o, "")
        assert r == 0

        o, r = pcs(
            self.temp_cib.name,
            "acl role create role2 read xpath /xpath3/ write xpath /xpath4/".split(),
        )
        ac(o, "")
        assert r == 0

        o, r = pcs(
            self.temp_cib.name,
            "acl role create role3 read xpath /xpath5/ write xpath /xpath6/".split(),
        )
        ac(o, "")
        assert r == 0

        o, r = pcs(self.temp_cib.name, "acl config".split())
        assert r == 0
        ac(
            o,
            """\
ACLs are disabled, run 'pcs acl enable' to enable

Role: role1
  Permission: read xpath /xpath1/ (role1-read)
  Permission: write xpath /xpath2/ (role1-write)
Role: role2
  Permission: read xpath /xpath3/ (role2-read)
  Permission: write xpath /xpath4/ (role2-write)
Role: role3
  Permission: read xpath /xpath5/ (role3-read)
  Permission: write xpath /xpath6/ (role3-write)
""",
        )

        o, r = pcs(
            self.temp_cib.name,
            "acl permission add role1 deny xpath /myxpath1/".split(),
        )
        ac(o, "")
        assert r == 0

        o, r = pcs(
            self.temp_cib.name,
            "acl permission add role4 deny xpath /myxpath2/".split(),
        )
        ac(o, "")
        assert r == 0

        o, r = pcs(self.temp_cib.name, "acl config".split())
        assert r == 0
        ac(
            o,
            """\
ACLs are disabled, run 'pcs acl enable' to enable

Role: role1
  Permission: read xpath /xpath1/ (role1-read)
  Permission: write xpath /xpath2/ (role1-write)
  Permission: deny xpath /myxpath1/ (role1-deny)
Role: role2
  Permission: read xpath /xpath3/ (role2-read)
  Permission: write xpath /xpath4/ (role2-write)
Role: role3
  Permission: read xpath /xpath5/ (role3-read)
  Permission: write xpath /xpath6/ (role3-write)
Role: role4
  Permission: deny xpath /myxpath2/ (role4-deny)
""",
        )

        o, r = pcs(
            self.temp_cib.name, "acl permission delete role4-deny".split()
        )
        ac(o, "")
        assert r == 0

        o, r = pcs(
            self.temp_cib.name, "acl permission delete role4-deny".split()
        )
        ac(o, "Error: ACL permission 'role4-deny' does not exist\n")
        assert r == 1

        o, r = pcs(
            self.temp_cib.name, "acl permission remove role4-deny".split()
        )
        ac(o, "Error: ACL permission 'role4-deny' does not exist\n")
        assert r == 1

        o, r = pcs(self.temp_cib.name, "acl config".split())
        assert r == 0
        ac(
            o,
            """\
ACLs are disabled, run 'pcs acl enable' to enable

Role: role1
  Permission: read xpath /xpath1/ (role1-read)
  Permission: write xpath /xpath2/ (role1-write)
  Permission: deny xpath /myxpath1/ (role1-deny)
Role: role2
  Permission: read xpath /xpath3/ (role2-read)
  Permission: write xpath /xpath4/ (role2-write)
Role: role3
  Permission: read xpath /xpath5/ (role3-read)
  Permission: write xpath /xpath6/ (role3-write)
Role: role4
""",
        )

        o, r = pcs(
            self.temp_cib.name, "acl permission delete role3-read".split()
        )
        ac(o, "")
        assert r == 0

        o, r = pcs(
            self.temp_cib.name, "acl permission delete role3-write".split()
        )
        ac(o, "")
        assert r == 0

        o, r = pcs(self.temp_cib.name, ["acl"])
        ac(
            o,
            """\
ACLs are disabled, run 'pcs acl enable' to enable

Role: role1
  Permission: read xpath /xpath1/ (role1-read)
  Permission: write xpath /xpath2/ (role1-write)
  Permission: deny xpath /myxpath1/ (role1-deny)
Role: role2
  Permission: read xpath /xpath3/ (role2-read)
  Permission: write xpath /xpath4/ (role2-write)
Role: role3
Role: role4
""",
        )
        assert r == 0

        o, r = pcs(
            self.temp_cib.name, "acl permission remove role1-read".split()
        )
        ac(o, "")
        self.assertEqual(0, r)

        o, r = pcs(
            self.temp_cib.name, "acl permission remove role1-write".split()
        )
        ac(o, "")
        self.assertEqual(0, r)

        o, r = pcs(
            self.temp_cib.name, "acl permission remove role1-deny".split()
        )
        ac(o, "")
        self.assertEqual(0, r)

        o, r = pcs(
            self.temp_cib.name, "acl permission remove role2-read".split()
        )
        ac(o, "")
        self.assertEqual(0, r)

        o, r = pcs(
            self.temp_cib.name, "acl permission remove role2-write".split()
        )
        ac(o, "")
        self.assertEqual(0, r)

        o, r = pcs(self.temp_cib.name, ["acl"])
        ac(
            o,
            """\
ACLs are disabled, run 'pcs acl enable' to enable

Role: role1
Role: role2
Role: role3
Role: role4
""",
        )
        self.assertEqual(0, r)

        o, r = pcs(self.temp_cib.name, "acl permission add role1 read".split())
        self.assertTrue(o.startswith("\nUsage: pcs acl permission add..."))
        self.assertEqual(1, r)

        o, r = pcs(
            self.temp_cib.name,
            "acl permission add role1 read //resources".split(),
        )
        self.assertTrue(o.startswith("\nUsage: pcs acl permission add..."))
        self.assertEqual(1, r)

        o, r = pcs(
            self.temp_cib.name,
            "acl permission add role1 read xpath".split(),
        )
        self.assertTrue(o.startswith("\nUsage: pcs acl permission add..."))
        self.assertEqual(1, r)

        o, r = pcs(
            self.temp_cib.name,
            "acl permission add role1 read id".split(),
        )
        self.assertTrue(o.startswith("\nUsage: pcs acl permission add..."))
        self.assertEqual(1, r)

        o, r = pcs(
            self.temp_cib.name,
            "acl permission add role1 readX xpath //resources".split(),
        )
        self.assertTrue(o.startswith("\nUsage: pcs acl permission add..."))
        self.assertEqual(1, r)

        o, r = pcs(
            self.temp_cib.name,
            "acl permission add role1 read xpathX //resources".split(),
        )
        self.assertTrue(o.startswith("\nUsage: pcs acl permission add..."))
        self.assertEqual(1, r)

        o, r = pcs(
            self.temp_cib.name,
            "acl permission add role1 read id dummy read".split(),
        )
        self.assertTrue(o.startswith("\nUsage: pcs acl permission add..."))
        self.assertEqual(1, r)

        o, r = pcs(
            self.temp_cib.name,
            "acl permission add role1 read id dummy read //resources".split(),
        )
        self.assertTrue(o.startswith("\nUsage: pcs acl permission add..."))
        self.assertEqual(1, r)

        o, r = pcs(
            self.temp_cib.name,
            "acl permission add role1 read id dummy read xpath".split(),
        )
        self.assertTrue(o.startswith("\nUsage: pcs acl permission add..."))
        self.assertEqual(1, r)

        o, r = pcs(
            self.temp_cib.name,
            "acl permission add role1 read id dummy read id".split(),
        )
        self.assertTrue(o.startswith("\nUsage: pcs acl permission add..."))
        self.assertEqual(1, r)

        self.assert_pcs_fail(
            "acl permission add role1 read id dummy readX xpath //resources".split(),
            stdout_start="\nUsage: pcs acl permission add...",
        )

        self.assert_pcs_fail(
            "acl permission add role1 read id dummy read xpathX //resources".split(),
            stdout_start="\nUsage: pcs acl permission add...",
        )

        o, r = pcs(self.temp_cib.name, ["acl"])
        ac(
            o,
            """\
ACLs are disabled, run 'pcs acl enable' to enable

Role: role1
Role: role2
Role: role3
Role: role4
""",
        )
        self.assertEqual(0, r)

    def test_can_add_permission_for_existing_id(self):
        self.assert_pcs_success("acl role create role1".split())
        self.assert_pcs_success("acl role create role2".split())
        self.assert_pcs_success(
            "acl permission add role1 read id role2".split()
        )

    def test_can_add_permission_for_existing_xpath(self):
        self.assert_pcs_success("acl role create role1".split())
        self.assert_pcs_success(
            "acl permission add role1 read xpath //nodes".split()
        )

    def test_can_not_add_permission_for_nonexisting_id(self):
        self.assert_pcs_success("acl role create role1".split())
        self.assert_pcs_fail(
            "acl permission add role1 read id non-existent-id".split(),
            "Error: id 'non-existent-id' does not exist\n",
        )

    def test_can_not_add_permission_for_nonexisting_id_in_later_part(self):
        self.assert_pcs_success("acl role create role1".split())
        self.assert_pcs_success("acl role create role2".split())
        self.assert_pcs_fail(
            "acl permission add role1 read id role2 read id non-existent-id".split(),
            "Error: id 'non-existent-id' does not exist\n",
        )

    def test_can_not_add_permission_for_nonexisting_role_with_bad_id(self):
        self.assert_pcs_success("acl role create role1".split())
        self.assert_pcs_fail(
            "acl permission add #bad-name read id role1".split(),
            "Error: invalid ACL role '#bad-name'"
            + ", '#' is not a valid first character for a ACL role\n",
        )

    def test_can_create_role_with_permission_for_existing_id(self):
        self.assert_pcs_success("acl role create role2".split())
        self.assert_pcs_success("acl role create role1 read id role2".split())

    def test_can_not_crate_role_with_permission_for_nonexisting_id(self):
        self.assert_pcs_fail(
            "acl role create role1 read id non-existent-id".split(),
            "Error: id 'non-existent-id' does not exist\n",
        )

    def test_can_not_create_role_with_bad_name(self):
        self.assert_pcs_fail(
            "acl role create #bad-name".split(),
            "Error: invalid ACL role '#bad-name'"
            + ", '#' is not a valid first character for a ACL role\n",
        )

    def test_fail_on_unknown_role_method(self):
        self.assert_pcs_fail(
            "acl role unknown whatever".split(),
            stdout_start="\nUsage: pcs acl role ...",
        )

    def test_assign_unassign_role_to_user(self):
        self.assert_pcs_success("acl role create role1".split())
        self.assert_pcs_success("acl user create user1".split())
        self.assert_pcs_success("acl role assign role1 user user1".split())
        self.assert_pcs_fail(
            "acl role assign role1 user user1".split(),
            "Error: Role 'role1' is already assigned to 'user1'\n",
        )
        self.assert_pcs_success("acl role unassign role1 user user1".split())
        self.assert_pcs_fail(
            "acl role unassign role1 user user1".split(),
            "Error: Role 'role1' is not assigned to 'user1'\n",
        )

    def test_assign_unassign_role_to_user_not_existing_user(self):
        self.assert_pcs_success("acl role create role1".split())
        self.assert_pcs_success("acl group create group1".split())
        self.assert_pcs_fail(
            "acl role assign role1 to user group1".split(),
            "Error: 'group1' is not an ACL user\n",
        )

    def test_assign_unassign_role_to_user_with_to(self):
        self.assert_pcs_success("acl role create role1".split())
        self.assert_pcs_success("acl user create user1".split())
        self.assert_pcs_success("acl role assign role1 to user user1".split())
        self.assert_pcs_fail(
            "acl role assign role1 to user user1".split(),
            "Error: Role 'role1' is already assigned to 'user1'\n",
        )
        self.assert_pcs_success(
            "acl role unassign role1 from user user1".split()
        )
        self.assert_pcs_fail(
            "acl role unassign role1 from user user1".split(),
            "Error: Role 'role1' is not assigned to 'user1'\n",
        )

    def test_assign_unassign_role_to_group(self):
        self.assert_pcs_success("acl role create role1".split())
        self.assert_pcs_success("acl group create group1".split())
        self.assert_pcs_success("acl role assign role1 group group1".split())
        self.assert_pcs_fail(
            "acl role assign role1 group group1".split(),
            "Error: Role 'role1' is already assigned to 'group1'\n",
        )
        self.assert_pcs_success("acl role unassign role1 group group1".split())
        self.assert_pcs_fail(
            "acl role unassign role1 group group1".split(),
            "Error: Role 'role1' is not assigned to 'group1'\n",
        )

    def test_assign_unassign_role_to_group_not_existing_group(self):
        self.assert_pcs_success("acl role create role1".split())
        self.assert_pcs_success("acl user create user1".split())
        self.assert_pcs_fail(
            "acl role assign role1 to group user1".split(),
            "Error: ACL group 'user1' does not exist\n",
        )

    def test_assign_unassign_role_to_group_with_to(self):
        self.assert_pcs_success("acl role create role1".split())
        self.assert_pcs_success("acl group create group1".split())
        self.assert_pcs_success("acl role assign role1 to group group1".split())
        self.assert_pcs_fail(
            "acl role assign role1 to group group1".split(),
            "Error: Role 'role1' is already assigned to 'group1'\n",
        )
        self.assert_pcs_success(
            "acl role unassign role1 from group group1".split()
        )
        self.assert_pcs_fail(
            "acl role unassign role1 from group group1".split(),
            "Error: Role 'role1' is not assigned to 'group1'\n",
        )
