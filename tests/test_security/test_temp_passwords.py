"""
Тесты системы временных паролей
"""
import pytest
from datetime import timedelta
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.contrib import messages
from django.utils import timezone

from users.utils import TemporaryPasswordManager
from users.models import UserProfile

User = get_user_model()


class TemporaryPasswordSystemTest(TestCase):
    """Тесты системы временных паролей"""

    def setUp(self):
        """Настройка тестов"""
        self.client = Client()

        # Создаем владельца платформы
        self.owner = User.objects.create_user(
            username='platform_owner',
            email='owner@besedka.com',
            role='owner',
            is_staff=True
        )

        # Создаем обычного пользователя
        self.user = User.objects.create_user(
            username='test_user',
            email='user@test.com',
            role='user'
        )

    def test_temp_password_generation(self):
        """Тест генерации временного пароля"""
        # Генерируем временный пароль
        temp_creds = TemporaryPasswordManager.create_temp_credentials(
            self.user,
            role='store_owner',
            valid_hours=24
        )

        # Проверяем результат
        self.assertIn('username', temp_creds)
        self.assertIn('password', temp_creds)
        self.assertIn('expires_at', temp_creds)

        # Проверяем, что пароль сгенерирован
        self.assertTrue(len(temp_creds['password']) >= 12)

        # Проверяем, что у пользователя создался профиль
        self.user.refresh_from_db()
        self.assertTrue(hasattr(self.user, 'profile_extra'))
        self.assertTrue(self.user.profile_extra.temp_password)
        self.assertIsNotNone(self.user.profile_extra.password_expires_at)

    def test_temp_password_login(self):
        """Тест входа с временным паролем"""
        # Создаем временный пароль
        temp_creds = TemporaryPasswordManager.create_temp_credentials(self.user)

        # Пытаемся войти с временным паролем
        login_successful = self.client.login(
            username=temp_creds['username'],
            password=temp_creds['password']
        )

        self.assertTrue(login_successful)

    def test_temp_password_expiration(self):
        """Тест истечения временного пароля"""
        # Создаем профиль пользователя
        profile, created = UserProfile.objects.get_or_create(user=self.user)

        # Устанавливаем истекший временный пароль
        profile.temp_password = True
        profile.password_expires_at = timezone.now() - timedelta(hours=1)
        profile.save()

        # Проверяем, что пароль истек
        self.assertTrue(profile.is_temp_password_expired())

    def test_temp_password_clearing(self):
        """Тест очистки временного пароля"""
        # Создаем временный пароль
        TemporaryPasswordManager.create_temp_credentials(self.user)

        # Очищаем временный пароль
        self.user.profile_extra.clear_temp_password()

        # Проверяем, что флаг сброшен
        self.user.profile_extra.refresh_from_db()
        self.assertFalse(self.user.profile_extra.temp_password)
        self.assertIsNone(self.user.profile_extra.password_expires_at)

    def test_owner_can_create_temp_credentials(self):
        """Тест: владелец может создавать временные учетные данные"""
        # Устанавливаем пароль для владельца
        self.owner.set_password('testpass123')
        self.owner.save()

        # Входим как владелец платформы
        login_successful = self.client.login(username='platform_owner', password='testpass123')
        self.assertTrue(login_successful)

        # Создаем нового пользователя через форму
        response = self.client.post(reverse('users:store_owner_management'), {
            'action': 'create_new',
            'username': 'new_store_owner',
            'email': 'newowner@test.com'
        })

        # Проверяем, что пользователь создан
        new_user = User.objects.filter(username='new_store_owner').first()
        self.assertIsNotNone(new_user)
        if new_user:
            self.assertEqual(new_user.role, 'store_owner')
            self.assertTrue(new_user.is_staff)

    def test_auto_profile_creation(self):
        """Тест автоматического создания профиля"""
        # У пользователя нет профиля
        self.assertFalse(hasattr(self.user, 'profile_extra'))

        # Создаем временный пароль
        TemporaryPasswordManager.create_temp_credentials(self.user)

        # Проверяем, что профиль создался автоматически
        self.user.refresh_from_db()
        self.assertTrue(hasattr(self.user, 'profile_extra'))

    def test_temp_password_strength(self):
        """Тест сложности временного пароля"""
        temp_password = TemporaryPasswordManager.generate_temp_password()

        # Проверяем длину
        self.assertGreaterEqual(len(temp_password), 12)

        # Проверяем наличие разных типов символов
        has_upper = any(c.isupper() for c in temp_password)
        has_lower = any(c.islower() for c in temp_password)
        has_digit = any(c.isdigit() for c in temp_password)
        has_special = any(c in "!@#$%^&*" for c in temp_password)

        self.assertTrue(has_upper)
        self.assertTrue(has_lower)
        self.assertTrue(has_digit)
        self.assertTrue(has_special)


@pytest.mark.django_db
class TemporaryPasswordMiddlewareTest(TestCase):
    """Тесты middleware для временных паролей"""

    def setUp(self):
        """Настройка тестов"""
        self.client = Client()

        # Создаем пользователя с временным паролем
        self.user = User.objects.create_user(
            username='temp_user',
            email='temp@test.com',
            role='store_owner',
            is_staff=True
        )

        # Создаем профиль с временным паролем
        profile, created = UserProfile.objects.get_or_create(user=self.user)
        profile.set_temp_password(24)

    def test_temp_password_redirect(self):
        """Тест перенаправления на смену пароля"""
        # Входим как пользователь с временным паролем
        self.client.force_login(self.user)

        # Пытаемся зайти на любую страницу
        response = self.client.get('/store_admin/')

        # Должны быть перенаправлены на смену пароля
        self.assertEqual(response.status_code, 302)
        # Проверяем, что в URL есть change_password
        redirect_url = response.get('Location', '')
        self.assertIn('password', redirect_url)

    def test_expired_temp_password_logout(self):
        """Тест выхода при истекшем временном пароле"""
        # Устанавливаем истекший временный пароль
        profile = self.user.profile_extra
        profile.password_expires_at = timezone.now() - timedelta(hours=1)
        profile.save()

        # Входим и пытаемся зайти на страницу
        self.client.force_login(self.user)
        response = self.client.get('/store_admin/')

        # Должны быть разлогинены
        self.assertEqual(response.status_code, 302)
        redirect_url = response.get('Location', '')
        self.assertIn('login', redirect_url)

    def test_normal_user_no_redirect(self):
        """Тест: обычные пользователи не перенаправляются"""
        # Создаем обычного пользователя
        normal_user = User.objects.create_user(
            username='normal_user',
            email='normal@test.com',
            role='user'
        )

        # Входим и проверяем доступ
        self.client.force_login(normal_user)
        response = self.client.get('/users/cabinet/')

        # Не должно быть перенаправления
        self.assertEqual(response.status_code, 200)
