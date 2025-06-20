# Generated by Django 4.2.21 on 2025-05-21 18:37

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="GrowLog",
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
                ("is_public", models.BooleanField(default=True, verbose_name="Public")),
                ("title", models.CharField(max_length=255, verbose_name="Title")),
                ("start_date", models.DateField(verbose_name="Start Date")),
                (
                    "end_date",
                    models.DateField(blank=True, null=True, verbose_name="End Date"),
                ),
                (
                    "setup_description",
                    models.TextField(verbose_name="Setup Description"),
                ),
            ],
            options={
                "verbose_name": "Grow Log",
                "verbose_name_plural": "Grow Logs",
                "ordering": ["-start_date"],
            },
        ),
        migrations.CreateModel(
            name="GrowLogEntry",
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
                ("day", models.PositiveIntegerField(verbose_name="Day")),
                ("description", models.TextField(verbose_name="Description")),
                (
                    "temperature",
                    models.DecimalField(
                        blank=True,
                        decimal_places=1,
                        max_digits=4,
                        null=True,
                        verbose_name="Temperature",
                    ),
                ),
                (
                    "humidity",
                    models.DecimalField(
                        blank=True,
                        decimal_places=1,
                        max_digits=4,
                        null=True,
                        verbose_name="Humidity %",
                    ),
                ),
                (
                    "ph",
                    models.DecimalField(
                        blank=True,
                        decimal_places=1,
                        max_digits=3,
                        null=True,
                        verbose_name="pH",
                    ),
                ),
                (
                    "growlog",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="entries",
                        to="growlogs.growlog",
                    ),
                ),
            ],
            options={
                "verbose_name": "Grow Log Entry",
                "verbose_name_plural": "Grow Log Entries",
                "ordering": ["day"],
            },
        ),
    ]
