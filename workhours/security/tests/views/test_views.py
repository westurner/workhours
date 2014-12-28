from __future__ import print_function
import unittest
from pyramid import testing

from workhours import configure_test_app
from workhours.models.sql import _initialize_sql_test

from workhours import testing
from workhours.models.fixtures import data

import transaction

class SecurityViewTests(testing.PyramidFixtureTestCase):
    TEST_USERNAME = u'testfixture_username'
    fixtures = (data.UserData, )

    def test_registration_nosubmit(self):
        from workhours.security.views import user_add
        configure_test_app(self.config)
        request = self._new_request()
        result = user_add(request)
        self.assertTrue('form' in result)

    def test_registration_submit_empty(self):
        from workhours.security.views import user_add
        configure_test_app(self.config)
        request = self._new_request()
        result = user_add(request)
        self.assertTrue('form' in result)
        _post = {
            'loginform.submitted': 'Register',
            '_csrf': request.session.get_csrf_token(),
        }
        request = self._new_request(post=_post)
        result = user_add(request)
        self.assertEqual(
            result['form'].form.errors,
            {
                'username': u'Required',
                #'confirm_passphrase': u'Required',
                'passphrase': u'Required',
                'email': u'Required',
                'name': u'Required',
            }
        )

    def test_registration_submit_schema_succeed(self):
        from workhours.models import User
        from workhours.security.views import user_add
        configure_test_app(self.config)
        request = self._new_request()

        test_user = {
            'username': u'username3',
            'passphrase': u'secret',
            'email': u'username@example.com',
            'name': u'John Doe',
        }

        _post = {
            'loginform.submitted': u'Register',
            'username': test_user['username'],
            'passphrase': test_user['passphrase'],
            #'confirm_passphrase': test_user['passphrase'],
            'email': test_user['email'],
            'name': test_user['name'],
            '_csrf': request.session.get_csrf_token()
        }
        request = self._new_request(post=_post)
        resp = user_add(request)

        transaction.commit()

        self.assertNotIn('Failed to add user',
                request.session.peek_flash())

        try:
            user = (
                self.session.query(User)
                    .filter(User.username == test_user['username']).one())
            self.assertTrue(user)

            self.assertEqual(user.username, test_user['username'])
            self.assertEqual(user.name, test_user['name'])
            self.assertEqual(user.email, test_user['email'])
        except Exception, e:
            print(e) # TODO FIXME
            self.assertFalse(e)
            #import ipdb
            #ipdb.set_trace()
            #raise





    def test_user_view(self):
        from workhours.security.views import user_view
        self.config.testing_securitypolicy(self.TEST_USERNAME)
        configure_test_app(self.config)
        request = self._new_request()
        request.matchdict = {'username': self.TEST_USERNAME}
        result = user_view(request)
        self.assertEqual(result['user'].username, self.TEST_USERNAME)
        self.assertTrue(result['user'].id)

    def test_login_view_submit_fail(self):
        from workhours.security.views import login_view
        configure_test_app(self.config)
        request = self._new_request()
        request.POST = {
            'loginform.submitted': u'Login',
            'username': self.TEST_USERNAME,
            'passphrase': u'wrongpassphrase',
            '_csrf': request.session.get_csrf_token()
        }
        login_view(request)
        messages = request.session.peek_flash()
        self.assertIn(u'Failed to login.', messages)

    def test_login_view_submit_success(self):
        from workhours.security.views import login_view
        configure_test_app(self.config)
        request = self._new_request()
        _post = {
            'loginform.submitted': u'Login',
            'username': data.UserData.one.username,
            'passphrase': data.UserData.one.passphrase,
            '_csrf': request.session.get_csrf_token()
        }
        request = self._new_request(post=_post)
        resp = login_view(request)
        messages = request.session.peek_flash()
        self.assertIn(u'Logged in successfully.', messages)

    def test_logout_view(self):
        from workhours.security.views import logout_view
        configure_test_app(self.config)
        request = self._new_request()
        logout_view(request)
        messages = request.session.peek_flash()
        self.assertIn(u'Logged out.', messages)
