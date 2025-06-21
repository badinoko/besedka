import os
import sys
import json
import requests
from datetime import datetime, timedelta
from django.utils import timezone
from django.conf import settings
from django.core.management.base import BaseCommand
from bs4 import BeautifulSoup, Tag
from typing import List, Dict, Any, Optional

# Добавляем путь к парсеру
parser_path = os.path.join(settings.BASE_DIR, 'parser_translator')
if parser_path not in sys.path:
    sys.path.append(parser_path)

from .models import NewsSource, ParsedNews, ParsingLog, NewsCategory

class NewsParsingService:
    """Сервис для парсинга новостей"""

    def __init__(self):
        self.translation_client = None
        self.errors = []

    def init_translation_client(self):
        """Инициализация клиента Google Cloud Translation API"""
        try:
            from google.cloud import translate_v2 as translate

            # Устанавливаем переменную окружения для ключа API
            api_key_path = os.path.join(settings.BASE_DIR, 'parser_translator', 'besedka-api-key.json')
            if os.path.exists(api_key_path):
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = api_key_path

            self.translation_client = translate.Client()
            return True
        except Exception as e:
            self.errors.append(f"Ошибка инициализации Google Cloud Translation API: {e}")
            return False

    def translate_text(self, text: str, target_language: str = 'ru') -> str:
        """Переводит текст с помощью Google Cloud Translation API"""
        if not text or text.strip() == "N/A" or not self.translation_client:
            return text

        try:
            # Ограничиваем длину текста для API
            if len(text) > 5000:
                text = text[:5000] + "..."

            result = self.translation_client.translate(text, target_language=target_language)
            return result['translatedText']
        except Exception as e:
            self.errors.append(f"Ошибка при переводе текста: {e}")
            return text

    def safe_get_text(self, element) -> str:
        """Безопасно извлекает текст из BeautifulSoup элемента"""
        if element and isinstance(element, Tag):
            return element.get_text(strip=True)
        return "N/A"

    def safe_get_attr(self, element, attr: str) -> str:
        """Безопасно извлекает атрибут из BeautifulSoup элемента"""
        if element and isinstance(element, Tag) and element.has_attr(attr):
            return element[attr]
        return "N/A"

    def get_full_article_content(self, article_url: str) -> str:
        """Получает полный текст статьи по URL"""
        if not article_url or article_url == "N/A":
            return ""

        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.75 Safari/537.36'
            }
            response = requests.get(article_url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            # Попытка найти основной контент
            content_selectors = [
                'div[class*="content"]',
                'div[class*="article-body"]',
                'div[class*="post-content"]',
                'div[class*="entry-content"]',
                'article',
                'main'
            ]

            full_text = []
            for selector in content_selectors:
                content_div = soup.select_one(selector)
                if content_div and isinstance(content_div, Tag):
                    paragraphs = content_div.find_all('p')
                    for p in paragraphs:
                        if isinstance(p, Tag):
                            text = p.get_text(strip=True)
                            if text and len(text) > 20:
                                full_text.append(text)
                    if full_text:
                        break

            combined_text = '\n'.join(full_text)
            return combined_text[:2000] + '...' if len(combined_text) > 2000 else combined_text

        except Exception as e:
            self.errors.append(f"Ошибка при получении полного текста статьи {article_url}: {e}")
            return ""

    def parse_leafly_news(self, soup: BeautifulSoup, source_name: str) -> List[Dict[str, Any]]:
        """Парсит новости с Leafly News"""
        articles = []
        article_cards = soup.find_all('div', class_='post-card', limit=5)

        for card in article_cards:
            if not isinstance(card, Tag):
                continue

            title_tag = card.find('h2', class_='post-card__title')
            link_tag = card.find('a', class_='post-card__link')
            image_tag = card.find('img', class_='post-card__image')
            date_tag = card.find('time', class_='post-card__date')

            title = self.safe_get_text(title_tag)
            link_href = self.safe_get_attr(link_tag, 'href')
            link = f"https://www.leafly.com{link_href}" if link_href != "N/A" else "N/A"
            image_url = self.safe_get_attr(image_tag, 'src')
            date_published = self.safe_get_text(date_tag)

            if title != "N/A" and link != "N/A":
                articles.append({
                    'title': title,
                    'url': link,
                    'source': source_name,
                    'image_url': image_url,
                    'date_published': date_published,
                    'full_text': self.get_full_article_content(link)
                })

        return articles

    def parse_generic_news(self, soup: BeautifulSoup, source_name: str) -> List[Dict[str, Any]]:
        """Универсальный парсер для новостных сайтов"""
        articles = []

        # Ищем общие селекторы для статей
        article_selectors = [
            'article',
            'div[class*="post"]',
            'div[class*="article"]',
            'div[class*="news"]',
            'div[class*="entry"]',
            'div[class*="item"]'
        ]

        for selector in article_selectors:
            elements = soup.select(selector)[:5]  # Берем максимум 5 статей

            for element in elements:
                if not isinstance(element, Tag):
                    continue

                # Ищем заголовок
                title_element = (
                    element.find('h1') or
                    element.find('h2') or
                    element.find('h3') or
                    element.find('[class*="title"]') or
                    element.find('[class*="headline"]')
                )

                # Ищем ссылку
                link_element = (
                    element.find('a') or
                    title_element.find('a') if title_element else None
                )

                # Ищем изображение
                img_element = element.find('img')

                title = self.safe_get_text(title_element)
                link = self.safe_get_attr(link_element, 'href')
                image_url = self.safe_get_attr(img_element, 'src')

                # Проверяем и исправляем относительные ссылки
                if link != "N/A" and not link.startswith('http'):
                    base_url = f"https://{source_name.lower().replace(' ', '')}.com"
                    link = f"{base_url}{link}" if link.startswith('/') else f"{base_url}/{link}"

                if title != "N/A" and link != "N/A" and len(title) > 10:
                    articles.append({
                        'title': title,
                        'url': link,
                        'source': source_name,
                        'image_url': image_url,
                        'date_published': "N/A",
                        'full_text': self.get_full_article_content(link)
                    })

            if articles:
                break  # Если нашли статьи, прекращаем поиск

        return articles

    def parse_source(self, source: NewsSource) -> List[Dict[str, Any]]:
        """Парсит новости с одного источника"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.75 Safari/537.36'
            }
            response = requests.get(source.url, headers=headers, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            # Специализированный парсинг для известных сайтов
            if "leafly.com/news" in source.url:
                return self.parse_leafly_news(soup, source.name)
            else:
                return self.parse_generic_news(soup, source.name)

        except Exception as e:
            self.errors.append(f"Ошибка при парсинге {source.name} ({source.url}): {e}")
            return []

    def create_test_articles(self) -> List[Dict[str, Any]]:
        """Создает тестовые статьи для демонстрации"""
        test_articles = [
            {
                'title': 'Новые методы выращивания каннабиса в домашних условиях',
                'url': 'https://example.com/growing-methods',
                'source': 'Тестовый источник',
                'image_url': 'N/A',
                'date_published': '2025-01-30',
                'full_text': 'Современные технологии позволяют выращивать каннабис в домашних условиях с максимальной эффективностью. В этой статье мы рассмотрим основные методы гидропоники, освещения LED и контроля климата для получения высококачественного урожая.'
            },
            {
                'title': 'Медицинский каннабис: последние исследования и открытия',
                'url': 'https://example.com/medical-research',
                'source': 'Тестовый источник',
                'image_url': 'N/A',
                'date_published': '2025-01-29',
                'full_text': 'Недавние исследования показывают новые терапевтические возможности каннабиса. Ученые обнаружили эффективность каннабиноидов в лечении различных заболеваний, включая эпилепсию, хроническую боль и тревожные расстройства.'
            },
            {
                'title': 'Лучшие сорта каннабиса для начинающих гроверов',
                'url': 'https://example.com/beginner-strains',
                'source': 'Тестовый источник',
                'image_url': 'N/A',
                'date_published': '2025-01-28',
                'full_text': 'Для начинающих гроверов важно выбрать правильные сорта каннабиса. Мы рекомендуем автоцветущие сорта с высокой устойчивостью к болезням и простыми требованиями к уходу.'
            }
        ]
        return test_articles

    def process_article(self, article_data: Dict[str, Any], source: NewsSource) -> Optional[ParsedNews]:
        """Обрабатывает одну статью и сохраняет в базу данных"""
        try:
            # Проверяем, не существует ли уже такая статья
            if ParsedNews.objects.filter(original_url=article_data['url']).exists():
                return None

            # Переводим текст
            original_title = article_data['title']
            original_content = article_data['full_text']

            translated_title = self.translate_text(original_title)
            translated_content = self.translate_text(original_content)

            # Создаем краткое описание
            summary = translated_content[:300] + "..." if len(translated_content) > 300 else translated_content

            # Определяем категорию (простая логика на основе ключевых слов)
            category = self.determine_category(translated_title + " " + translated_content)

            # Парсим дату
            parsed_date = self.parse_date(article_data.get('date_published', ''))

            # Создаем запись
            parsed_news = ParsedNews.objects.create(
                title=translated_title,
                original_title=original_title,
                content=translated_content,
                original_content=original_content,
                summary=summary,
                source=source,
                original_url=article_data['url'],
                image_url=article_data.get('image_url'),
                original_date=parsed_date,
                category=category
            )

            return parsed_news

        except Exception as e:
            self.errors.append(f"Ошибка при обработке статьи {article_data.get('title', 'Неизвестно')}: {e}")
            return None

    def determine_category(self, text: str) -> Optional[NewsCategory]:
        """Определяет категорию новости на основе содержания"""
        text_lower = text.lower()

        # Создаем базовые категории если их нет
        categories_map = {
            'выращивание': 'Выращивание',
            'медицин': 'Медицинский каннабис',
            'сорт': 'Сорта и штаммы',
            'оборудование': 'Оборудование',
            'освещение': 'Освещение',
            'удобрения': 'Удобрения',
            'гидропоник': 'Гидропоника',
            'законодательство': 'Законодательство',
            'исследования': 'Исследования'
        }

        for keyword, category_name in categories_map.items():
            if keyword in text_lower:
                category, created = NewsCategory.objects.get_or_create(
                    name=category_name,
                    defaults={'description': f'Новости о {keyword}'}
                )
                return category

        # Возвращаем общую категорию
        general_category, created = NewsCategory.objects.get_or_create(
            name='Общие новости',
            defaults={'description': 'Общие новости о каннабисе'}
        )
        return general_category

    def parse_date(self, date_str: str) -> Optional[datetime]:
        """Парсит дату из строки"""
        if not date_str or date_str == "N/A":
            return None

        date_formats = [
            '%Y-%m-%d',
            '%d.%m.%Y',
            '%d/%m/%Y',
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%dT%H:%M:%S'
        ]

        for fmt in date_formats:
            try:
                return datetime.strptime(date_str[:len(fmt)], fmt)
            except ValueError:
                continue

        return None

    def run_parsing(self) -> Dict[str, Any]:
        """Основная функция запуска парсинга"""
        log = ParsingLog.objects.create()

        try:
            # Инициализируем переводчик
            translation_available = self.init_translation_client()

            # Получаем активные источники
            sources = NewsSource.objects.filter(parsing_enabled=True)
            log.total_sources = sources.count()
            log.save()

            total_articles = 0
            new_articles = 0
            successful_sources = 0

            # Если нет реальных источников, создаем тестовые статьи
            if not sources.exists():
                # Создаем тестовый источник
                test_source, created = NewsSource.objects.get_or_create(
                    name="Тестовый источник",
                    defaults={'url': 'https://example.com', 'parsing_enabled': True}
                )

                # Получаем тестовые статьи
                test_articles = self.create_test_articles()

                for article_data in test_articles:
                    total_articles += 1
                    parsed_news = self.process_article(article_data, test_source)
                    if parsed_news:
                        new_articles += 1

                successful_sources = 1
                test_source.last_parsed = timezone.now()
                test_source.save()
            else:
                # Парсим реальные источники
                for source in sources:
                    try:
                        articles = self.parse_source(source)

                        for article_data in articles:
                            total_articles += 1
                            parsed_news = self.process_article(article_data, source)
                            if parsed_news:
                                new_articles += 1

                        if articles:
                            successful_sources += 1

                        source.last_parsed = timezone.now()
                        source.save()

                    except Exception as e:
                        self.errors.append(f"Ошибка при обработке источника {source.name}: {e}")

            # Обновляем лог
            log.finished_at = timezone.now()
            log.status = 'completed'
            log.successful_sources = successful_sources
            log.total_articles = total_articles
            log.new_articles = new_articles
            log.errors = '\n'.join(self.errors) if self.errors else ''
            log.notes = f"Переводчик: {'доступен' if translation_available else 'недоступен'}"
            log.save()

            return {
                'success': True,
                'total_articles': total_articles,
                'new_articles': new_articles,
                'successful_sources': successful_sources,
                'errors': self.errors
            }

        except Exception as e:
            log.finished_at = timezone.now()
            log.status = 'failed'
            log.errors = str(e)
            log.save()

            return {
                'success': False,
                'error': str(e),
                'total_articles': 0,
                'new_articles': 0
            }
