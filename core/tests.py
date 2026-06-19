from django.test import TestCase

from .models import User


class UserSecurityTests(TestCase):
    def test_new_user_password_is_hashed(self):
        user = User.objects.create(username='admin', password='secret123', permission=0)

        self.assertNotEqual(user.password, 'secret123')
        self.assertTrue(user.password.startswith('pbkdf2_'))

    def test_legacy_plaintext_password_is_migrated_on_login(self):
        user = User.objects.create(username='legacy', password='temp123', permission=0)
        User.objects.filter(id=user.id).update(password='temp123')

        response = self.client.post('/login/', {
            'username': 'legacy',
            'password': 'temp123',
        })

        user.refresh_from_db()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/')
        self.assertNotEqual(user.password, 'temp123')
        self.assertTrue(user.password.startswith('pbkdf2_'))
        self.assertEqual(self.client.session.get('user_id'), user.id)

    def test_delete_user_requires_post(self):
        admin = User.objects.create(username='admin', password='secret123', permission=0)
        victim = User.objects.create(username='victim', password='secret123', permission=1)

        session = self.client.session
        session['user_id'] = admin.id
        session.save()

        response = self.client.get(f'/users/{victim.id}/delete/')

        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(id=victim.id).exists())

    def test_delete_user_via_post_succeeds(self):
        admin = User.objects.create(username='admin', password='secret123', permission=0)
        victim = User.objects.create(username='victim', password='secret123', permission=1)

        session = self.client.session
        session['user_id'] = admin.id
        session.save()

        response = self.client.post(f'/users/{victim.id}/delete/')

        self.assertEqual(response.status_code, 302)
        self.assertFalse(User.objects.filter(id=victim.id).exists())
