import requests
from bs4 import BeautifulSoup, Tag
from google.cloud import translate_v2 as translate
import os
import re
import json
from typing import List, Dict, Any, Optional

# --- 1. Настройка Google Cloud Translation API ---
# ВАЖНО: Укажи путь к твоему JSON-файлу с ключом сервисного аккаунта Google Cloud Translation API.
# Это должен быть абсолютный или относительный путь от места запуска скрипта.

def init_translation_client():
    """Инициализация клиента Google Cloud Translation API с обработкой ошибок"""
    try:
        # Устанавливаем переменную окружения для ключа API
        api_key_path = os.path.join(os.path.dirname(__file__), "besedka-api-key.json")
        if os.path.exists(api_key_path):
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = api_key_path

        translate_client = translate.Client()
        print("✅ Google Cloud Translation API успешно инициализирован")
        return translate_client
    except Exception as e:
        print(f"❌ Ошибка инициализации Google Cloud Translation API: {e}")
        print("🔧 Убедитесь, что:")
        print("   1. Файл besedka-api-key.json находится в папке parser_translator/")
        print("   2. В файле корректные данные сервисного аккаунта")
        print("   3. API включен в Google Cloud Console")
        return None

# --- 2. Список сайтов для парсинга ---
SITES = {
    "Leafly News": "https://www.leafly.com/news",
    "Leafly Strains": "https://www.leafly.com/strains",
    "Marijuana Moment": "https://www.marijuanamoment.net/",
    "Ganjapreneur News": "https://www.ganjapreneur.com/cannabis-news/",
    "Ganjapreneur Cultivation": "https://www.ganjapreneur.com/news/cannabis-cultivation/",
    "GPN Mag Cannabis": "https://gpnmag.com/category/cannabis/",
    "News-Medical Cannabis": "https://news-medical.net/condition/Cannabis",
    "Cannabis Science Tech": "https://www.cannabissciencetech.com/news",
    "CannaConnection Strains": "https://www.cannaconnection.com/strains",
}

# --- 3. Вспомогательная функция для получения полного текста новости по URL ---
def get_full_article_content(article_url: str) -> str:
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

        # Попытка найти основной контент в разных общих местах
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

        # Если ничего не нашли в специфичных блоках, попробуем собрать все параграфы
        if not full_text:
            paragraphs = soup.find_all('p')
            for p in paragraphs:
                if isinstance(p, Tag):
                    text = p.get_text(strip=True)
                    if text and len(text) > 20:
                        full_text.append(text)

        combined_text = '\n'.join(full_text)
        return combined_text[:1000] + '...' if len(combined_text) > 1000 else combined_text

    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка запроса при получении полного текста статьи {article_url}: {e}")
        return ""
    except Exception as e:
        print(f"❌ Общая ошибка при получении полного текста статьи {article_url}: {e}")
        return ""

# --- 4. Функция для перевода текста ---
def translate_text(text: str, translate_client, target_language: str = 'ru') -> str:
    """Переводит текст с помощью Google Cloud Translation API"""
    if not text or text.strip() == "N/A" or not translate_client:
        return text

    try:
        # Ограничиваем длину текста для API
        if len(text) > 5000:
            text = text[:5000] + "..."

        result = translate_client.translate(text, target_language=target_language)
        return result['translatedText']
    except Exception as e:
        print(f"❌ Ошибка при переводе текста: {e}")
        return text

# --- 5. Функция для безопасного извлечения текста из элемента ---
def safe_get_text(element) -> str:
    """Безопасно извлекает текст из BeautifulSoup элемента"""
    if element and isinstance(element, Tag):
        return element.get_text(strip=True)
    return "N/A"

def safe_get_attr(element, attr: str) -> str:
    """Безопасно извлекает атрибут из BeautifulSoup элемента"""
    if element and isinstance(element, Tag) and element.has_attr(attr):
        return element[attr]
    return "N/A"

