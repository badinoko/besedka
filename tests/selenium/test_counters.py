import time
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# Используем общие утилиты/фикстуры из существующего комплексного теста
from tests.selenium.test_full_site import (
    driver as global_driver_fixture,  # WebDriver фикстура
    login,
    USERS,
    BASE_URL,
)

# Глобально разрешаем доступ к БД внутри live_server
pytestmark = pytest.mark.django_db(transaction=True)

@pytest.mark.usefixtures("global_setup")
class TestCounters:
    @pytest.fixture(scope="class", autouse=True)
    def global_setup(self, driver, base_url):  # noqa: D401
        """Логинимся единоразово под test_user перед серией проверок."""
        # Обновляем глобальный BASE_URL в модуле test_full_site, чтобы login() использовал корректный URL
        import importlib
        from tests.selenium import test_full_site as tfs

        tfs.BASE_URL = base_url

        creds = USERS["user"]
        login(driver, creds["username"], creds["password"])
        # Ожидаем появления навигации после логина (подтверждение успешного входа)
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "header .navbar-brand"))
        )
        yield
        # После завершения тестов выходим, чтобы не влиять на другие сессии
        driver.get(f"{base_url}/accounts/logout/")

    def _click_like_and_assert_irreversible(self, driver, btn_selector, count_selector):
        wait = WebDriverWait(driver, 15)
        like_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, btn_selector)))
        count_el = driver.find_element(By.CSS_SELECTOR, count_selector)
        initial_count = int(count_el.text.strip())

        # Кликаем первый раз – ожидаем +1
        like_btn.click()
        time.sleep(1)  # ждём AJAX
        new_count = int(count_el.text.strip())
        assert new_count == initial_count + 1, "После первого лайка счётчик не увеличился на 1"

        # Повторный клик (кнопка может стать неактивной, но на всякий случай пробуем)
        try:
            like_btn.click()
            time.sleep(0.5)
        except Exception:
            # Если клик недоступен – это ок (кнопка задизейблена), значит необратимо
            pass
        final_count = int(count_el.text.strip())
        assert (
            final_count == new_count
        ), "Повторный клик изменил счётчик – лайк должен быть необратим"

    def _verify_card_counter_updated(self, driver, list_url, card_selector, stat_selector, expected_value):
        """Переходит на list_url, находит первую карточку и сравнивает стат-значение."""
        wait = WebDriverWait(driver, 15)
        driver.get(list_url)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, card_selector)))
        like_span = driver.find_element(By.CSS_SELECTOR, stat_selector)
        current_count = int(like_span.text.strip())
        assert (
            current_count == expected_value
        ), f"Счётчик на карточке (expected {expected_value}) отображает {current_count}"

    def _add_comment_and_reply(self, driver, unique_prefix="Comm"):
        """Добавляет комментарий и ответ, возвращает ожидаемое увеличение (2)."""
        wait = WebDriverWait(driver, 10)
        comment_box = driver.find_element(By.CSS_SELECTOR, "#comment-form textarea")
        unique_comment = f"{unique_prefix}-{int(time.time())}"
        comment_box.send_keys(unique_comment)
        driver.find_element(By.CSS_SELECTOR, "#comment-form button[type='submit']").click()
        # Ждём появления комментария без перезагрузки
        wait.until(EC.text_to_be_present_in_element((By.CSS_SELECTOR, "#comments"), unique_comment))

        # Оставляем ответ на только что созданный комментарий
        reply_btns = driver.find_elements(By.CSS_SELECTOR, ".comment-reply-btn")
        if not reply_btns:
            return 1  # только родительский комментарий
        reply_btns[-1].click()
        reply_box = driver.find_element(By.CSS_SELECTOR, ".reply-form textarea")
        unique_reply = f"Reply-{int(time.time())}"
        reply_box.send_keys(unique_reply)
        driver.find_element(By.CSS_SELECTOR, ".reply-form button[type='submit']").click()
        # Проверяем появление
        wait.until(EC.text_to_be_present_in_element((By.CSS_SELECTOR, "#comments"), unique_reply))
        return 2  # комментарий + ответ

    def test_gallery_photo_like_comments_counters(self, driver, base_url):
        wait = WebDriverWait(driver, 20)
        # Открываем галерею и первую фото
        driver.get(f"{base_url}/gallery/")
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".unified-card a")))
        first_photo = driver.find_element(By.CSS_SELECTOR, ".unified-card a")
        first_photo.click()

        # Проверяем лайк
        self._click_like_and_assert_irreversible(
            driver,
            btn_selector="#like-photo-btn",
            count_selector="#likes-count",
        )

        # Добавляем комментарий и смотрим счётчик
        comment_box = driver.find_element(By.CSS_SELECTOR, "#comment-form textarea")
        unique_comment = f"SeleniumComment {int(time.time())}"
        comment_box.send_keys(unique_comment)
        driver.find_element(By.CSS_SELECTOR, "#comment-form button[type='submit']").click()
        time.sleep(1)
        assert unique_comment in driver.page_source, "Комментарий не появился без перезагрузки"

        # Фиксируем итоговый счётчик лайков
        likes_after = int(driver.find_element(By.CSS_SELECTOR, "#likes-count").text.strip())

        # Возвращаемся назад и проверяем счётчик в карточке
        self._verify_card_counter_updated(
            driver,
            f"{base_url}/gallery/",
            card_selector=".unified-card:first-child .stat-item.likes span",
            stat_selector=".unified-card:first-child .stat-item.likes span",
            expected_value=likes_after,
        )

    def test_news_post_like_views_comments_counters(self, driver, base_url):
        wait = WebDriverWait(driver, 20)
        # Переход на главную новостей и открываем первую
        driver.get(f"{base_url}/news/")
        wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".news-card a"))
        )
        first_news = driver.find_element(By.CSS_SELECTOR, ".news-card a")
        first_news.click()

        # Проверяем лайк (кнопка .reaction-btn внутри .reaction-buttons)
        self._click_like_and_assert_irreversible(
            driver,
            btn_selector=".reaction-buttons .reaction-btn[data-reaction='like']",
            count_selector=".reaction-buttons .reaction-btn .count",
        )

        # Сохраняем текущее число просмотров, обновляем страницу, убеждаемся +1
        views_el = driver.find_element(By.CSS_SELECTOR, ".hero-stats .views-indicator span")
        views_before = int(views_el.text.strip())
        driver.refresh()
        time.sleep(1)
        views_after = int(
            driver.find_element(By.CSS_SELECTOR, ".hero-stats .views-indicator span").text.strip()
        )
        assert views_after == views_before + 1, "Просмотры не увеличились после обновления страницы"

        # Комментарий + ответ
        comment_box = driver.find_element(By.CSS_SELECTOR, "#comment-form textarea")
        unique_comment = f"NewsComment {int(time.time())}"
        comment_box.send_keys(unique_comment)
        driver.find_element(By.CSS_SELECTOR, "#comment-form button[type='submit']").click()
        time.sleep(1)
        assert unique_comment in driver.page_source, "Комментарий к новости не появился"

        # Оставляем ответ на только что созданный комментарий (ищем последнюю кнопку Reply)
        reply_buttons = driver.find_elements(By.CSS_SELECTOR, ".comment-reply-btn")
        if reply_buttons:
            reply_buttons[-1].click()
            reply_box = driver.find_element(By.CSS_SELECTOR, ".reply-form textarea")
            unique_reply = f"Reply {int(time.time())}"
            reply_box.send_keys(unique_reply)
            driver.find_element(By.CSS_SELECTOR, ".reply-form button[type='submit']").click()
            time.sleep(1)
            assert unique_reply in driver.page_source, "Ответ на комментарий не появился"

        # Проверяем счётчик комментариев
        comment_counter_el = driver.find_element(By.CSS_SELECTOR, ".hero-stat-value")
        expected_comments = int(comment_counter_el.text.strip())

        # Проверка карточки
        self._verify_card_counter_updated(
            driver,
            f"{base_url}/news/",
            card_selector=".news-card:first-child .stat-item.comments span",
            stat_selector=".news-card:first-child .stat-item.comments span",
            expected_value=expected_comments,
        )

    def test_growlog_like_comment_counters(self, driver, base_url):
        wait = WebDriverWait(driver, 20)
        # Переходим к списку гроурепортов
        driver.get(f"{base_url}/growlogs/")
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".unified-card a")))
        first_gl = driver.find_element(By.CSS_SELECTOR, ".unified-card a")
        first_gl.click()

        # Лайк кнопка
        like_btn_sel = ".btn-like.like-btn"
        like_count_sel = ".btn-like.like-btn .like-count"
        self._click_like_and_assert_irreversible(driver, like_btn_sel, like_count_sel)

        # Добавляем комментарий и ответ
        inc = self._add_comment_and_reply(driver, "GrowLogComm")

        # Проверяем карточку
        likes_final = int(driver.find_element(By.CSS_SELECTOR, like_count_sel).text.strip())
        self._verify_card_counter_updated(
            driver,
            f"{base_url}/growlogs/",
            card_selector=".unified-card:first-child .stat-item.likes span",
            stat_selector=".unified-card:first-child .stat-item.likes span",
            expected_value=likes_final,
        )


# === Фикстуры переиспользуемые из test_full_site ===

@pytest.fixture(scope="session")
def driver(global_driver_fixture):
    """Переиспользуем глобальный webdriver из test_full_site, чтобы не создавать новый."""
    return global_driver_fixture

@pytest.fixture(scope="session")
def base_url(live_server):
    """Возвращает базовый URL live_server (тот же, что в test_full_site)."""
    return live_server.url.rstrip("/")
