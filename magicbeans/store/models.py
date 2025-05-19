from django.db import models


class Administrator(models.Model):
    """Модель для администраторов магазина."""
    name = models.CharField(max_length=255, verbose_name="Имя")
    telegram_id = models.CharField(
        max_length=100, unique=True, verbose_name="Telegram ID",
    )
    is_active = models.BooleanField(default=True, verbose_name="Активный")
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Дата создания",
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name="Дата обновления",
    )

    class Meta:
        verbose_name = "Администратор"
        verbose_name_plural = "Администраторы"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.telegram_id})"


class Producer(models.Model):
    name = models.CharField(max_length=255, verbose_name="Название")
    logo = models.ImageField(
        upload_to="producers/", blank=True, null=True, verbose_name="Логотип",
    )
    hidden = models.BooleanField(default=False, verbose_name="Скрыт")

    def __str__(self):
        return self.name


class Type(models.Model):
    name = models.CharField(max_length=100, verbose_name="Тип сорта")

    def __str__(self):
        return self.name


class ProductPhoto(models.Model):
    image = models.ImageField(upload_to="products/", verbose_name="Фото")

    def __str__(self):
        return self.image.url


class Product(models.Model):
    name = models.CharField(max_length=255, verbose_name="Название")
    photos = models.ManyToManyField(
        ProductPhoto, blank=True, verbose_name="Фотографии",
    )
    description = models.TextField(blank=True, verbose_name="Описание")
    characteristics = models.TextField(blank=True, verbose_name="Характеристики")
    hidden = models.BooleanField(default=False, verbose_name="Скрыт")
    producer = models.ForeignKey(
        Producer,
        on_delete=models.CASCADE,
        related_name="products",
        verbose_name="Сидбанк",
    )
    type = models.ForeignKey(
        Type,
        on_delete=models.SET_NULL,
        null=True,
        related_name="products",
        verbose_name="Тип сорта",
    )

    def __str__(self):
        return self.name


class ProductPackage(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="packages",
        verbose_name="Сорт",
    )
    seeds_count = models.CharField(
        max_length=20, verbose_name="Количество семян (фасовка)",
    )
    price = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Цена за пачку",
    )
    stock = models.PositiveIntegerField(verbose_name="Количество на складе")

    def __str__(self):
        return f"{self.product.name} - {self.seeds_count}"


class Order(models.Model):
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Дата/время создания",
    )
    admin_telegram_id = models.CharField(
        max_length=64, verbose_name="ID админа Telegram",
    )
    user_telegram_id = models.CharField(
        max_length=64, verbose_name="ID пользователя Telegram",
    )
    total = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Общая сумма заказа",
    )

    def __str__(self):
        return f"Order #{self.id} ({self.created_at})"


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="Заказ",
    )
    product = models.ForeignKey(
        Product, on_delete=models.SET_NULL, null=True, verbose_name="Сорт",
    )
    product_package = models.ForeignKey(
        ProductPackage, on_delete=models.SET_NULL, null=True, verbose_name="Фасовка",
    )
    product_name_snapshot = models.CharField(
        max_length=255, verbose_name="Название сорта (снимок)",
    )
    seeds_count_snapshot = models.CharField(
        max_length=20, verbose_name="Фасовка (снимок)",
    )
    quantity = models.PositiveIntegerField(verbose_name="Количество упаковок")
    price_snapshot = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Цена за упаковку (снимок)",
    )

    def __str__(self):
        return (
            f"{self.product_name_snapshot} "
            f"({self.seeds_count_snapshot}) x{self.quantity}"
        )