# --- 6. Функция для парсинга каждого сайта ---
def parse_site(site_name: str, url: str) -> List[Dict[str, Any]]:
    """Парсит новости с указанного сайта"""
    print(f"🔍 Парсинг {site_name} ({url})...")
    articles = []

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.75 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Универсальный парсинг для всех сайтов
        if "leafly.com/news" in url:
            articles = parse_leafly_news(soup, site_name)
        elif "leafly.com/strains" in url:
            articles = parse_leafly_strains(soup, site_name)
        elif "marijuanamoment.net" in url:
            articles = parse_marijuana_moment(soup, site_name)
        elif "ganjapreneur.com" in url:
            articles = parse_ganjapreneur(soup, site_name)
        elif "gpnmag.com" in url:
            articles = parse_gpn_mag(soup, site_name)
        elif "news-medical.net" in url:
            articles = parse_news_medical(soup, site_name)
        elif "cannabissciencetech.com" in url:
            articles = parse_cannabis_science_tech(soup, site_name)
        elif "cannaconnection.com" in url:
            articles = parse_cannaconnection(soup, site_name)
        else:
            print(f"⚠️ Для сайта {site_name} не найдена специфичная логика парсинга")

    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка запроса к {site_name} ({url}): {e}")
    except Exception as e:
        print(f"❌ Общая ошибка при парсинге {site_name} ({url}): {e}")

    print(f"✅ Найдено {len(articles)} статей с {site_name}")
    return articles

def parse_leafly_news(soup: BeautifulSoup, site_name: str) -> List[Dict[str, Any]]:
    """Парсит новости с Leafly News"""
    articles = []
    article_cards = soup.find_all('div', class_='post-card', limit=10)

    for card in article_cards:
        if not isinstance(card, Tag):
            continue

        title_tag = card.find('h2', class_='post-card__title')
        link_tag = card.find('a', class_='post-card__link')
        image_tag = card.find('img', class_='post-card__image')
        date_tag = card.find('time', class_='post-card__date')

        title = safe_get_text(title_tag)
        link_href = safe_get_attr(link_tag, 'href')
        link = f"https://www.leafly.com{link_href}" if link_href != "N/A" else "N/A"
        image_url = safe_get_attr(image_tag, 'src')
        date_published = safe_get_text(date_tag)

        if title != "N/A" and link != "N/A":
            articles.append({
                'title': title,
                'url': link,
                'source': site_name,
                'image_url': image_url,
                'date_published': date_published,
                'full_text': get_full_article_content(link)
            })

    return articles

def parse_leafly_strains(soup: BeautifulSoup, site_name: str) -> List[Dict[str, Any]]:
    """Парсит штаммы с Leafly Strains"""
    articles = []
    strain_cards = soup.find_all('a', class_='category-card', limit=10)

    for card in strain_cards:
        if not isinstance(card, Tag):
            continue

        title_tag = card.find('h3', class_='category-card__name')
        link_href = safe_get_attr(card, 'href')
        image_tag = card.find('img', class_='category-card__image')

        title = safe_get_text(title_tag)
        link = f"https://www.leafly.com{link_href}" if link_href != "N/A" else "N/A"
        image_url = safe_get_attr(image_tag, 'src')

        if title != "N/A" and link != "N/A":
            articles.append({
                'title': f"Штамм: {title}",
                'url': link,
                'source': site_name,
                'image_url': image_url,
                'date_published': "N/A",
                'full_text': get_full_article_content(link)
            })

    return articles

def parse_marijuana_moment(soup: BeautifulSoup, site_name: str) -> List[Dict[str, Any]]:
    """Парсит новости с Marijuana Moment"""
    articles = []
    entries = soup.find_all('article', class_='news-article', limit=10)

    for entry in entries:
        if not isinstance(entry, Tag):
            continue

        title_tag = entry.find('h2', class_='entry-title')
        link_tag = title_tag.find('a') if title_tag else None
        image_tag = entry.find('img', class_='featured-image')
        date_tag = entry.find('time', class_='entry-date')

        title = safe_get_text(link_tag)
        link = safe_get_attr(link_tag, 'href')
        image_url = safe_get_attr(image_tag, 'src')
        date_published = safe_get_attr(date_tag, 'datetime')

        if title != "N/A" and link != "N/A":
            articles.append({
                'title': title,
                'url': link,
                'source': site_name,
                'image_url': image_url,
                'date_published': date_published,
                'full_text': get_full_article_content(link)
            })

    return articles

