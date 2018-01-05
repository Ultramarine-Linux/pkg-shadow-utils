#!/usr/bin/env  python
"""
A script that tests functionality of the shadow-utils package.

Author:     Jakub Hrozek, <jhrozek@redhat.com>
License:    GNU GPL v2
Date:       2007

TODO:
    * tests for password aging
    * if something fails, print out the command issued for easier debugging
    * test long options variants along with the short ones
"""

import  unittest
import  pwd
import  grp
import  commands
import  os
import  os.path
import  sys
import  copy
import  tempfile
import  rpm
import  shutil

from UserDict import UserDict

class RedHatVersion(object):
    def __init__(self, type=None, version=None, release=None):
        self.type = type
        self.version = version
        self.release = release
	self.rhel    = False

    def __eq__( self, other):
        """
        Don't compare if either of the values is None 
        so we can do comparisons like 'is it fedora?' or 'is it rhel4?'
        """
        ok = (self.type == other.type)
        if ok == False:  return False

        if self.version and other.version:
            ok = (self.version == other.version)
            if ok == False:  return False

            if (self.release == other.release):
                ok = (self.release == other.release)

        return ok

    def __ne__(  self, other):
        return not self.__eq__(other)

    def __get_fedora_info(self, mi):
        return [ (h['version'],h['release']) for h in mi ][0]

    def __get_rhel_info(self, mi):
        # The rules for RHEL versions are braindead..releases even more
        ver_rpm, rel_rpm  = [ (h['version'],h['release']) for h in mi ][0]
        rhel_versions = { '3AS' : 3, '4AS' : 4, '5Server' : 5, '5Client' : 5, '6' : 6 }
        if ver_rpm[:3] == '5.9' or ver_rpm[:1] == '6':  # rhel6 prerelease and release hack
            rhel_versions[ver_rpm] = 6
        if ver_rpm in rhel_versions.keys():
            return (rhel_versions[ver_rpm], rel_rpm)

    def is_rhel(self):
	return self.rhel

    def get_info(self):
        """
        Returns a tuple containing (type, version, release) of RHEL or Fedora.
        Type is either RHEL or Fedora.
        Returns None if it cannot parse the info
        """

        ts = rpm.TransactionSet()
        mi = ts.dbMatch()
        mi.pattern('name', rpm.RPMMIRE_GLOB, 'redhat-release*')

        if mi:
	    self.rhel = True
            return ('RHEL',) + self.__get_rhel_info(mi)
        else:
            mi = ts.dbMatch('name','fedora-release')
	    self.rhel = False
            if mi.count() != 0:
                return ('Fedora',) + self.__get_fedora_info(mi)

        return None


class UserInfo(UserDict):
    fields = { "pw_name" : 0, "pw_passwd" : 1, "pw_uid" : 2, "pw_gid" : 3,
               "pw_gecos" : 4, "pw_dir" : 5, "pw_shell" : 6 }

    def __init__(self):
        UserDict.__init__(self)
        for f in UserInfo.fields: self[f] = None

    def __getitem__(self, key):
        return UserDict.__getitem__(self, key)

    def __setitem__(self, key, value):
        UserDict.__setitem__(self, key, value)

    def __cmp__(self, other):
        return UserDict.__cmp__(self, other)

    def __repr__(self):
        return " ; ".join( [ "%s => %s" % (k, v) for k, v in self.data.items() ] )

    def __parse_info(self, struct):
        for f in UserInfo.fields: 
            self[f] = struct[UserInfo.fields[f]]

    def get_info_uid(self, uid):
        self.__parse_info(pwd.getpwuid(uid))

    def get_info_name(self, name):
        try:
            self.__parse_info(pwd.getpwnam(name))
        except KeyError:
            return None

    def lazy_compare(self, pattern):
        """ Compare pattern against self. If any field in pattern is set
        to None, it is automatically considered equal with the corresponding
        field in self. """
        for field in UserInfo.fields:
            if pattern[field] and pattern[field] != self[field]:
                return False

        return True

class GroupInfo(UserDict):
    fields = { "gr_name" : 0, "gr_passwd" : 1, 
               "gr_gid" : 2, "gr_mem" : 3}

    def __init__(self):
        UserDict.__init__(self)
        for f in GroupInfo.fields: self[f] = None

    def __getitem__(self, key):
        return UserDict.__getitem__(self, key)

    def __setitem__(self, key, value):
        UserDict.__setitem__(self, key, value)

    def __cmp__(self, other):
        return UserDict.__cmp__(self, other)

    def __repr__(self):
        return " ; ".join( [ "%s => %s" % (k, v) for k, v in self.data.items() ] )

    def __parse_info(self, struct):
        for f in GroupInfo.fields: 
            self[f] = struct[GroupInfo.fields[f]]

    def get_info_gid(self, gid):
        self.__parse_info(grp.getgrgid(gid))

    def get_info_name(self, name):
        self.__parse_info(grp.getgrnam(name))

    def lazy_compare(self, pattern):
        """ Compare pattern against self. If any field in pattern is set
        to None, it is automatically considered equal with the corresponding
        field in self. """
        for field in GroupInfo.fields:
            if pattern[field] and pattern[field] != self[field]:
                return False

        return True

