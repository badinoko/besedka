# Generated by Django 4.2.21 on 2025-05-24 22:43

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("growlogs", "0003_auto_20250525_0139"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="growlogentry",
            name="description",
        ),
        migrations.AddField(
            model_name="growlog",
            name="container_size",
            field=models.CharField(
                blank=True, max_length=100, verbose_name="Container Size"
            ),
        ),
        migrations.AddField(
            model_name="growlog",
            name="current_stage",
            field=models.CharField(
                choices=[
                    ("germination", "Germination"),
                    ("seedling", "Seedling"),
                    ("vegetative", "Vegetative"),
                    ("flowering", "Flowering"),
                    ("harvest", "Harvest"),
                    ("curing", "Curing"),
                    ("completed", "Completed"),
                ],
                default="germination",
                max_length=20,
                verbose_name="Current Stage",
            ),
        ),
        migrations.AddField(
            model_name="growlog",
            name="environment",
            field=models.CharField(
                choices=[
                    ("indoor", "Indoor"),
                    ("outdoor", "Outdoor"),
                    ("greenhouse", "Greenhouse"),
                ],
                default="indoor",
                max_length=20,
                verbose_name="Environment",
            ),
        ),
        migrations.AddField(
            model_name="growlog",
            name="goals",
            field=models.TextField(blank=True, verbose_name="Goals"),
        ),
        migrations.AddField(
            model_name="growlog",
            name="lighting",
            field=models.CharField(blank=True, max_length=255, verbose_name="Lighting"),
        ),
        migrations.AddField(
            model_name="growlog",
            name="likes",
            field=models.ManyToManyField(
                blank=True, related_name="liked_growlogs", to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.AddField(
            model_name="growlog",
            name="medium",
            field=models.CharField(
                blank=True, max_length=255, verbose_name="Growing Medium"
            ),
        ),
        migrations.AddField(
            model_name="growlog",
            name="notes",
            field=models.TextField(blank=True, verbose_name="Additional Notes"),
        ),
        migrations.AddField(
            model_name="growlog",
            name="nutrients",
            field=models.TextField(blank=True, verbose_name="Nutrients"),
        ),
        migrations.AddField(
            model_name="growlog",
            name="views_count",
            field=models.PositiveIntegerField(default=0, verbose_name="Views"),
        ),
        migrations.AddField(
            model_name="growlog",
            name="yield_actual",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=8,
                null=True,
                verbose_name="Actual Yield (g)",
            ),
        ),
        migrations.AddField(
            model_name="growlog",
            name="yield_expected",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=8,
                null=True,
                verbose_name="Expected Yield (g)",
            ),
        ),
        migrations.AddField(
            model_name="growlogentry",
            name="activities",
            field=models.TextField(
                blank=True,
                help_text="Watering, feeding, training, etc.",
                verbose_name="Activities",
            ),
        ),
        migrations.AddField(
            model_name="growlogentry",
            name="ec",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=4,
                null=True,
                verbose_name="EC (mS/cm)",
            ),
        ),
        migrations.AddField(
            model_name="growlogentry",
            name="height",
            field=models.DecimalField(
                blank=True,
                decimal_places=1,
                max_digits=5,
                null=True,
                verbose_name="Height (cm)",
            ),
        ),
        migrations.AddField(
            model_name="growlogentry",
            name="notes",
            field=models.TextField(default="No notes", verbose_name="Notes"),
        ),
        migrations.AddField(
            model_name="growlogentry",
            name="nutrients_used",
            field=models.TextField(blank=True, verbose_name="Nutrients Used"),
        ),
        migrations.AddField(
            model_name="growlogentry",
            name="stage",
            field=models.CharField(
                choices=[
                    ("germination", "Germination"),
                    ("seedling", "Seedling"),
                    ("vegetative", "Vegetative"),
                    ("flowering", "Flowering"),
                    ("harvest", "Harvest"),
                    ("curing", "Curing"),
                    ("completed", "Completed"),
                ],
                default="germination",
                max_length=20,
                verbose_name="Stage",
            ),
        ),
        migrations.AddField(
            model_name="growlogentry",
            name="water_amount",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=5,
                null=True,
                verbose_name="Water (L)",
            ),
        ),
        migrations.AddField(
            model_name="growlogentry",
            name="width",
            field=models.DecimalField(
                blank=True,
                decimal_places=1,
                max_digits=5,
                null=True,
                verbose_name="Width (cm)",
            ),
        ),
        migrations.AlterField(
            model_name="growlogentry",
            name="humidity",
            field=models.DecimalField(
                blank=True,
                decimal_places=1,
                max_digits=4,
                null=True,
                verbose_name="Humidity (%)",
            ),
        ),
        migrations.AlterField(
            model_name="growlogentry",
            name="temperature",
            field=models.DecimalField(
                blank=True,
                decimal_places=1,
                max_digits=4,
                null=True,
                verbose_name="Temperature (°C)",
            ),
        ),
        migrations.CreateModel(
            name="GrowLogComment",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="Created at"),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name="Updated at"),
                ),
                ("text", models.TextField(verbose_name="Comment")),
                (
                    "author",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="growlog_comments",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "growlog",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="comments",
                        to="growlogs.growlog",
                    ),
                ),
            ],
            options={
                "verbose_name": "Grow Log Comment",
                "verbose_name_plural": "Grow Log Comments",
                "ordering": ["created_at"],
            },
        ),
    ]
