from types import SimpleNamespace

from django.test import SimpleTestCase

from inmuebles.api.permissions import HasApiKey


class HasApiKeyTests(SimpleTestCase):
    def setUp(self):
        self.permission = HasApiKey()

    def test_allowed_when_authenticated_by_api_key(self):
        request = SimpleNamespace(successful_authenticator=object())
        self.assertTrue(self.permission.has_permission(request, None))

    def test_denied_without_authenticator(self):
        request = SimpleNamespace(successful_authenticator=None)
        self.assertFalse(self.permission.has_permission(request, None))
