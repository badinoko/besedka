"""Module for all Form Tests."""

from django.utils.translation import gettext_lazy as _
import pytest
from django.contrib.auth import get_user_model

# from magicbeans.users.forms import UserAdminCreationForm # Проверить, нужен ли этот импорт и откуда он на самом деле
# from magicbeans.users.models import User # <-- Закомментировано или удалить
from users.models import User # <--- Новый импорт
from users.forms import UserAdminCreationForm # <--- Предполагаемый правильный импорт формы


class TestUserAdminCreationForm:
    """
    Test class for all tests related to the UserAdminCreationForm
    """

    def test_username_validation_error_msg(self, user: User):
        """
        Tests UserAdminCreation Form's unique validator functions correctly by testing:
            1) A new user with an existing username cannot be added.
            2) Only 1 error is raised by the UserCreation Form
            3) The desired error message is raised
        """

        # The user already exists,
        # hence cannot be created.
        form = UserAdminCreationForm(
            {
                "username": user.username,
                "password1": user.password,
                "password2": user.password,
            },
        )

        assert not form.is_valid()
        assert len(form.errors) == 1
        assert "username" in form.errors
        assert form.errors["username"][0] == _("This username has already been taken.")
