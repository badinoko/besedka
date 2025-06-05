from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.db import transaction
from allauth.account.signals import password_changed
from core.models import ActionLog
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

@receiver(pre_save, sender=User)
def enforce_single_store_owner(sender, instance, **kwargs):
    """
    Сигнал для обеспечения логики "Один Владелец Магазина".
    При назначении/активации роли STORE_OWNER текущему пользователю,
    автоматически деактивирует других активных владельцев магазина,
    понижает их роль до USER и сбрасывает is_staff.
    Также деактивирует связанных с ними администраторов магазина.
    """
    if instance.role == User.Role.STORE_OWNER and instance.is_active:
        # Используем транзакцию для атомарности операции
        with transaction.atomic():
            # Деактивируем всех других активных владельцев магазина
            other_store_owners = User.objects.filter(
                role=User.Role.STORE_OWNER,
                is_active=True
            ).exclude(pk=instance.pk if instance.pk else None) # Исключаем текущий экземпляр, если он уже сохранен

            for owner in other_store_owners:
                owner.role = User.Role.USER      # Понижаем роль
                owner.is_staff = False           # Сбрасываем is_staff
                owner.is_active = False          # Деактивируем

                # Сохраняем изменения для бывшего владельца
                # Указываем _change_user, если доступно, для ActionLogMiddleware, или текущего instance.user, если это админка
                change_user = getattr(instance, '_change_user', None) or getattr(instance, 'user', None)
                if change_user: # Если нет информации о том, кто делает изменение, это может быть системный процесс
                     owner._change_user = change_user

                owner.save(update_fields=['role', 'is_staff', 'is_active'])
                logger.info(f"Автоматически деактивирован и понижен в роли предыдущий владелец магазина: {owner.username}")

                # Очищаем временный пароль у деактивированного владельца
                from .models import UserProfile # Импорт здесь, чтобы избежать циклических зависимостей
                UserProfile.objects.filter(user=owner).update(
                    temp_password=False,
                    password_expires_at=None
                )

                # Деактивируем связанных администраторов магазина с этим бывшим владельцем
                # Логика привязки админов магазина к конкретному владельцу магазина не ясна из текущей модели.
                # Предположим, что все store_admin деактивируются, если нет другого активного store_owner.
                # Это соответствует текущей логике сигнала, но может быть неидеально.
                # Пункт 2.1.1.3 (Судьба Администраторов Магазина) будет это рассматривать подробнее.
                # Пока оставляем текущую логику деактивации ВСЕХ store_admin, если меняется STORE_OWNER.
                store_admins = User.objects.filter(role=User.Role.STORE_ADMIN, is_active=True)
                for admin in store_admins:
                    admin.is_active = False
                    admin.role = User.Role.USER
                    admin.is_staff = False
                    if change_user:
                        admin._change_user = change_user
                    admin.save(update_fields=['is_active', 'role', 'is_staff'])
                    logger.info(f"Автоматически деактивирован и понижен в роли администратор магазина: {admin.username} из-за смены владельца магазина.")

@receiver(password_changed)
def clear_temp_password_on_change(sender, request, user, **kwargs):
    """
    Сигнал для сброса флага временного пароля при смене пароля пользователем.
    """
    try:
        from .models import UserProfile
        profile, created = UserProfile.objects.get_or_create(user=user)
        if profile.temp_password:
            profile.clear_temp_password()
            logger.info(f"Сброшен флаг временного пароля для пользователя: {user.username}")
    except Exception as e:
        logger.error(f"Ошибка при сбросе временного пароля для {user.username}: {e}")

@receiver(post_save, sender=User)
def log_store_owner_changes(sender, instance, created, **kwargs):
    """
    Логирование изменений владельца магазина.
    """
    if instance.role == User.Role.STORE_OWNER:
        try:
            # Получаем текущего пользователя из контекста (если доступен)
            current_user = getattr(instance, '_change_user', None)
            if current_user and current_user.is_authenticated:
                action_type = ActionLog.ACTION_ADD if created else ActionLog.ACTION_EDIT
                details = f"Назначен владельцем магазина" if created else f"Обновлен владелец магазина"

                ActionLog.objects.create(
                    user=current_user,
                    action_type=action_type,
                    model_name=User.__name__,
                    object_id=instance.pk,
                    object_repr=str(instance),
                    details=details
                )
        except Exception as e:
            logger.error(f"Ошибка при логировании изменений владельца магазина: {e}")

# Тут будет логика сигнала
