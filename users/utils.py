import secrets
import string
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model
from core.models import ActionLog
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

class TemporaryPasswordManager:
    """Унифицированный менеджер для работы с временными паролями"""
    DEFAULT_PASSWORD_LENGTH = 12
    DEFAULT_VALID_HOURS = 24

    @staticmethod
    def generate_temp_password(length=12):
        """
        Генерирует безопасный временный пароль, гарантируя наличие всех типов символов.
        Это основной метод генерации паролей.
        """
        if length < 4:  # Минимальная длина для всех типов символов
            raise ValueError("Password length must be at least 4 to include all character types.")

        # Обязательные символы
        password_chars = [
            secrets.choice(string.ascii_uppercase),
            secrets.choice(string.ascii_lowercase),
            secrets.choice(string.digits),
            secrets.choice("!@#$%^&*"),
        ]

        # Дополнительные символы
        remaining_length = length - len(password_chars)
        all_chars = string.ascii_letters + string.digits + "!@#$%^&*"
        for _ in range(remaining_length):
            password_chars.append(secrets.choice(all_chars))

        # Перемешиваем для случайности
        secrets.SystemRandom().shuffle(password_chars)
        return ''.join(password_chars)

    @staticmethod
    def create_temporary_password_for_user(user, valid_hours=DEFAULT_VALID_HOURS):
        """
        Создает временный пароль для пользователя, используя методы UserProfile.
        Возвращает детали (пароль, срок действия).
        """
        from .models import UserProfile

        # Генерируем временный пароль
        temp_password_str = TemporaryPasswordManager.generate_temp_password()

        # Устанавливаем пароль пользователю
        user.set_password(temp_password_str)
        user.save(update_fields=['password'])

        # Создаем или получаем профиль пользователя
        profile, created = UserProfile.objects.get_or_create(user=user)

        # Используем метод модели для установки временного пароля
        profile.set_temp_password(valid_hours=valid_hours)

        # Логирование (если доступен контекст пользователя)
        current_user = getattr(user, '_change_user', None)
        if current_user and current_user.is_authenticated:
            try:
                ActionLog.objects.create(
                    user=current_user,
                    action_type=ActionLog.ACTION_EDIT,
                    model_name=User.__name__,
                    object_id=user.pk,
                    object_repr=str(user),
                    details=f'Создан временный пароль. Действителен {valid_hours} часов.'
                )
            except Exception as e:
                logger.error(f"Ошибка при логировании создания временного пароля: {e}")

        return {
            "username": user.username,
            "password": temp_password_str,
            "expires_at": profile.password_expires_at
        }

    @staticmethod
    def create_temp_credentials(user, role='store_owner', valid_hours=24):
        """
        Создает временные учетные данные (совместимость с существующим кодом).
        Использует унифицированный метод create_temporary_password_for_user.
        """
        # Используем основной метод
        result = TemporaryPasswordManager.create_temporary_password_for_user(user, valid_hours)

        return result

    @staticmethod
    def clear_temp_password(user):
        """
        Очищает временный пароль пользователя, используя методы UserProfile.
        """
        try:
            from .models import UserProfile
            profile, created = UserProfile.objects.get_or_create(user=user)
            if profile.temp_password:
                profile.clear_temp_password()
                logger.info(f"Очищен временный пароль для пользователя: {user.username}")
                return True
            return False
        except Exception as e:
            logger.error(f"Ошибка при очистке временного пароля для {user.username}: {e}")
            return False

    @staticmethod
    def is_temp_password_expired(user):
        """
        Проверяет, истек ли временный пароль пользователя.
        """
        try:
            from .models import UserProfile
            profile = getattr(user, 'profile_extra', None)
            if profile:
                return profile.is_temp_password_expired()
            return False
        except Exception as e:
            logger.error(f"Ошибка при проверке истечения пароля для {user.username}: {e}")
            return False

    # Устаревшие методы для совместимости (будут удалены в будущем)
    @staticmethod
    def generate_random_password(length=DEFAULT_PASSWORD_LENGTH):
        """
        УСТАРЕЛ: Используйте generate_temp_password().
        Оставлен для совместимости с существующим кодом.
        """
        logger.warning("generate_random_password устарел, используйте generate_temp_password")
        return TemporaryPasswordManager.generate_temp_password(length)
