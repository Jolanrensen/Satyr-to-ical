from typing import Optional

from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.webdriver import WebDriver
from webdriver_manager.chrome import ChromeDriverManager


class ChromeDriver(object):
    executable_path: str
    driver: Chrome

    def __init__(self, executable_path: Optional[str] = None):
        if executable_path is None:
            executable_path = ChromeDriverManager().install()
        self.executable_path = executable_path

    def __enter__(self) -> WebDriver:
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        self.driver = Chrome(
            service=Service(self.executable_path),
            options=options,
        )
        return self.driver

    def __exit__(self, *args):
        self.driver.quit()
