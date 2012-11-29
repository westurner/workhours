import unittest
from pyramid import testing

from workhours import _register_routes
from workhours import _register_common_templates
from workhours.models.sql import _initialize_sql_test

class SecurityViewTests(unittest.TestCase):
    def setUp(self):
        self.meta = _initialize_sql_test()
        self.session = self.meta.Session
        self.config = testing.setUp()

    def tearDown(self):
        import transaction
        transaction.abort()
        testing.tearDown()

    def _addUser(self, username=u'username'):
        from workhours.models import User
        user = User(username=username, passphrase=u'passphrase', name=u'name',
                    email=u'email')
        self.session.add(user)
        self.session.flush()
        return user

    def test_registration_nosubmit(self):
        from workhours.security.views import user_add
        _register_routes(self.config)
        _register_common_templates(self.config)
        request = testing.DummyRequest()
        result = user_add(request)
        self.assertTrue('form' in result)

    def test_registration_submit_empty(self):
        from workhours.security.views import user_add
        _register_routes(self.config)
        _register_common_templates(self.config)
        request = testing.DummyRequest()
        result = user_add(request)
        self.assertTrue('form' in result)
        request = testing.DummyRequest(post={'form.submitted': 'Shoot'})
        result = user_add(request)
        self.assertEqual(
            result['form'].form.errors,
            {
                'username': u'Missing value',
                'confirm_passphrase': u'Missing value',
                'passphrase': u'Missing value',
                'email': u'Missing value',
                'name': u'Missing value'
            }
        )

    def test_registration_submit_schema_succeed(self):
        from workhours.security.views import user_add
        from workhours.security.models import User
        _register_routes(self.config)
        _register_common_templates(self.config)
        request = testing.DummyRequest(
            post={
                'form.submitted': u'Register',
                'username': u'username',
                'passphrase': u'secret',
                'confirm_passphrase': u'secret',
                'email': u'username@example.com',
                'name': u'John Doe',
            }
        )
        user_add(request)
        users = self.session.query(User).all()
        self.assertEqual(len(users), 1)
        user = users[0]
        self.assertEqual(user.username, u'username')
        self.assertEqual(user.name, u'John Doe')
        self.assertEqual(user.email, u'username@example.com')
        #self.assertEqual(user.hits, 0)
        #self.assertEqual(user.misses, 0)
        #self.assertEqual(user.delivered_hits, 0)
        #self.assertEqual(user.delivered_misses, 0)
        #self.assertEqual(user.ideas, [])
        #self.assertEqual(user.voted_ideas, [])


    def test_user_view(self):
        from workhours.security.views import user_view
        self.config.testing_securitypolicy(u'username')
        _register_routes(self.config)
        _register_common_templates(self.config)
        request = testing.DummyRequest()
        request.matchdict = {'username': u'username'}
        self._addUser()
        result = user_view(request)
        self.assertEqual(result['user'].username, u'username')
        self.assertEqual(result['user'].user_id, 1)



    def test_login_view_submit_fail(self):
        from workhours.security.views import login_view
        _register_routes(self.config)
        self._addUser()
        request = testing.DummyRequest()
        request.POST = {
            'form.submitted': u'Login',
            'username': u'username',
            'passphrase': u'wrongpassphrase',
            '_csrf': request.session.get_csrf_token()
        }
        login_view(request)
        messages = request.session.peek_flash()
        self.assertEqual(messages, [u'Failed to login.'])


    def test_login_view_submit_success(self):
        from workhours.security.views import login_view
        _register_routes(self.config)
        self._addUser()
        request = testing.DummyRequest(
            post={
                'form.submitted': u'Login',
                'username': u'username',
                'passphrase': u'passphrase',
            }
        )
        login_view(request)
        messages = request.session.peek_flash()
        self.assertEqual(messages, [u'Logged in successfully.'])

    def test_logout_view(self):
        from workhours.security.views import logout_view
        _register_routes(self.config)
        request = testing.DummyRequest()
        logout_view(request)
        messages = request.session.peek_flash()
        self.assertEqual(messages, [u'Logged out.'])
