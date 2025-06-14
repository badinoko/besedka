from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from gallery.models import Photo, PhotoComment

User = get_user_model()

class Command(BaseCommand):
    help = 'Добавляет тестовые лайки и комментарии к фотографиям'

    def handle(self, *args, **options):
        # Получаем всех пользователей
        users = User.objects.all()
        photos = Photo.objects.all()

        if not users or not photos:
            self.stdout.write(self.style.ERROR('Нет пользователей или фотографий для тестирования'))
            return

        created_likes = 0
        created_comments = 0

        # Добавляем лайки к каждой фотографии от разных пользователей
        for photo in photos:
            for i, user in enumerate(users[:3]):  # Максимум 3 лайка на фото
                if user not in photo.likes.all():
                    photo.likes.add(user)
                    created_likes += 1

        # Добавляем комментарии
        test_comments = [
            "Отличное фото! 🌟",
            "Красивые растения!",
            "Какой сорт?",
            "Впечатляющий результат!",
            "Отличная работа! 👍"
        ]

        for i, photo in enumerate(photos[:5]):  # Комментарии к первым 5 фото
            for j, user in enumerate(users[:2]):  # По 2 комментария от разных пользователей
                if not PhotoComment.objects.filter(photo=photo, author=user).exists():
                    PhotoComment.objects.create(
                        photo=photo,
                        author=user,
                        text=test_comments[(i + j) % len(test_comments)]
                    )
                    created_comments += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Успешно добавлено {created_likes} лайков и {created_comments} комментариев'
            )
        )
