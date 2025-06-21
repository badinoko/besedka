import time
import unittest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

BASE_URL = "http://127.0.0.1:8001"
LOGIN = "Buddy"
PASSWORD = "testpassword"  # Заменить на актуальный пароль тестового пользователя

class CommentsE2ETest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        cls.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        cls.driver.implicitly_wait(5)

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

    def login(self):
        self.driver.get(f"{BASE_URL}/accounts/login/")
        username_input = self.driver.find_element(By.NAME, "login")
        password_input = self.driver.find_element(By.NAME, "password")
        username_input.send_keys(LOGIN)
        password_input.send_keys(PASSWORD)
        password_input.send_keys(Keys.RETURN)
        time.sleep(2)
        assert "Выйти" in self.driver.page_source or "Logout" in self.driver.page_source

    def check_comments_section(self, detail_url, comment_text):
        self.driver.get(detail_url)
        self.login()
        self.driver.get(detail_url)
        time.sleep(1)
        # Найти форму комментария
        textarea = self.driver.find_element(By.TAG_NAME, "textarea")
        textarea.clear()
        textarea.send_keys(comment_text)
        submit_btn = self.driver.find_element(By.XPATH, "//button[contains(@class, 'btn-primary') and contains(text(), 'Отправить')]")
        submit_btn.click()
        time.sleep(2)
        # Проверить, что комментарий появился первым
        comments = self.driver.find_elements(By.CSS_SELECTOR, ".comment")
        self.assertTrue(any(comment_text in c.text for c in comments[:2]))
        # Проверить, что кнопка "Ответить" есть у первого комментария
        reply_btns = comments[0].find_elements(By.XPATH, ".//button[contains(text(), 'Ответить')] | .//a[contains(text(), 'Ответить')]")
        self.assertTrue(len(reply_btns) > 0, "Кнопка 'Ответить' отсутствует после AJAX")
        # Проверить вложенность (ответ на комментарий)
        reply_btns[0].click()
        time.sleep(1)
        reply_text = comment_text + " (ответ)"
        textarea = self.driver.find_element(By.TAG_NAME, "textarea")
        textarea.clear()
        textarea.send_keys(reply_text)
        submit_btn = self.driver.find_element(By.XPATH, "//button[contains(@class, 'btn-primary') and contains(text(), 'Отправить')]")
        submit_btn.click()
        time.sleep(2)
        # Проверить, что ответ появился под родительским комментарием
        comments = self.driver.find_elements(By.CSS_SELECTOR, ".comment")
        self.assertTrue(any(reply_text in c.text for c in comments))
        # Проверить, что кнопка "Ответить" не исчезла
        reply_btns = comments[0].find_elements(By.XPATH, ".//button[contains(text(), 'Ответить')] | .//a[contains(text(), 'Ответить')]")
        self.assertTrue(len(reply_btns) > 0, "Кнопка 'Ответить' исчезла после ответа")

    def test_news_comments(self):
        self.check_comments_section(f"{BASE_URL}/news/post/6803/", "Selenium тест: новость")

    def test_gallery_comments(self):
        self.check_comments_section(f"{BASE_URL}/gallery/photo/1/", "Selenium тест: галерея")

    def test_growlog_comments(self):
        self.check_comments_section(f"{BASE_URL}/growlogs/1/", "Selenium тест: гроурепорт")

if __name__ == "__main__":
    unittest.main()
