from django.test import RequestFactory, SimpleTestCase, override_settings

from inmuebles.api.authentication import ReadOnlyApiKeyAuthentication


@override_settings(READ_API_KEY='secret-test-key')
class ReadOnlyApiKeyAuthenticationTests(SimpleTestCase):
    def setUp(self):
        self.auth = ReadOnlyApiKeyAuthentication()
        self.factory = RequestFactory()

    def test_no_header_returns_none(self):
        request = self.factory.get('/api/inmuebles/')
        self.assertIsNone(self.auth.authenticate(request))

    def test_wrong_keyword_returns_none(self):
        request = self.factory.get('/api/inmuebles/', HTTP_AUTHORIZATION='Bearer secret-test-key')
        self.assertIsNone(self.auth.authenticate(request))

    def test_wrong_token_returns_none(self):
        request = self.factory.get('/api/inmuebles/', HTTP_AUTHORIZATION='Api-Key wrong-token')
        self.assertIsNone(self.auth.authenticate(request))

    def test_correct_token_authenticates_with_no_user(self):
        request = self.factory.get('/api/inmuebles/', HTTP_AUTHORIZATION='Api-Key secret-test-key')
        result = self.auth.authenticate(request)
        self.assertIsNotNone(result)
        user, auth = result
        self.assertIsNone(user)
        self.assertEqual(auth, 'secret-test-key')

    @override_settings(READ_API_KEY='')
    def test_empty_configured_key_never_authenticates(self):
        request = self.factory.get('/api/inmuebles/', HTTP_AUTHORIZATION='Api-Key anything')
        self.assertIsNone(self.auth.authenticate(request))