class LoginDefsParser(UserDict):
    "A quick-n-dirty way how to fetch the defaults from /etc/login.defs into a dictionary"

    def __getitem__(self, key):
        try:
            return UserDict.__getitem__(self, key)
        except KeyError:
            # if a name-value is not defined in the config file, return defaults
            if key == "CREATE_MAIL_SPOOL":
                return "yes"
            if key == "UMASK":
                return "077"

    def __init__(self, path="/etc/login.defs",split=None):
        self.path = path
        UserDict.__init__(self)
        try:
            defs = open(path)
        except IOError:
            print "Could not open the config file %s" % (path)
    
        for line in defs:
            if line.startswith('#'): continue
            fields = line.split(split)
            if len(fields) != 2: continue       # yeah, we're dirty
            self.data[fields[0]] = fields[1]

    def serialize(self):
        output = open(self.path, "w+")
        for k,v in self.data.items():
            output.write("%s=%s" % (k, v))

        output.write("\n")
        output.close()

class TestUserInfo(unittest.TestCase):
    def testLazyCompare(self):
        """ (test sanity): Test comparing two UserInfo records """
        a = UserInfo()
        a["pw_name"] = "foo"
        a["pw_uid"]  = 555
        b = copy.deepcopy(a)
        c = UserInfo()

        self.assertEqual(a.lazy_compare(b), True)
        self.assertEqual(a.lazy_compare(c), True)

        c["pw_name"] = "foo"
        c["pw_uid"]   = None
        self.assertEqual(a.lazy_compare(c), True)
        self.assertEqual(c.lazy_compare(a), False)

        c["pw_name"] = "bar"
        self.assertNotEqual(a.lazy_compare(c), True)

    def testGetInfoUid(self):
        """ (test sanity): Test getting user info based on his UID """
        a = UserInfo()
        a.get_info_uid(0)
        self.assertEqual(a["pw_name"], "root")

    def testGetInfoName(self):
        """ (test sanity): Test getting user info based on his name """
        a = UserInfo()
        a.get_info_name("root")
        self.assertEqual(a["pw_uid"], 0)

class ShadowUtilsTestBase:
    """ Handy routines """ 
    def getDefaults(self):
        # get the default values for so we can compare against that
        (status, defaults_str) = commands.getstatusoutput('useradd -D')
        if status != 0: 
            raise RuntimeError("Could not get the default values for useradd")
        return dict([ rec.split("=") for rec in defaults_str.split("\n") ])

    def getDefaultUserInfo(self, username):
        expected = UserInfo()
        defaults = self.getDefaults()

        expected["pw_name"]  = username
        expected["pw_dir"]   = defaults["HOME"] + "/" + username
        expected["pw_shell"] = defaults["SHELL"]

        return expected

