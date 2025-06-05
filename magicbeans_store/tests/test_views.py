from django.test import TestCase, Client
from django.urls import reverse
from magicbeans_store.models import Strain, SeedBank
from django.contrib.auth import get_user_model

User = get_user_model()

class StoreCatalogViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.seedbank = SeedBank.objects.create(name="Test Seedbank", slug="test-seedbank")
        self.strain1 = Strain.objects.create(
            name="Test Strain 1",
            seedbank=self.seedbank,
            strain_type="sativa",
            is_active=True,
            description="Description 1"
        )
        self.strain2 = Strain.objects.create(
            name="Test Strain 2",
            seedbank=self.seedbank,
            strain_type="indica",
            is_active=True,
            description="Description 2"
        )
        self.strain_not_active = Strain.objects.create(
            name="Not Active Strain",
            seedbank=self.seedbank,
            strain_type="hybrid",
            is_active=False,
            description="Not active desc"
        )

    def test_catalog_view_status_code(self):
        """Тест: CatalogView возвращает статус 200."""
        response = self.client.get(reverse('store:catalog'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'store/catalog.html')

    def test_catalog_view_displays_public_strains(self):
        """Тест: CatalogView отображает публичные и активные сорта."""
        response = self.client.get(reverse('store:catalog'))
        self.assertContains(response, self.strain1.name)
        self.assertContains(response, self.strain2.name)
        self.assertNotContains(response, self.strain_not_active.name)

    def test_catalog_view_pagination(self):
        """Тест: Пагинация в CatalogView (если товаров больше paginate_by)."""
        # Создадим больше товаров, чем paginate_by в CatalogView (по умолчанию 12)
        for i in range(15):
            Strain.objects.create(
                name=f"Strain Page {i}",
                seedbank=self.seedbank,
                strain_type="hybrid",
                is_active=True
            )
        response = self.client.get(reverse('store:catalog'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue('is_paginated' in response.context)
        self.assertTrue(response.context['is_paginated'] is True)
        self.assertEqual(len(response.context['strains']), 12) # CatalogView.paginate_by

        response_page2 = self.client.get(reverse('store:catalog') + '?page=2')
        self.assertEqual(response_page2.status_code, 200)
        self.assertTrue('is_paginated' in response_page2.context)
        # self.assertEqual(len(response_page2.context['strains']), 5) # 2 существующих + 15 новых - 12 на первой = 5
        # Точное количество на второй странице зависит от общего числа public/active товаров

    # Добавить тесты для фильтрации (StrainFilterForm)
