import os
import random
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.contrib.auth import get_user_model
from PIL import Image, ImageDraw, ImageFont
import io
from gallery.models import Photo, PhotoComment
from growlogs.models import GrowLog, GrowLogComment
from users.models import Notification

User = get_user_model()


class Command(BaseCommand):
    help = 'Создание тестовых данных для галереи и гроурепортов'

    def add_arguments(self, parser):
        parser.add_argument(
            '--photos',
            type=int,
            default=15,
            help='Количество фотографий для создания (по умолчанию 15)'
        )
        parser.add_argument(
            '--growlogs',
            type=int,
            default=5,
            help='Количество гроурепортов для создания (по умолчанию 5)'
        )

    def handle(self, *args, **options):
        self.stdout.write('🚀 Создание тестовых данных для галереи и гроурепортов...')

        # Список растений для генерации
        plant_names = [
            'White Widow', 'Northern Lights', 'Blue Dream', 'AK-47',
            'Purple Haze', 'Jack Herer', 'Sour Diesel', 'OG Kush',
            'Super Skunk', 'Amnesia Haze', 'Cheese', 'Critical',
            'Gorilla Glue', 'Girl Scout Cookies', 'Strawberry Cough'
        ]

        # Цвета для генерации фейковых изображений
        plant_colors = [
            '#2ECC71', '#27AE60', '#16A085', '#1ABC9C',
            '#3498DB', '#2980B9', '#9B59B6', '#8E44AD',
            '#F39C12', '#E67E22', '#E74C3C', '#C0392B'
        ]

        # Получаем существующих пользователей
        users = list(User.objects.filter(is_active=True))
        if not users:
            self.stdout.write(self.style.ERROR('❌ Нет активных пользователей для создания тестовых данных'))
            return

        # Создаем фотографии в галерее
        photos_created = 0
        for i in range(options['photos']):
            try:
                # Случайный автор
                author = random.choice(users)

                # Случайное растение
                plant_name = random.choice(plant_names)

                # Генерируем фейковое изображение
                image = self.create_test_image(plant_name, random.choice(plant_colors))

                # Создаем фото
                photo = Photo.objects.create(
                    title=f'{plant_name} - День {random.randint(1, 120)}',
                    description=self.generate_description(plant_name),
                    author=author,
                    is_public=True
                )

                # Сохраняем изображение
                img_file = ContentFile(image.getvalue())
                photo.image.save(f'test_photo_{i+1}.png', img_file, save=True)

                # Добавляем случайные лайки
                like_users = random.sample(users, k=random.randint(0, min(5, len(users))))
                for like_user in like_users:
                    if like_user != author:  # Автор не лайкает себя
                        photo.likes.add(like_user)

                # Добавляем случайные комментарии
                comment_users = random.sample(users, k=random.randint(0, 3))
                for comment_user in comment_users:
                    if comment_user != author:
                        PhotoComment.objects.create(
                            photo=photo,
                            author=comment_user,
                            content=self.generate_comment()
                        )

                photos_created += 1
                self.stdout.write(f'📸 Создано фото {photos_created}: {photo.title}')

            except Exception as e:
                self.stdout.write(self.style.WARNING(f'⚠️ Ошибка создания фото {i+1}: {e}'))

        # Создаем гроурепорты
        growlogs_created = 0
        for i in range(options['growlogs']):
            try:
                # Случайный автор
                grower = random.choice(users)

                # Случайное растение
                plant_name = random.choice(plant_names)

                # Создаем гроурепорт
                growlog = GrowLog.objects.create(
                    title=f'Выращивание {plant_name} #{i+1}',
                    description=self.generate_growlog_description(plant_name),
                    grower=grower,
                    environment=random.choice(['indoor', 'outdoor', 'greenhouse']),
                    medium=random.choice(['soil', 'hydro', 'coco', 'aero']),
                    current_stage=random.choice(['seed', 'germination', 'seedling', 'vegetative', 'flowering', 'harvest']),
                    is_public=True,
                    strain_custom=plant_name
                )

                # Добавляем случайные лайки
                like_users = random.sample(users, k=random.randint(0, min(7, len(users))))
                for like_user in like_users:
                    if like_user != grower:
                        growlog.likes.add(like_user)

                # Добавляем случайные комментарии
                comment_users = random.sample(users, k=random.randint(0, 4))
                for comment_user in comment_users:
                    if comment_user != grower:
                        GrowLogComment.objects.create(
                            growlog=growlog,
                            author=comment_user,
                            content=self.generate_growlog_comment()
                        )

                growlogs_created += 1
                self.stdout.write(f'🌱 Создан гроурепорт {growlogs_created}: {growlog.title}')

            except Exception as e:
                self.stdout.write(self.style.WARNING(f'⚠️ Ошибка создания гроурепорта {i+1}: {e}'))

        # Создаем уведомления естественным образом (через лайки и комментарии)
        self.stdout.write('🔔 Генерируем уведомления...')
        notifications_created = 0

        # Создаем уведомления о новых лайках
        for photo in Photo.objects.filter(title__startswith='White Widow'):
            for like_user in photo.likes.all()[:2]:  # Берем первых 2 лайкеров
                if like_user != photo.author:
                    Notification.objects.create(
                        recipient=photo.author,
                        sender=like_user,
                        title='Новый лайк в галерее!',
                        message=f'{like_user.username} лайкнул вашу фотографию "{photo.title}"',
                        notification_type='like',
                        content_object=photo
                    )
                    notifications_created += 1

        # Создаем уведомления о новых комментариях
        for growlog in GrowLog.objects.filter(title__contains='Blue Dream'):
            for comment in growlog.comments.all()[:1]:  # Берем первый комментарий
                if comment.author != growlog.grower:
                    Notification.objects.create(
                        recipient=growlog.grower,
                        sender=comment.author,
                        title='Новый комментарий к гроурепорту!',
                        message=f'{comment.author.username} прокомментировал ваш гроурепорт "{growlog.title}"',
                        notification_type='comment',
                        content_object=growlog
                    )
                    notifications_created += 1

        self.stdout.write(self.style.SUCCESS(f'✅ ГОТОВО!'))
        self.stdout.write(self.style.SUCCESS(f'📸 Создано фотографий: {photos_created}'))
        self.stdout.write(self.style.SUCCESS(f'🌱 Создано гроурепортов: {growlogs_created}'))
        self.stdout.write(self.style.SUCCESS(f'🔔 Создано уведомлений: {notifications_created}'))

    def create_test_image(self, plant_name, color):
        """Создает тестовое изображение растения"""
        # Создаем изображение 400x400
        img = Image.new('RGB', (400, 400), color=color)
        draw = ImageDraw.Draw(img)

        # Рисуем простую имитацию растения
        # Стебель
        draw.rectangle([190, 200, 210, 380], fill='#8B4513')

        # Листья
        for i in range(3):
            y = 150 + i * 60
            # Левый лист
            draw.ellipse([120, y, 190, y + 40], fill='#228B22')
            # Правый лист
            draw.ellipse([210, y, 280, y + 40], fill='#228B22')

        # Добавляем текст
        try:
            # Пытаемся использовать системный шрифт
            font = ImageFont.load_default()
        except:
            font = None

        # Название растения
        text_bbox = draw.textbbox((0, 0), plant_name, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        draw.text((200 - text_width // 2, 50), plant_name, fill='white', font=font)

        # Сохраняем в BytesIO
        img_io = io.BytesIO()
        img.save(img_io, format='PNG')
        img_io.seek(0)
        return img_io

    def generate_description(self, plant_name):
        """Генерирует описание для фотографии"""
        descriptions = [
            f'Мой {plant_name} на {random.randint(20, 80)} день цветения. Очень доволен результатом!',
            f'Красивые шишки {plant_name}. Запах просто невероятный!',
            f'{plant_name} день {random.randint(1, 120)}. Растет как на дрожжах!',
            f'Первый опыт выращивания {plant_name}. Пока все идет отлично.',
            f'Харвест {plant_name} близко! Жду не дождусь попробовать.',
            f'Мой любимый сорт - {plant_name}. Всегда радует качеством.',
        ]
        return random.choice(descriptions)

    def generate_growlog_description(self, plant_name):
        """Генерирует описание для гроурепорта"""
        descriptions = [
            f'Документирую полный цикл выращивания {plant_name}. Это мой первый опыт с этим сортом.',
            f'Эксперимент с {plant_name} в гидропонике. Делюсь опытом и наблюдениями.',
            f'Органическое выращивание {plant_name} в почве. Записываю все этапы развития.',
            f'Второй гров {plant_name}. В прошлый раз результат был отличный, повторяю.',
            f'Сравниваю разные методы на {plant_name}. Интересно увидеть разницу.',
        ]
        return random.choice(descriptions)

    def generate_comment(self):
        """Генерирует случайный комментарий для фото"""
        comments = [
            'Отличная работа! 👍',
            'Красивые шишки! Какой запах?',
            'Вау! Очень впечатляет!',
            'Сколько дней цветения?',
            'Какие удобрения используешь?',
            'Шикарный результат! 🔥',
            'Какая урожайность ожидается?',
            'Первый раз вижу такую красоту!',
            'Поделись секретом успеха!',
            'Фото просто огонь! 📸',
        ]
        return random.choice(comments)

    def generate_growlog_comment(self):
        """Генерирует случайный комментарий для гроурепорта"""
        comments = [
            'Интересный подход! Буду следить за развитием.',
            'Какой свет используешь?',
            'Отличный старт! Удачи в выращивании!',
            'Очень познавательно! Спасибо за детали.',
            'Подписался на обновления! 👀',
            'Какая температура в боксе?',
            'Сколько растений планируешь?',
            'Крутая установка! Сам такую хочу.',
            'Какой сидбанк у семян?',
            'Жду продолжения! Очень интересно!',
        ]
        return random.choice(comments)