class TestUseradd(ShadowUtilsTestBase, unittest.TestCase):
    def setUp(self):
        self.username = "test-shadow-utils-useradd"

    def tearDown(self):
        commands.getstatusoutput("userdel -r %s" % (self.username))

    def testBasicAdd(self):
        """ useradd: Tests basic adding of a user """
        expected = self.getDefaultUserInfo(self.username)

        runme = "useradd %s" % (self.username)
        (status, output) = commands.getstatusoutput(runme)
        self.failUnlessEqual(status, 0, output)

        created = UserInfo()
        created.get_info_name(self.username)
        self.assertEqual(created.lazy_compare(expected), True, "FAIL: Could not add a user\nIssued command: %s" % (runme))

    def testExistingUser(self):
        """ useradd: Test that user with an existing name cannot be added """
        (status, output) = commands.getstatusoutput("useradd %s" % (self.username))
        self.failUnlessEqual(status, 0, output)
        self.assertNotEqual(commands.getstatusoutput("useradd %s" % (self.username))[0], 0, "FAIL: User that already exists added")

    def testCustomUID(self):
        """ useradd: Adding an user with a specific UID """
        UID = 23456 # FIXME - test for a free UID slot first

        expected = self.getDefaultUserInfo(self.username)
        expected["pw_uid"] = UID

        runme = "useradd %s -u %d" % (self.username, UID)
        (status, output) = commands.getstatusoutput(runme)
        self.failUnlessEqual(status, 0, "Issued command: %s\n" % (runme) + "Got from useradd: %s\n" % (output))

        created = UserInfo()
        created.get_info_name(self.username)
        self.assertEqual(created.lazy_compare(expected), True, "FAIL: Could not add a user with a specific UID\nIssued command: %s" % (runme))

    def testNegativeUID(self):
        """ useradd: Tests that user cannot have a negative UID assigned """
        self.assertNotEqual(commands.getstatusoutput("useradd %s --uid -5" % (self.username))[0], 0, "FAIL: User with UID < 0 added")

    def testCustomExistingUID(self):
        """ useradd: Adding a user with a specific existing UID """
        UID = 32112 

        expected = self.getDefaultUserInfo(self.username)
        expected["pw_uid"] = UID

        (status_u, output_u) = commands.getstatusoutput("useradd %s -u %d" % (self.username, UID))

        # must fail without -o flag
        (status_u_no_o, output_u_no_o) = commands.getstatusoutput("useradd foo -u %d" % (UID))

        # must pass with -o flag
        (status_o, output_o) = commands.getstatusoutput("useradd foo -u %d -o" % (UID))

        # clean up
        (status, output) = commands.getstatusoutput("userdel -r foo")

        self.failUnlessEqual(status_u, 0, "FAIL: cannot add an user with a specified UID\n"+output_u)
        self.assertEqual(status_o, 0, "FAIL: cannot add an user with an existing UID using the -o flag\n"+output_o)
        self.failUnlessEqual(status, 0, output)
        self.assertNotEqual(status_u_no_o, 0, "FAIL: user with an existing UID added\n"+output_u_no_o)

    def testCustomGID(self):
        """ useradd: Adding an user with a specific GID """
        GID = 100   # users group should be everywhere - should we test before?
        expected = self.getDefaultUserInfo(self.username)
        expected["pw_gid"]   = GID

        (status, output) = commands.getstatusoutput("useradd %s -g %d" % (self.username, GID))
        self.failUnlessEqual(status, 0, output)

        created = UserInfo()
        created.get_info_name(self.username)
        self.assertEqual(created.lazy_compare(expected), True, "FAIL: Could not add a user with a specific GID")

    def testCustomShell(self):
        """ useradd: Adding an user with a specific login shell """
        shell = "/bin/ksh"
        expected = self.getDefaultUserInfo(self.username)
        expected["pw_shell"] = shell

        (status, output) = commands.getstatusoutput("useradd %s -s %s" % (self.username, shell))
        self.failUnlessEqual(status, 0, output)

        created = UserInfo()
        created.get_info_name(self.username)
        self.assertEqual(created.lazy_compare(expected), True, "FAIL: Could not add a user with a specific shell")

    def testCustomHome(self):
        """ useradd: Adding an user with a specific home directory """
	home = "/tmp/useradd-test"
	os.mkdir(home)
        expected = self.getDefaultUserInfo(self.username)
        expected["pw_dir"] = home

        (status, output) = commands.getstatusoutput("useradd %s -d %s" % (self.username, home))
	shutil.rmtree(home)
        self.failUnlessEqual(status, 0, output)

        created = UserInfo()
        created.get_info_name(self.username)
        self.assertEqual(created.lazy_compare(expected), True, "FAIL: Could not add a user with a specific home")

    def testSystemAccount(self):
        """ useradd: Adding a system user (UID < UID_MIN from /etc/login.defs) """
        defaults = LoginDefsParser()

        # system account with no home dir
        expected = self.getDefaultUserInfo(self.username)

        (status, output) = commands.getstatusoutput("useradd -r %s" % (self.username))
        self.failUnlessEqual(status, 0, output)

        created = UserInfo()
        created.get_info_name(self.username)
        self.assertEqual(os.path.exists(created["pw_dir"]), False, "FAIL: System user has a home dir created")
        self.assertEqual(created["pw_uid"] < defaults['UID_MIN'], True, "FAIL: System user has UID > UID_MIN")
        self.assertEqual(created.lazy_compare(expected), True, "FAIL: Could not add a system user")

    def testAddToMoreGroups(self):
        """ useradd: Creating an user that belongs to more than one group """
        (status, output) = commands.getstatusoutput("useradd -G bin %s" % (self.username))
        self.failUnlessEqual(status, 0, output)

        gr_bin = GroupInfo()
        gr_bin.get_info_name("bin")
        self.assertEqual(self.username in gr_bin["gr_mem"], True, "FAIL: User not in supplementary group after usermod -G -a")


    def testAddWithCommonName(self):
        """ useradd: Specifying a comment (user for account name) """
        comment = "zzzzzz"
        (status, output) = commands.getstatusoutput("useradd -c %s %s" % (comment, self.username))
        self.failUnlessEqual(status, 0, output)

        created = UserInfo()
        created.get_info_name(self.username)
        self.assertEqual(created["pw_gecos"], comment, "FAIL: failed to create a user with a GECOS comment")

    def testHomePermissions(self):
        """ useradd: Check if permissions on newly created home dir match the umask """
        defaults = LoginDefsParser()

        (status, output) = commands.getstatusoutput("useradd %s" % (self.username))
        self.failUnlessEqual(status, 0, output)

        created = UserInfo()
        created.get_info_name(self.username)

        import stat
        perm = os.stat(created["pw_dir"])[stat.ST_MODE]
        mode = int(oct(perm & 0777))

        self.assertEqual(defaults["UMASK"], "077", "FAIL: umask setting is not sane - is %s, should be 077" % (defaults["UMASK"]))
        self.assertEqual(int(defaults["UMASK"]) + mode , 777, "FAIL: newly-created home dir does not match the umask")

    def testCreateMailSpool(self):
        """ useradd: Check whether the mail spool gets created when told to"""
        # set up creating of mail spool
        defaults = LoginDefsParser("/etc/default/useradd", split="=")
              
        create_mail = defaults["CREATE_MAIL_SPOOL"]
        defaults["CREATE_MAIL_SPOOL"] = "yes"
        defaults.serialize()

        login_defs = LoginDefsParser() 

        (status, output) = commands.getstatusoutput("useradd %s" % (self.username))
        self.failUnlessEqual(status, 0, output)

        # clean up
        defaults["CREATE_MAIL_SPOOL"] = create_mail
        defaults.serialize()
        self.assertEqual(os.path.exists(login_defs["MAIL_DIR"] + "/" + self.username), True, "FAIL: useradd did not create mail spool")

    def testDefaultMailSettings(self):
        """ useradd: Check whether the mail spool is on by default"""
        defaults = LoginDefsParser("/etc/default/useradd", split="=")
        self.assertEqual(defaults["CREATE_MAIL_SPOOL"], "yes\n")

    def testNoLastlog(self):
        """ useradd: Check if the -l option prevents from being added to the lastlog """
        pass    # FIXME - add some code here
        

