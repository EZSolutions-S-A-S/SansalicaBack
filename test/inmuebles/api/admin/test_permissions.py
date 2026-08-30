from types import SimpleNamespace

from django.contrib.auth.models import AnonymousUser
from django.test import SimpleTestCase

from inmuebles.api.admin.permissions import IsStaffUser


class IsStaffUserTests(SimpleTestCase):
    def setUp(self):
        self.permission = IsStaffUser()

    def test_denied_for_anonymous(self):
        request = SimpleNamespace(user=AnonymousUser())
        self.assertFalse(self.permission.has_permission(request, None))

    def test_denied_for_authenticated_non_staff(self):
        user = SimpleNamespace(is_authenticated=True, is_staff=False)
        request = SimpleNamespace(user=user)
        self.assertFalse(self.permission.has_permission(request, None))

    def test_allowed_for_staff(self):
        user = SimpleNamespace(is_authenticated=True, is_staff=True)
        request = SimpleNamespace(user=user)
        self.assertTrue(self.permission.has_permission(request, None))
