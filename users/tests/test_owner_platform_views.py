from django.test import TestCase, Client
from django.urls import reverse, reverse_lazy
from django.contrib.auth import get_user_model
from users.models import UserProfile
from users.utils import TemporaryPasswordManager
from unittest.mock import patch
import string

User = get_user_model()

class ManageStoreOwnerViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        # Создаем Владельца Платформы
        self.platform_owner = User.objects.create_user(
            username="platform_owner",
            password="password123",
            role=User.Role.OWNER,
            is_staff=True, # Для доступа к админке
            is_superuser=True # Для простоты, чтобы имел все права в тестах
        )
        # Создаем обычного пользователя, которого будем делать Владельцем Магазина
        self.potential_store_owner_user = User.objects.create_user(
            username="potential_owner",
            email="potential@example.com",
            password="password123",
            role=User.Role.USER
        )
        # URL для тестируемого view
        self.manage_url = reverse_lazy("owner_admin:manage_store_owner")

    def test_view_requires_login(self):
        response = self.client.get(self.manage_url)
        # Ожидаем редирект на страницу логина (allauth)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse('account_login')))

    def test_view_accessible_by_platform_owner(self):
        self.client.login(username="platform_owner", password="password123")
        response = self.client.get(self.manage_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "owner_admin/manage_store_owner.html")

    def test_view_assign_new_store_owner(self):
        self.client.login(username="platform_owner", password="password123")
        new_owner_username = "new_store_owner_test"
        new_owner_email = "new_store_owner@example.com"

        initial_store_owner_count = User.objects.filter(role=User.Role.STORE_OWNER, is_active=True).count()

        with patch('users.utils.TemporaryPasswordManager.generate_random_password') as mock_generate_password:
            mock_generate_password.return_value = "supersecret_temp_password1!"
            response = self.client.post(self.manage_url, {
                "username": new_owner_username,
                "email": new_owner_email,
                "first_name": "New",
                "last_name": "Owner",
                "assign_owner_submit": "Назначить Владельца" # Важно, чтобы имя кнопки совпадало
            })

        self.assertEqual(response.status_code, 200) # Должен быть рендер той же страницы с сообщением
        self.assertContains(response, "Новый владелец магазина")
        self.assertContains(response, new_owner_username)
        self.assertContains(response, "supersecret_temp_password1!")

        # Проверяем, что пользователь создан и его роль изменена
        newly_assigned_owner = User.objects.get(username=new_owner_username)
        self.assertEqual(newly_assigned_owner.role, User.Role.STORE_OWNER)
        self.assertTrue(newly_assigned_owner.is_staff)

        # Проверяем, что создан UserProfile с временным паролем
        user_profile = UserProfile.objects.get(user=newly_assigned_owner)
        self.assertTrue(user_profile.temp_password)
        self.assertIsNotNone(user_profile.password_expires_at)

        # Проверяем, что теперь только один активный владелец магазина
        final_store_owner_count = User.objects.filter(role=User.Role.STORE_OWNER, is_active=True).count()
        self.assertEqual(final_store_owner_count, 1)
        self.assertEqual(User.objects.get(role=User.Role.STORE_OWNER, is_active=True).username, new_owner_username)

    def test_view_deactivate_store_owner(self):
        self.client.login(username="platform_owner", password="password123")
        # Сначала назначим владельца, чтобы было кого деактивировать
        current_owner = User.objects.create_user(
            username="current_store_owner_to_deactivate",
            email="deactivate@example.com",
            role=User.Role.STORE_OWNER,
            is_staff=True,
            is_active=True
        )
        UserProfile.objects.create(user=current_owner)

        self.assertTrue(User.objects.get(username=current_owner.username).is_active)

        response = self.client.post(self.manage_url, {
            "confirm_deactivation": "on", # CheckboxInput отправляет 'on' если отмечен
            "deactivate_owner_submit": "Отозвать Владельца Магазина"
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "был успешно деактивирован")
        self.assertFalse(User.objects.get(username=current_owner.username).is_active)

        # Проверяем, что UserProfile обновлен (temp_password сброшен)
        user_profile = UserProfile.objects.get(user=current_owner)
        self.assertFalse(user_profile.temp_password)
        self.assertIsNone(user_profile.password_expires_at)

    def test_one_store_owner_logic_on_assign(self):
        self.client.login(username="platform_owner", password="password123")
        # Создаем первого владельца магазина
        owner1 = User.objects.create_user("owner1", "owner1@example.com", "pass", role=User.Role.STORE_OWNER, is_active=True, is_staff=True)
        UserProfile.objects.create(user=owner1)

        # Назначаем второго владельца через форму
        self.client.post(self.manage_url, {
            "username": "owner2", "email": "owner2@example.com",
            "assign_owner_submit": "Назначить Владельца"
        })

        # Проверяем, что первый владелец деактивирован
        owner1.refresh_from_db()
        self.assertFalse(owner1.is_active)

        # Проверяем, что второй владелец активен
        owner2 = User.objects.get(username="owner2")
        self.assertTrue(owner2.is_active)
        self.assertEqual(owner2.role, User.Role.STORE_OWNER)
        self.assertEqual(User.objects.filter(role=User.Role.STORE_OWNER, is_active=True).count(), 1)

class TemporaryPasswordManagerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser_temp_pass", email="temp@example.com", password="oldpassword")

    @patch('users.utils.TemporaryPasswordManager.generate_random_password')
    def test_create_temporary_password_for_user(self, mock_generate_password):
        mock_generate_password.return_value = "new_secure_temp_password1!"

        details = TemporaryPasswordManager.create_temporary_password_for_user(self.user)

        self.user.refresh_from_db()
        user_profile = UserProfile.objects.get(user=self.user)

        self.assertTrue(self.user.check_password("new_secure_temp_password1!"))
        self.assertTrue(user_profile.temp_password)
        self.assertIsNotNone(user_profile.password_expires_at)
        self.assertEqual(details["password"], "new_secure_temp_password1!")
        self.assertEqual(details["username"], self.user.username)

    def test_generate_random_password_properties(self):
        password = TemporaryPasswordManager.generate_random_password()
        self.assertEqual(len(password), TemporaryPasswordManager.DEFAULT_PASSWORD_LENGTH)
        self.assertTrue(any(char.isdigit() for char in password))
        # В моей реализации TemporaryPasswordManager используется string.punctuation
        self.assertTrue(any(char in string.punctuation for char in password))