class TestUseraddWeirdNameTest(unittest.TestCase, ShadowUtilsTestBase):
    """ Tests addition/removal of usernames that have proven to be problematic in the past.
    The reason to separate these from the main useradd test suite is to not run the setUp
    and tearDown methods """

    def addAndRemove(self, username, success=True):
        expected = self.getDefaultUserInfo(username)
        expected["pw_name"] = username

        (status, output) = commands.getstatusoutput("useradd %s" % (username))
        if success:
            self.failUnlessEqual(status, 0, output)
        else:
            self.failIfEqual(status, 0, output)
            return True

        created = UserInfo()
        created.get_info_name(username)
        self.assertEqual(created.lazy_compare(expected), True, "FAIL: TestUseraddWeirdName::addAndRemove - could not add a user")

        # the cleanup method won't help this time
        (status, output) = commands.getstatusoutput("userdel -r %s" % (username))
        self.failUnlessEqual(status, 0, output)

    def testNumericName(self):
        """ useradd: Test if an user with a purely numerical name can be added (123) """
        return self.addAndRemove("123")

    def testSambaName(self):
        """ useradd: Test if an user with a name with a dollar at the end can be added (joepublic$ ) """
        return self.addAndRemove("joepublic$")

    def testDotInName(self):
        """ useradd: Test if an user with a name with a dot in it can be added (joe.public ) """
        return self.addAndRemove("joe.public")

    def testAtInName(self):
        """ useradd: Test if an user with an '@' in name can be added (joe@public.com) - should fail """
        return self.addAndRemove("joe@public.com", False)

    def testUppercase(self):
        """ useradd: Test if an user with UPPERCASE or Uppercase name can be added """
        return self.addAndRemove("JOEPUBLIC")
        return self.addAndRemove("Joepublic")

class TestUseraddDefaultsChange(unittest.TestCase, ShadowUtilsTestBase):
    def testDefaultsChange(self):
        """ useradd: Test overriding default settings (shell, home dir, group) with a -D option """
        save = self.getDefaults()
        
        new_defs = dict()
        new_defs["SHELL"] = "/bin/ksh"
        new_defs["GROUP"] = "1"
        new_defs["HOME"]  = "/tmp"

        command = "useradd -D -s%s -g%s -b%s" % (new_defs["SHELL"], new_defs["GROUP"], new_defs["HOME"])
        (status, output) = commands.getstatusoutput(command)
        self.failUnlessEqual(status, 0, output)

        overriden = self.getDefaults()
        [ self.assertEqual(overriden[k], new_defs[k]) for k in new_defs.keys() ]

        command = "useradd -D -s%s -g%s -b%s" % (save["SHELL"], save["GROUP"], save["HOME"])
        (status, output) = commands.getstatusoutput(command)
        self.failUnlessEqual(status, 0, output)


class TestUserdel(unittest.TestCase, ShadowUtilsTestBase):
    def setUp(self):
        self.username = "test-shadow-utils-userdel"
        (status, output) = commands.getstatusoutput("useradd %s" % (self.username))
        self.failUnlessEqual(status, 0, output)

    def testRemoveUserGroup(self):
        """ userdel: test if userdel removes user's group when he's deleted - regression test for #201379 """
        (status, output) = commands.getstatusoutput("userdel -r %s" % (self.username))
        self.failUnlessEqual(status, 0, output)

        # This would fail if we did not have the group removed
        (status, output) = commands.getstatusoutput("useradd %s" % (self.username))
        self.failUnlessEqual(status, 0, output)

        (status, output) = commands.getstatusoutput("userdel -r %s" % (self.username))
        self.failUnlessEqual(status, 0, output)

