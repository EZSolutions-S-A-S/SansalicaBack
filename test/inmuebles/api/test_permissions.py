from types import SimpleNamespace

from django.contrib.auth.models import AnonymousUser
from django.test import SimpleTestCase

from inmuebles.api.permissions import ReadOnlyOrAdmin


class ReadOnlyOrAdminTests(SimpleTestCase):
    def setUp(self):
        self.permission = ReadOnlyOrAdmin()

    def _request(self, method, successful_authenticator=None, user=None):
        return SimpleNamespace(method=method, successful_authenticator=successful_authenticator, user=user)

    def test_safe_method_allowed_when_authenticated_by_api_key(self):
        request = self._request('GET', successful_authenticator=object())
        self.assertTrue(self.permission.has_permission(request, None))

    def test_safe_method_denied_without_authenticator(self):
        request = self._request('GET', successful_authenticator=None)
        self.assertFalse(self.permission.has_permission(request, None))

    def test_write_method_denied_for_anonymous(self):
        request = self._request('POST', user=AnonymousUser())
        self.assertFalse(self.permission.has_permission(request, None))

    def test_write_method_denied_for_non_staff_user(self):
        user = SimpleNamespace(is_authenticated=True, is_staff=False)
        request = self._request('DELETE', user=user)
        self.assertFalse(self.permission.has_permission(request, None))

    def test_write_method_allowed_for_staff_user(self):
        user = SimpleNamespace(is_authenticated=True, is_staff=True)
        request = self._request('PATCH', user=user)
        self.assertTrue(self.permission.has_permission(request, None))
