# from magicbeans.users.models import User # <-- Закомментировано или удалить
from users.models import User # <--- Новый импорт
import pytest


def test_user_get_absolute_url(user: User):
    assert user.get_absolute_url() == f"/users/{user.username}/"