class TestUsermod(unittest.TestCase, ShadowUtilsTestBase):
    def setUp(self):
        self.username = "test-shadow-utils-usermod"
        (status, output) = commands.getstatusoutput("useradd %s" % (self.username))
        self.failUnlessEqual(status, 0, output)

    def tearDown(self):
        (status, output) = commands.getstatusoutput("userdel -r %s" % (self.username))
        self.failUnlessEqual(status, 0, output)

    def testAppendToSupplementaryGroup(self):
        """ usermod: Test if a user can be added to a supplementary group """
        add_group = "additional_group"
        (status, output) = commands.getstatusoutput("groupadd %s" % (add_group))
        self.failUnlessEqual(status, 0, output)

        (status_mod, output_mod) = commands.getstatusoutput("usermod -a -G %s %s" % (add_group, self.username))
        add_group_info = GroupInfo()
        add_group_info.get_info_name(add_group)
        (status, output) = commands.getstatusoutput("groupdel %s" % (add_group))

        self.failUnlessEqual(status, 0, output)
        self.failUnlessEqual(status_mod, 0, output_mod)
        self.assertEqual(self.username in add_group_info["gr_mem"], True, "User not in supplementary group after usermod -G --append")


    def testAppendToSupplementaryGroupLongOption(self):
        """ usermod: Test if a user can be added to a supplementary group via --append rather that -a (regression test for 222540) """
	# this is known to not work on older RHELs - test what we are running
	rhv = RedHatVersion()
	runs = rhv.get_info()
	if rhv.is_rhel():
	    if runs[1] < 5:
		print "This test makes sense for RHEL5+"
		return 
	else:
	    if runs[1] < 6:
		print "This test makes sense for Fedora 6+"
		return 

	type, release, version = RedHatVersion().get_info()
	if RedHatVersion().is_rhel():
            if release < 5 or (release == 5 and version < 2):
                print "This test makes sense for RHEL 5.2+"
                return

        add_group = "additional_group"
        (status, output) = commands.getstatusoutput("groupadd %s" % (add_group))
        self.failUnlessEqual(status, 0, output)

        (status_mod, output_mod) = commands.getstatusoutput("usermod --append -G %s %s" % (add_group, self.username))
        add_group_info = GroupInfo()
        add_group_info.get_info_name(add_group)
        (status, output) = commands.getstatusoutput("groupdel %s" % (add_group))

        self.failUnlessEqual(status, 0, output)
        self.failUnlessEqual(status_mod, 0, output_mod)
        self.assertEqual(self.username in add_group_info["gr_mem"], True, "User not in supplementary group after usermod -G --append")


    def testNameChange(self):
        """ usermod: Test if the comment field (used as the Common Name) can be changed """
        new_comment = "zzzzzz"

        (status, output) = commands.getstatusoutput("usermod -c %s %s" % (new_comment, self.username))
        self.failUnlessEqual(status, 0, output)

        created = UserInfo()
        created.get_info_name(self.username)

        self.assertEqual(created["pw_gecos"], new_comment)

    def testHomeChange(self):
        """ usermod: Test if user's home directory can be changed """
        new_home = "/tmp"
        created = UserInfo()
        created.get_info_name(self.username)
        old_home = created["pw_dir"]

        (status, output) = commands.getstatusoutput("usermod -d %s %s" % (new_home, self.username))
        self.failUnlessEqual(status, 0, output)

        created.get_info_name(self.username)
        self.assertEqual(created["pw_dir"], new_home)

        # revert to old home so we can userdel -r in tearDown
        (status, output) = commands.getstatusoutput("usermod -d %s %s" % (old_home, self.username))
        self.failUnlessEqual(status, 0, output)

        # FIXME - test if contents of /home directories are transferred with the -m option
        # FIXME - test if new home is created if does not exist before

    def testGIDChange(self):
        """ usermod: Test if user's gid can be changed. """
        new_group = "root"
        # test non-existing group
        (status_fail, output_fail) = commands.getstatusoutput("usermod -g no-such-group %s" % (self.username))
        (status, output) = commands.getstatusoutput("usermod -g %s %s" % (new_group, self.username))

        created = UserInfo()
        created.get_info_name(self.username)

        left = GroupInfo()
        if left.get_info_name(self.username) == None:
            (status_del, output_del) = commands.getstatusoutput("groupdel %s" % (self.username))
            self.failUnlessEqual(status_del, 0, output_del)

        self.failIfEqual(status_fail, 0, output_fail)
        self.failUnlessEqual(status, 0, output)
        self.assertEqual(created["pw_gid"], 0) #0 is root group

    def testLoginChange(self):
        """ usermod: Test if user's login can be changed """
        new_login = "usermod-login-change"
        user = UserInfo()
        user.get_info_name(self.username)
        uid = user["pw_uid"]    # UID won't change even when login does

        # test changing to an existing user name
        (status, output) = commands.getstatusoutput("usermod -l root %s" % (self.username))
        self.failIfEqual(status, 0, output)

        (status, output) = commands.getstatusoutput("usermod -l %s %s" % (new_login, self.username))
        self.failUnlessEqual(status, 0, output)
        user.get_info_name(new_login)
        self.assertEqual(user["pw_uid"], uid) 

        # revert so we can userdel -r on tearDown
        (status, output) = commands.getstatusoutput("usermod -l %s %s" % (self.username, new_login))
        self.failUnlessEqual(status, 0, output)

    def testShellChange(self):
        """ usermod: Test if user's shell can be changed """
        new_shell = "/bin/sh"

        (status, output) = commands.getstatusoutput("usermod -s %s %s" % (new_shell, self.username))
        self.failUnlessEqual(status, 0, output)

        created = UserInfo()
        created.get_info_name(self.username)
        self.assertEqual(created["pw_shell"], new_shell)

