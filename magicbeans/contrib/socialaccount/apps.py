from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class SocialAccountConfig(AppConfig):
    name = "allauth.socialaccount"
    verbose_name = _("Social Accounts")
    default = True

    def ready(self):
        # Скрываем приложение из админ-панели
        from django.contrib.admin.apps import AdminConfig
        try:
            # Скрываем все модели этого приложения из админки
            from allauth.socialaccount import models
            for model_name in dir(models):
                model = getattr(models, model_name)
                if hasattr(model, "_meta"):
                    model._meta.app_config.verbose_name = ""
        except:
            pass
        self.verbose_name = ""
