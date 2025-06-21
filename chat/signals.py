from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from .models import Message, DiscussionRoom
from users.models import Notification


@receiver(post_save, sender=Message)
def update_messages_dump(sender, instance, created, **kwargs):
    """Обновить дамп сообщений при создании/изменении сообщения"""
    if instance.room.is_discussion and hasattr(instance.room, 'discussion_room'):
        discussion_room = instance.room.discussion_room
        discussion_room.set_messages_dump()


@receiver(post_delete, sender=Message)
def update_messages_dump_on_delete(sender, instance, **kwargs):
    """Обновить дамп сообщений при удалении сообщения"""
    if instance.room.is_discussion and hasattr(instance.room, 'discussion_room'):
        discussion_room = instance.room.discussion_room
        discussion_room.set_messages_dump()


@receiver(post_save, sender=Message)
def create_chat_notification(sender, instance, created, **kwargs):
    """Создать уведомление о новом сообщении в чате"""
    if not created:
        return

    # Определяем получателей уведомления
    recipients = []

    if instance.room.is_private and hasattr(instance.room, 'room_thread'):
        # Приватный чат - уведомляем собеседника
        thread = instance.room.room_thread
        partner = thread.get_partner(instance.author)
        if partner:
            recipients.append(partner)

    elif instance.room.is_discussion and hasattr(instance.room, 'discussion_room'):
        # Групповое обсуждение - уведомляем всех участников кроме автора
        discussion = instance.room.discussion_room
        recipients = discussion.members.exclude(id=instance.author.id)

    # Создаем уведомления
    for recipient in recipients:
        # Проверяем, что комната не отключена для уведомлений
        if not instance.room.muted:
            Notification.objects.create(
                recipient=recipient,
                sender=instance.author,
                title=str(_('Новое сообщение в чате')),
                message=_('%(author)s написал: %(content)s') % {
                    'author': instance.author.get_full_name() or instance.author.username,
                    'content': instance.content[:100] + '...' if len(instance.content) > 100 else instance.content
                },
                content_object=instance.room,
                notification_type='chat_message'
            )


@receiver(post_save, sender=DiscussionRoom)
def add_owner_to_members(sender, instance, created, **kwargs):
    """Автоматически добавить владельца в участники обсуждения"""
    if created:
        instance.members.add(instance.owner)