class TestGroupadd(unittest.TestCase, ShadowUtilsTestBase):
    def setUp(self):
        self.groupname = "test-shadow-utils-groups"

    def tearDown(self):
        commands.getstatusoutput("groupdel %s" % (self.groupname))

    def testAddGroup(self):
        """ groupadd: Basic adding of a group """

        expected = GroupInfo()
        expected["gr_name"] = self.groupname

        (status, output) = commands.getstatusoutput("groupadd %s" % (self.groupname))
        self.failUnlessEqual(status, 0, output)

        created = GroupInfo()
        created.get_info_name(self.groupname)
        self.assertEqual(created.lazy_compare(expected), True, "FAIL: Could not add a group")

    def testAddSystemGroup(self):
        """ groupadd: Adding a system group with gid < MIN_GID """

        expected = GroupInfo()
        expected["gr_name"] = self.groupname
        defaults = LoginDefsParser()

        (status, output) = commands.getstatusoutput("groupadd -r %s" % (self.groupname))
        self.failUnlessEqual(status, 0, output)

        created = GroupInfo()
        created.get_info_name(self.groupname)
        self.assertEqual(created["gr_gid"] < defaults["GID_MIN"], True, "FAIL: System group has gid >= GID_MIN")
        self.assertEqual(created.lazy_compare(expected), True, "FAIL: Could not add a system group")

    def testAddExistingGid(self):
        """ groupadd: Test if we group with an existing GID can be added """
        (status, output) = commands.getstatusoutput("groupadd %s" % (self.groupname))
        self.failUnlessEqual(status, 0, output)

        gname = "%s-2" % (self.groupname)

        created = GroupInfo()
        created.get_info_name(self.groupname)

        # no -o option -> this should fail
        (status, output) = commands.getstatusoutput("groupadd -g%s %s" % (created["gr_gid"], gname))
        self.failIfEqual(status, 0, output)

        # override with -o option, should pass now
        (status, output) = commands.getstatusoutput("groupadd -g%s -o %s" % (created["gr_gid"], gname))
        self.failUnlessEqual(status, 0, output)

        # test if the new GID is really the same
        same_gid = GroupInfo()
        same_gid.get_info_name(gname)
        self.assertEqual(same_gid["gr_gid"], created["gr_gid"])

        # clean up
        (status, output) = commands.getstatusoutput("groupdel %s" % (gname))
        self.failUnlessEqual(status, 0, output)


    def testOverrideDefaults(self):
        """ groupadd: Test if the defaults can be overriden with the -K option """
	# this is known to not work on older RHELs - test what we are running
	rhv = RedHatVersion()
	runs = rhv.get_info()
	if rhv.is_rhel():
	    if runs[1] < 5:
		print "This test makes sense for RHEL5+"
		return 
	else:
	    if runs[1] < 6:
		print "This test makes sense for Fedora 6+"
		return 

		
        GID_MIN = 600
        GID_MAX = 625

        (status, output) = commands.getstatusoutput("groupadd -K GID_MIN=%d -K GID_MAX=%d %s" %
                           (GID_MIN, GID_MAX, self.groupname))
        self.failUnlessEqual(status, 0, output)

        created = GroupInfo()
        created.get_info_name(self.groupname)
        self.assertEqual(GID_MIN <= created["gr_gid"] <= GID_MAX, True, "FAIL: created an user with UID of %d" % (created["gr_gid"]))


    def testFOption(self):
        """ groupadd: Tests the -f option of groupadd """
        (status, output) = commands.getstatusoutput("groupadd %s" % (self.groupname))
        self.failUnlessEqual(status, 0, output)

        (status, output) = commands.getstatusoutput("groupadd -f %s" % (self.groupname))
        self.assertEqual(status, 0, output)

class TestGroupaddInvalidName(unittest.TestCase, ShadowUtilsTestBase):
    def testGroupaddInvalidName(self):
        """ groupadd: Test adding of a group with an invalid name """
        (status, output) = commands.getstatusoutput("groupadd foo?")
        self.assertNotEqual(status, 0, output)
        (status, output) = commands.getstatusoutput("groupadd aaaaabbbbbcccccdddddeeeeefffffggg") #33 chars
        self.assertNotEqual(status, 0, output)