def parse_ganjapreneur(soup: BeautifulSoup, site_name: str) -> List[Dict[str, Any]]:
    """Парсит новости с Ganjapreneur"""
    articles = []
    article_blocks = soup.find_all('div', class_='elementor-post__text', limit=10)

    for block in article_blocks:
        if not isinstance(block, Tag):
            continue

        title_tag = block.find('h3', class_='elementor-post__title')
        link_tag = title_tag.find('a') if title_tag else None
        date_tag = block.find('span', class_='elementor-post-date')

        # Изображение может быть в соседнем блоке
        image_container = block.find_previous_sibling('div', class_='elementor-post__thumbnail')
        image_tag = image_container.find('img') if image_container else None

        title = safe_get_text(link_tag)
        link = safe_get_attr(link_tag, 'href')
        image_url = safe_get_attr(image_tag, 'src')
        date_published = safe_get_text(date_tag)

        if title != "N/A" and link != "N/A":
            articles.append({
                'title': title,
                'url': link,
                'source': site_name,
                'image_url': image_url,
                'date_published': date_published,
                'full_text': get_full_article_content(link)
            })

    return articles

def parse_gpn_mag(soup: BeautifulSoup, site_name: str) -> List[Dict[str, Any]]:
    """Парсит новости с GPN Mag"""
    articles = []
    article_cards = soup.find_all('div', class_='entry-box', limit=10)

    for card in article_cards:
        if not isinstance(card, Tag):
            continue

        title_tag = card.find('h2', class_='entry-title')
        link_tag = title_tag.find('a') if title_tag else None
        image_tag = card.find('img')
        date_tag = card.find('span', class_='published')

        title = safe_get_text(link_tag)
        link = safe_get_attr(link_tag, 'href')
        image_url = safe_get_attr(image_tag, 'src')
        date_published = safe_get_text(date_tag)

        if title != "N/A" and link != "N/A":
            articles.append({
                'title': title,
                'url': link,
                'source': site_name,
                'image_url': image_url,
                'date_published': date_published,
                'full_text': get_full_article_content(link)
            })

    return articles

def parse_news_medical(soup: BeautifulSoup, site_name: str) -> List[Dict[str, Any]]:
    """Парсит новости с News Medical"""
    articles = []
    items = soup.find_all('li', class_='article-list-item', limit=10)

    for item in items:
        if not isinstance(item, Tag):
            continue

        title_container = item.find('h3', class_='title')
        link_tag = title_container.find('a') if title_container else None
        image_tag = item.find('img')
        date_tag = item.find('p', class_='pub-date')

        title = safe_get_text(link_tag)
        link_href = safe_get_attr(link_tag, 'href')
        link = f"https://www.news-medical.net{link_href}" if link_href != "N/A" else "N/A"
        image_url = safe_get_attr(image_tag, 'src')
        date_text = safe_get_text(date_tag)
        date_published = date_text.replace('Published: ', '') if date_text != "N/A" else "N/A"

        if title != "N/A" and link != "N/A":
            articles.append({
                'title': title,
                'url': link,
                'source': site_name,
                'image_url': image_url,
                'date_published': date_published,
                'full_text': get_full_article_content(link)
            })

    return articles

