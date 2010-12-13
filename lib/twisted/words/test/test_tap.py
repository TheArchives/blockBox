# Copyright (c) 2001-2005 Twisted Matrix Laboratories.
# See LICENSE for details.

from lib.twisted.cred import credentials, error
from lib.twisted.words import tap
from lib.twisted.trial import unittest



class WordsTap(unittest.TestCase):
    """
    Ensures that the twisted.words.tap API works.
    """

    PASSWD_TEXT = "admin:admin\njoe:foo\n"
    admin = credentials.UsernamePassword('admin', 'admin')
    joeWrong = credentials.UsernamePassword('joe', 'bar')


    def setUp(self):
        """
        Create a file with two users.
        """
        self.filename = self.mktemp()
        self.file = open(self.filename, 'w')
        self.file.write(self.PASSWD_TEXT)
        self.file.flush()


    def tearDown(self):
        """
        Close the dummy user database.
        """
        self.file.close()


    def test_hostname(self):
        """
        Tests that the --hostname parameter gets passed to Options.
        """
        opt = tap.Options()
        opt.parseOptions(['--hostname', 'myhost'])
        self.assertEquals(opt['hostname'], 'myhost')


    def test_passwd(self):
        """
        Tests the --passwd command for backwards-compatibility.
        """
        opt = tap.Options()
        opt.parseOptions(['--passwd', self.file.name])
        self._loginTest(opt)


    def test_auth(self):
        """
        Tests that the --auth command generates a checker.
        """
        opt = tap.Options()
        opt.parseOptions(['--auth', 'file:'+self.file.name])
        self._loginTest(opt)


    def _loginTest(self, opt):
        """
        This method executes both positive and negative authentication
        tests against whatever credentials checker has been stored in
        the Options class.

        @param opt: An instance of L{tap.Options}.
        """
        self.assertEquals(len(opt['credCheckers']), 1)
        checker = opt['credCheckers'][0]
        self.assertFailure(checker.requestAvatarId(self.joeWrong),
                           error.UnauthorizedLogin)
        def _gotAvatar(username):
            self.assertEquals(username, self.admin.username)
        return checker.requestAvatarId(self.admin).addCallback(_gotAvatar)