class TestGroupaddValidName(unittest.TestCase, ShadowUtilsTestBase):
    def testGroupaddValidName(self):
        """ groupadd: Test adding and removing of groups with maximal valid name and name ending with $ """
        (status, output) = commands.getstatusoutput("groupadd aaaaabbbbbcccccdddddeeeeefffffgg") #32 chars
        self.assertEqual(status, 0, output)
        (status, output) = commands.getstatusoutput("groupadd aaaaabbbbbcccccdddddeeeeefffffg\$") #32 chars
        self.assertEqual(status, 0, output)
        (status, output) = commands.getstatusoutput("groupdel aaaaabbbbbcccccdddddeeeeefffffgg") #32 chars
        self.assertEqual(status, 0, output)
        (status, output) = commands.getstatusoutput("groupdel aaaaabbbbbcccccdddddeeeeefffffg\$") #32 chars
        self.assertEqual(status, 0, output)


class TestGroupmod(unittest.TestCase, ShadowUtilsTestBase):
    def setUp(self):
        self.groupname = "test-shadow-utils-groups"
        (status, output) = commands.getstatusoutput("groupadd %s" % (self.groupname))
        self.failUnlessEqual(status, 0, output)

    def tearDown(self):
        commands.getstatusoutput("groupdel %s" % (self.groupname))

    def testChangeGID(self):
        """ groupmod: Test changing a gid of a group """
        expected = GroupInfo()
        expected["gr_name"] = self.groupname
        expected["gr_gid"]  = 54321

        (status, output) = commands.getstatusoutput("groupmod -g%d %s" % (expected["gr_gid"], self.groupname))
        self.failUnlessEqual(status, 0, output)

        created = GroupInfo()
        created.get_info_name(self.groupname)
        self.assertEqual(created.lazy_compare(expected), True, "FAIL: Could not change GID of an existing group")

    def testChangeGIDToExistingValue(self):
        """ groupmod: Test changing GID to an existing value """
        second_name = "%s-2" % (self.groupname)

        created = GroupInfo()
        created.get_info_name(self.groupname)

        expected = GroupInfo()
        expected["gr_name"] = self.groupname
        expected["gr_gid"]  = created["gr_gid"]

        (status, output) = commands.getstatusoutput("groupadd %s" % (second_name))
        self.failUnlessEqual(status, 0, output)

        # try to assingn GID of the first group to the second - this should fail without the -o option
        (status, output) = commands.getstatusoutput("groupmod -g%d %s" % (created["gr_gid"], second_name))
        self.failIfEqual(status, 0, output)

        # should pass with the -o option
        (status, output) = commands.getstatusoutput("groupmod -g%d -o %s" % (created["gr_gid"], second_name))
        self.failUnlessEqual(status, 0, output)

        self.assertEqual(created.lazy_compare(expected), True, "FAIL: Could not change GID of an existing group to an existing one")

        # clean up
        commands.getstatusoutput("groupdel %s" % (second_name))
        self.failUnlessEqual(status, 0, output)

    def testChangeGroupName(self):
        """ groupmod: Test changing a group's name """
        second_name = "%s-2" % (self.groupname)

        created = GroupInfo()
        created.get_info_name(self.groupname)

        (status, output) = commands.getstatusoutput("groupmod -n%s %s" % (second_name, self.groupname))
        self.failUnlessEqual(status, 0, output)

        changed = GroupInfo()
        changed.get_info_gid(created["gr_gid"])
        self.assertEqual(changed["gr_name"], second_name)
        self.assertEqual(changed["gr_gid"], created["gr_gid"])

        # change back, so the group could be deleted by tearDown
        (status, output) = commands.getstatusoutput("groupmod -n%s %s" % (self.groupname, second_name))
        self.failUnlessEqual(status, 0, output)

    def testChangeGroupNameExisting(self):
        """ groupmod: Test changing a group's name to an existing one """
        existing = "bin"
        (status, output) = commands.getstatusoutput("groupmod -n%s %s" % (existing, self.groupname))
        self.assertNotEqual(status, 0, output) # man groupmod -> 9: group name already in use 

    def testChangeNonExistingGroup(self):
        """ groupmod: Test properties of a non-existing group """
        nonexistent = "foobar"
        (status, output) = commands.getstatusoutput("groupmod -nspameggs %s" % (nonexistent))
        self.assertNotEqual(status, 0, status) # man groupmod -> 6: specified group doesn't exist

class TestGroupdel(unittest.TestCase, ShadowUtilsTestBase):
    def testCorrectGroupdel(self):
        """ groupdel: Basic usage of groupdel """
        self.groupname = "test-shadow-utils-groups"
        (status, output) = commands.getstatusoutput("groupadd %s" % (self.groupname))
        self.failUnlessEqual(status, 0, output)
        (status, output) = commands.getstatusoutput("groupdel %s" % (self.groupname))
        self.assertEqual(status, 0, output)

    def testGroupdelNoSuchGroup(self):
        """ groupdel: Remove non-existing group """
        (status, output) = commands.getstatusoutput("groupdel foobar")
        self.assertNotEqual(status, 0, output)

    def testRemovePrimaryGroup(self):
        """ groupdel: Remove a primary group of an user """
        username = "test-groupdel-primary"
        (status, output) = commands.getstatusoutput("useradd %s" % (username))
        self.failUnlessEqual(status, 0, output)

        (status, output) = commands.getstatusoutput("groupdel %s" % (username))
        self.assertNotEqual(status, 0, output)

        # clean up
        (status, output) = commands.getstatusoutput("userdel -r %s" % (username))
        self.failUnlessEqual(status, 0, output)