def parse_cannabis_science_tech(soup: BeautifulSoup, site_name: str) -> List[Dict[str, Any]]:
    """Парсит новости с Cannabis Science Tech"""
    articles = []
    article_cards = soup.find_all('article', class_='node--type-news', limit=10)

    for card in article_cards:
        if not isinstance(card, Tag):
            continue

        title_tag = card.find('h2', class_='node__title')
        link_tag = title_tag.find('a') if title_tag else None
        image_tag = card.find('img')

        title = safe_get_text(link_tag)
        link_href = safe_get_attr(link_tag, 'href')
        link = f"https://www.cannabissciencetech.com{link_href}" if link_href != "N/A" else "N/A"
        image_url = safe_get_attr(image_tag, 'src')

        if title != "N/A" and link != "N/A":
            articles.append({
                'title': title,
                'url': link,
                'source': site_name,
                'image_url': image_url,
                'date_published': "N/A",
                'full_text': get_full_article_content(link)
            })

    return articles

def parse_cannaconnection(soup: BeautifulSoup, site_name: str) -> List[Dict[str, Any]]:
    """Парсит штаммы с CannaConnection"""
    articles = []
    strain_blocks = soup.find_all('div', class_='strain-item', limit=10)

    for block in strain_blocks:
        if not isinstance(block, Tag):
            continue

        title_tag = block.find('h3')
        link_tag = block.find('a')
        image_tag = block.find('img')

        title = safe_get_text(title_tag)
        link = safe_get_attr(link_tag, 'href')
        image_url = safe_get_attr(image_tag, 'src')

        if title != "N/A" and link != "N/A":
            articles.append({
                'title': f"Штамм: {title}",
                'url': link,
                'source': site_name,
                'image_url': image_url,
                'date_published': "N/A",
                'full_text': get_full_article_content(link)
            })

    return articles

# --- 7. Основная функция для запуска парсинга и перевода ---
def run_parser_and_translator(output_filename: str = "translated_cannabis_news.json",
                             max_articles_per_site: int = 2) -> bool:
    """Основная функция парсинга и перевода новостей"""

    # Инициализация клиента перевода
    translate_client = init_translation_client()

    all_translated_news = []
    total_parsed = 0

    print("🚀 Начинаем процесс парсинга и перевода...")
    print(f"📊 Максимум статей с каждого сайта: {max_articles_per_site}")

    for site_name, url in SITES.items():
        print(f"\n📰 Обрабатываем {site_name}...")
        articles = parse_site(site_name, url)

        # Ограничиваем количество статей с каждого сайта
        articles = articles[:max_articles_per_site]

        for i, article in enumerate(articles, 1):
            print(f"   📄 Обрабатываем статью {i}/{len(articles)}: {article['title'][:50]}...")

            original_title = article.get('title', 'N/A')
            original_text = article.get('full_text', 'N/A')

            # Перевод заголовка и текста
            translated_title = translate_text(original_title, translate_client) if translate_client else original_title
            translated_text = translate_text(original_text, translate_client) if translate_client else original_text

            all_translated_news.append({
                'source': article.get('source', 'N/A'),
                'original_title': original_title,
                'translated_title': translated_title,
                'original_text': original_text,
                'translated_text': translated_text,
                'url': article.get('url', 'N/A'),
                'image_url': article.get('image_url', 'N/A'),
                'date_published': article.get('date_published', 'N/A'),
                'parsed_at': __import__('datetime').datetime.now().isoformat()
            })
            total_parsed += 1

    # Сохранение результатов в JSON
    try:
        output_path = os.path.join(os.path.dirname(__file__), output_filename)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(all_translated_news, f, ensure_ascii=False, indent=2)

        print(f"\n✅ Парсинг завершен успешно!")
        print(f"📊 Всего обработано статей: {total_parsed}")
        print(f"💾 Результаты сохранены в: {output_path}")
        return True

    except Exception as e:
        print(f"❌ Ошибка при сохранении результатов: {e}")
        return False

# --- 8. Запуск скрипта ---
if __name__ == "__main__":
    success = run_parser_and_translator(
        output_filename="cannabis_news_parsed.json",
        max_articles_per_site=2
    )

    if success:
        print("\n🎉 Парсер работает корректно!")
        print("🔧 Готов к интеграции в проект 'Беседка'")
    else:
        print("\n❌ Произошли ошибки при выполнении парсера")
