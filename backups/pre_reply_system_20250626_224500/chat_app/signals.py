from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Message

# Этот файл пока можно оставить пустым,
# если у нас нет сигналов для новых моделей.
# В будущем мы сможем добавить сюда логику,
# например, для отправки уведомлений при новых сообщениях.