class TestPwckGrpck(unittest.TestCase):
    def setUp(self):
        self.passwd_path = tempfile.mktemp(suffix="test-pwck-passwd")
        self.passwd_file = open(self.passwd_path, "w")
        self.group_path = tempfile.mktemp(suffix="test-pwck-grp")
        self.group_file = open(self.group_path, "w")
        self.gshadow_path = tempfile.mktemp(suffix="test-pwck-gshadow")
        self.gshadow_file = open(self.gshadow_path, "w")

    def tearDown(self):
        self.passwd_file.close()
        self.group_file.close()
        self.gshadow_file.close()

        os.remove(self.passwd_path)
        os.remove(self.group_path)
        os.remove(self.gshadow_path)

    def runPwckCheck(self, passwd, group):
        self.passwd_file.truncate()
        self.group_file.truncate()

        self.passwd_file.write(passwd)
        self.passwd_file.flush()
        self.group_file.write(group)
        self.group_file.flush()

        command = "pwck -r %s %s" % (self.passwd_path, self.group_path)
        return commands.getstatusoutput(command)

    def runGrpCheck(self, group, gshadow):
        self.group_file.truncate()
        self.gshadow_file.truncate()

        self.gshadow_file.write(gshadow)
        self.gshadow_file.flush()

        self.group_file.write(group)
        self.group_file.flush()

        command = "grpck -r %s %s" % (self.group_path, self.gshadow_path)
        return commands.getstatusoutput(command)


    def testValidEntries(self):
        """ pwck: a valid entry """
        status, output = self.runPwckCheck("foo:x:685:0::/dev/null:/bin/bash", "")
	rhv = RedHatVersion()
	runs = rhv.get_info()
	if rhv.is_rhel():
	    if runs[1] < 6:
		self.assertEqual(status, 0, output)
	    else:
		self.assertNotEqual(status, 0, output)

    def testNumberOfFields(self):
        """ pwck: invalid number of fields in the record """
        not_enough = "foo:x:685:685::/dev/null"
        too_many   = "foo:x:685:685::/dev/null:/bin/bash:comment"
        status, output = self.runPwckCheck(not_enough, "")
        self.assertNotEqual(status, 0, output)

        status, output = self.runPwckCheck(too_many, "")
        self.assertNotEqual(status, 0, output)

    def testUniqueUserName(self):
        """ pwck: unique user name in the record """
        duplicate_username = "foo:x:685:685::/dev/null:/bin/bash\nfoo:x:686:686::/dev/null:/bin/bash"
        status, output = self.runPwckCheck(duplicate_username, "")
        self.assertNotEqual(status, 0, output)

    def testValidID(self):
        """ pwck: invalid UID in the records """
        invalid_ids = [ "foo:x:-1:685::/dev/null:/bin/bash", "foo:x:blah:685::/dev/null:/bin/bash", "foo:x:1234567890:685::/dev/null:/bin/bash" ]
        for record in invalid_ids:
            status, output = self.runPwckCheck(record, "")
            self.assertNotEqual(status, 0, record)


    def testValidPrimaryGroup(self):
        """ pwck: invalid primary group """
        invalid_groups = [ "foo:x:685:-1::/dev/null:/bin/bash", "foo:x:685:blah::/dev/null:/bin/bash", "foo:x:685:1234567890::/dev/null:/bin/bash" ]
        for record in invalid_groups:
            status, output = self.runPwckCheck("", record)
            self.assertNotEqual(status, 0, output)

    def testValidHomeDir(self):
        """ pwck: invalid home dir """
        for record in [ "foo:x:685:685::123:/bin/bash", "foo:x:685:685::/path/to/nowhere:/bin/bash", "foo:x:685:1234567890::!:/bin/bash" ]:
            status, output = self.runPwckCheck(record, "")
            self.assertNotEqual(status, 0, output)

    def testBZ164954(self):
        """ grpck: regression test for BZ164954 """
        record = "root:x:0:root\nbin:x:1:root,bin,daemon\ndaemon:x:2:root,bin,daemon\nsys:x:3:root,bin,adm\nadm:x:4:root,adm,daemon"
        status, output = self.runGrpCheck("", record)
        self.assertNotEqual(status, 0, output)

if __name__ == "__main__":
    broken_on_rhel4 = { "TestUseradd" : [ "testCustomUID", "testCustomGID" ] }

    if os.getuid() != 0:
        print "This test must be run as root"
        sys.exit(1)

    unittest.main()

