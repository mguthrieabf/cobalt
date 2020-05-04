from django.test import TestCase
from django.urls import reverse
from accounts.models import User

class UserTestCase(TestCase):
    def setUp(self):
        User.objects.create(email="a@fake.com", system_number=100)

    def test_user_created(self):
        user1 = User.objects.get(email="a@fake.com")
        self.assertEqual(user1.system_number,100)

class UserViewCase(TestCase):
    def test_public_profile(self):
        self.client.force_login(User.objects.get_or_create(system_number=100)[0])
        # response = self.client.get(reverse('accounts:public_profile', kwargs={'pk':0}))
        response = self.client.get(reverse('dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "100")
