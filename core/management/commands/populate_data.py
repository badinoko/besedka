import os
import random
import tempfile
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.core.files import File
from django.utils.text import slugify
from django.utils import timezone
from faker import Faker
from PIL import Image, ImageDraw, ImageFont

from news.models import Post, Category
from gallery.models import Photo
from growlogs.models import GrowLog
from users.models import Like, Notification
from django.contrib.contenttypes.models import ContentType

User = get_user_model()
fake = Faker('ru_RU')

# =======================================================================
# Настройки генерации
# =======================================================================
NUM_POSTS = 5
NUM_PHOTOS = 15
NUM_GROWLOGS = 4
MAX_LIKES_PER_ITEM = 5
MAX_COMMENTS_PER_ITEM = 3
# =======================================================================

class Command(BaseCommand):
    help = 'Populates the database with test data for news, gallery, growlogs, and creates notifications.'

    def handle(self, *args, **kwargs):
        self.stdout.write("Начинаем наполнение базы данных тестовыми данными...")

        users = list(User.objects.filter(is_superuser=False, is_staff=False))
        main_user = User.objects.filter(username='Buddy').first()
        if not users:
            self.stdout.write(self.style.ERROR("Нет обычных пользователей для создания контента. Пожалуйста, создайте их."))
            return
        if not main_user:
            self.stdout.write(self.style.ERROR("Основной пользователь 'Buddy' не найден. Уведомления не будут созданы."))
            return

        self.create_posts(users, main_user)
        self.create_photos(users, main_user)
        self.create_growlogs(users, main_user)

        self.stdout.write(self.style.SUCCESS("==============================================="))
        self.stdout.write(self.style.SUCCESS("✓ Наполнение базы данных успешно завершено!"))
        self.stdout.write(self.style.SUCCESS("==============================================="))

    def _create_placeholder_image(self, text, width=800, height=600):
        """Создает временное изображение с текстом."""
        img = Image.new('RGB', (width, height), color = (random.randint(50, 200), random.randint(50, 200), random.randint(50, 200)))
        d = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("arial.ttf", 40)
        except IOError:
            font = ImageFont.load_default()
        d.text((10,10), text, fill=(255,255,255), font=font)

        temp_dir = tempfile.gettempdir()
        temp_img_path = os.path.join(temp_dir, f'{text.replace(" ", "_").replace(".", "")}.jpg')
        img.save(temp_img_path)
        return temp_img_path

    def _add_likes_and_comments(self, item, users, main_user):
        """Добавляет лайки и комментарии к объекту (пост, фото, гроулог)."""
        content_type = ContentType.objects.get_for_model(item)
        item_author = getattr(item, 'author', getattr(item, 'grower', None))
        if not item_author:
             return # Не можем добавить лайки если нет автора

        likers = random.sample(users, min(len(users), random.randint(1, MAX_LIKES_PER_ITEM)))
        for user in likers:
            Like.objects.get_or_create(user=user, content_type=content_type, object_id=item.id)
            if item_author != user:
                Notification.create_notification(
                    recipient=item_author,
                    sender=user,
                    notification_type=Notification.NotificationType.LIKE,
                    title=f'Ваш контент "{item.title[:30]}..." понравился!',
                    message=f'Пользователю {user.username} понравился ваш пост/фото.',
                    content_object=item
                )

    def create_posts(self, users, main_user):
        self.stdout.write("--- Создание новостей ---")
        if not Category.objects.exists():
            Category.objects.create(name='Общие новости', slug='general')
            self.stdout.write("  > Создана категория по умолчанию 'Общие новости'")
        default_category = Category.objects.first()

        for i in range(NUM_POSTS):
            author = random.choice(users)
            title = fake.sentence(nb_words=6)
            slug = slugify(title) + '-' + str(random.randint(1000, 9999))
            post = Post.objects.create(
                author=author,
                title=title,
                slug=slug,
                content='\n\n'.join(fake.paragraphs(nb=5)),
                status='published',
                category=default_category
            )
            self.stdout.write(f"  > Создан пост: '{post.title}'")
            self._add_likes_and_comments(post, users, main_user)

    def create_photos(self, users, main_user):
        self.stdout.write("--- Создание фотографий в галерее ---")
        for i in range(NUM_PHOTOS):
            author = random.choice(users)
            title = fake.sentence(nb_words=4)
            placeholder_path = self._create_placeholder_image(f"Photo {i+1}")

            with open(placeholder_path, 'rb') as f:
                photo = Photo.objects.create(
                    author=author,
                    title=title,
                    description=fake.paragraph(nb_sentences=3),
                    image=File(f, name=os.path.basename(placeholder_path)),
                )
            self.stdout.write(f"  > Создано фото: '{photo.title}'")
            self._add_likes_and_comments(photo, users, main_user)
            os.remove(placeholder_path)

    def create_growlogs(self, users, main_user):
        self.stdout.write("--- Создание гроу-репортов ---")
        for i in range(NUM_GROWLOGS):
            author = random.choice(users)
            growlog = GrowLog.objects.create(
                grower=author,
                title=f"Гроу-репорт: {fake.word().capitalize()} {fake.word().capitalize()}",
                strain_custom=fake.word().capitalize(),
                setup_description='\n\n'.join(fake.paragraphs(nb=4)),
                start_date=timezone.now().date() - timezone.timedelta(days=random.randint(5, 40)),
                is_public=True
            )
            self.stdout.write(f"  > Создан гроу-репорт: '{growlog.title}'")
            self._add_likes_and_comments(growlog, users, main_user)
