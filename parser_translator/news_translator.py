import requests
from bs4 import BeautifulSoup
import time

SITES = [
    ("Leafly", "https://www.leafly.com/news"),
    ("Ganjapreneur", "https://www.ganjapreneur.com/cannabis-news/"),
    ("Cannabis Science Tech", "https://www.cannabissciencetech.com/news"),
    ("Weedmaps", "https://weedmaps.com/news"),
    ("CannaConnection", "https://www.cannaconnection.com/news"),
    ("GPN Cannabis", "https://gpnmag.com/category/cannabis/"),
    ("MJMoment Health", "https://www.marijuanamoment.net/category/science-health/"),
    ("News-Medical", "https://www.news-medical.net/condition/Cannabis"),
]

KEYWORDS = ['grow', 'strain', 'technology', 'medical', 'hydroponic', 'fertilizer', 'lighting', 'genetics', 'report', 'review', 'disease']
EXCLUDE = ['policy', 'politic', 'market', 'business', 'economy', 'regulation']

def simple_translate(text, target="ru"):
    """Бесплатный перевод через LibreTranslate (ограниченно, но реально работает)"""
    try:
        resp = requests.post(
            "https://libretranslate.com/translate",
            data={
                "q": text,
                "source": "en",
                "target": target,
                "format": "text"
            },
            timeout=10
        )
        return resp.json().get("translatedText", "[перевод не получен]")
    except Exception as e:
        return f"[ошибка перевода: {e}]"

def filter_title(title):
    """Фильтрует нежелательные новости"""
    t = title.lower()
    if any(x in t for x in EXCLUDE):
        return False
    if any(x in t for x in KEYWORDS):
        return True
    return False

def collect_news():
    results = []
    for name, url in SITES:
        try:
            r = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
            soup = BeautifulSoup(r.text, "html.parser")
            links = []
            # Поиск ссылок на новости (упрощённо)
            for a in soup.find_all("a", href=True):
                title = a.get_text().strip()
                href = a['href']
                if not title or len(title) < 10:
                    continue
                if not href.startswith("http"):
                    href = url.rstrip("/") + "/" + href.lstrip("/")
                if filter_title(title):
                    links.append((title, href))
                if len(links) >= 3:
                    break
            for title, link in links:
                print(f"[{name}] {title} ({link})")
                # Скачиваем статью (поверхностно)
                article = ""
                try:
                    rr = requests.get(link, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
                    soup2 = BeautifulSoup(rr.text, "html.parser")
                    paras = [p.get_text().strip() for p in soup2.find_all("p") if len(p.get_text().strip()) > 40]
                    article = "\n".join(paras[:5])  # первые 5 абзацев
                except Exception as e:
                    article = f"[Ошибка загрузки статьи: {e}]"
                rus = simple_translate(title + "\n\n" + article)
                results.append({
                    "site": name,
                    "url": link,
                    "title": title,
                    "text": article,
                    "translated": rus
                })
                time.sleep(3)
        except Exception as e:
            print(f"Ошибка парсинга {url}: {e}")
    return results

def save_results(news):
    with open("translated_news.txt", "w", encoding="utf-8") as f:
        for item in news:
            f.write("="*50 + "\n")
            f.write(f"Источник: {item['site']}\n")
            f.write(f"URL: {item['url']}\n")
            f.write("Заголовок:\n" + item['title'] + "\n")
            f.write("Текст (ориг):\n" + item['text'] + "\n\n")
            f.write("Перевод:\n" + item['translated'] + "\n\n")

if __name__ == "__main__":
    news = collect_news()
    save_results(news)
    print("Готово! Файл translated_news.txt создан.")

