import unittest
from pyramid import testing

from workhours import _register_routes
from workhours import _register_common_templates
from workhours.models.sql import _initialize_sql_test

from workhours import testing
from workhours.models.fixtures import data

import transaction

class SecurityViewTests(testing.PyramidFixtureTestCase):
    TEST_USERNAME = u'testfixture_username'
    fixtures = (data.UserData, )

    def _addUser(self, username):
        from workhours.models import User
        user = User(
                username=username,
                passphrase=u'passphrase',
                name=u'name',
                email=u'email')
        self.session.add(user)
        self.session.flush()
        return user

    def test_registration_nosubmit(self):
        from workhours.security.views import user_add
        _register_routes(self.config)
        _register_common_templates(self.config)
        request = self._new_request()
        result = user_add(request)
        self.assertTrue('form' in result)

    def test_registration_submit_empty(self):
        from workhours.security.views import user_add
        _register_routes(self.config)
        _register_common_templates(self.config)
        request = self._new_request()
        result = user_add(request)
        self.assertTrue('form' in result)
        request = self._new_request()
        request.POST = {
            'loginform.submitted': 'Shoot',
            '_csrf': request.session.get_csrf_token(),
        }
        result = user_add(request)
        self.assertEqual(
            result['form'].form.errors,
            {
                'username': u'Missing value',
                'confirm_passphrase': u'Missing value',
                'passphrase': u'Missing value',
                'email': u'Missing value',
                'name': u'Missing value',
            }
        )

    def test_registration_submit_schema_succeed(self):
        from workhours.models import User
        from workhours.security.views import user_add
        _register_routes(self.config)
        _register_common_templates(self.config)
        request = self._new_request()
        request.POST = {
            'loginform.submitted': u'Register',
            'username': 'username3',
            'passphrase': u'secret',
            'confirm_passphrase': u'secret',
            'email': u'username@example.com',
            'name': u'John Doe',
            '_csrf': request.session.get_csrf_token()
        }
        resp = user_add(request)
        raise Exception()

        user = (
            self.session.query(User)
                .filter(User.username == 'username3').one())

        #self.assertTrue(len(users), 1)
        #user = users[0]
        self.assertEqual(user.username, 'username3')
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
        self.config.testing_securitypolicy(self.TEST_USERNAME)
        _register_routes(self.config)
        _register_common_templates(self.config)
        request = self._new_request()
        request.matchdict = {'username': self.TEST_USERNAME}
        result = user_view(request)
        self.assertEqual(result['user'].username, self.TEST_USERNAME)
        self.assertTrue(result['user']._id)



    def test_login_view_submit_fail(self):
        from workhours.security.views import login_view
        _register_routes(self.config)
        request = self._new_request()
        request.POST = {
            'loginform.submitted': u'Login',
            'username': self.TEST_USERNAME,
            'passphrase': u'wrongpassphrase',
            '_csrf': request.session.get_csrf_token()
        }
        login_view(request)
        messages = request.session.peek_flash()
        self.assertEqual(messages, [u'Failed to login.'])


    def test_login_view_submit_success(self):
        from workhours.security.views import login_view
        _register_routes(self.config)
        request = self._new_request()
        request.POST = {
            'loginform.submitted': u'Login',
            'username': self.TEST_USERNAME,
            'passphrase': data.UserData.one.passphrase,
            '_csrf': request.session.get_csrf_token()
        }
        login_view(request)
        messages = request.session.peek_flash()
        self.assertEqual(messages, [u'Logged in successfully.'])

    def test_logout_view(self):
        from workhours.security.views import logout_view
        _register_routes(self.config)
        request = self._new_request()
        logout_view(request)
        messages = request.session.peek_flash()
        self.assertEqual(messages, [u'Logged out.'])
