import os
import uuid
from datetime import datetime
from io import StringIO
from typing import Final, Callable, Any, TypeVar, Optional

import pandas as pd
import pytz
from chrome_driver import ChromeDriver
from icalendar import Calendar, Event
from pandas import DataFrame
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
from tabulate import tabulate

"""
Requires python packages:
- selenium
- webdriver-manager
- pandas
- icalendar
- tabulate
- lxml
- html5lib
- BeautifulSoup4

Requires Chrome being installed (On Alpine linux
or Home Assistant Appdaemon, this means:
`apk add chromium chromium-chromedriver`)
"""


def update_ical_file_from_satyr(
        url: str,
        username: str,
        password: str,
        ics_path: str,
        chrome_driver_path: Optional[str] = None,
) -> None:
    """
    Updates an iCalendar (.ics) file based on the timetable data obtained from the Satyr web portal. This function uses
    a web driver to automate the login process, retrieve the timetable data, and generate an updated iCalendar (.ics) file.
    This ensures synchronization of the timetable with the local .ics file for further use.

    :param url: The URL of the Satyr web portal. Like 'https://satyr.ugent.be/#/student'.
    :type url: str
    :param username: The username required to log in to the Satyr web portal.
    :type username: str
    :param password: The password required to log in to the Satyr web portal.
    :type password: str
    :param ics_path: The file path where the updated iCalendar (.ics) file should be saved.
                     Like '/config/www/satyr.ics'.
    :type ics_path: str
    :param chrome_driver_path: The file path where the Chrome driver executable is located.
                                Will install Chrome if not supplied.
    :type chrome_driver_path: Optional[str]
    :return: None
    """

    print(f"Fetching data for {username}.")

    def read_time_table_with_driver(driver: WebDriver):
        _read_time_table(
            driver=driver,
            callback=make_ical,
        )

    def make_ical(df: DataFrame):
        print(tabulate(df, headers="keys", tablefmt="psql"))

        calendar: Final[Calendar] = _create_calendar(df)
        ical: bytes = calendar.to_ical()

        with open(ics_path, "wb") as file:
            file.write(ical)
            print(f"Wrote file to {ics_path}.")

    d: WebDriver
    with ChromeDriver(executable_path=chrome_driver_path) as d:
        _visit_url_and_login(
            driver=d,
            url=url,
            username=username,
            password=password,
            callback=read_time_table_with_driver,
        )


def _visit_url_and_login(
        driver: WebDriver,
        url: str,
        username: str,
        password: str,
        callback: Callable[[WebDriver], None],
):
    driver.get(url)
    try:
        form: Final[WebElement] = WebDriverWait(driver, 30).until(
            expected_conditions.visibility_of_element_located(
                (By.CSS_SELECTOR, "form")
            )
        )
    finally:
        username_elem: Final[WebElement] = form.find_element(By.CSS_SELECTOR, "[name='username']")
        username_elem.send_keys(username)

        password_elem: Final[WebElement] = form.find_element(By.CSS_SELECTOR, "[name='password']")
        password_elem.send_keys(password)
        password_elem.send_keys(Keys.ENTER)

        print(f"Connected to Satyr and logged in.")

        callback(driver)


def _read_time_table(driver: WebDriver, callback: Callable[[DataFrame], None]):
    try:
        print("Waiting for time table to load...")
        element: Final[WebElement] = WebDriverWait(driver, 30).until(
            expected_conditions.visibility_of_element_located(
                (By.CSS_SELECTOR, "[role='table']")
            )
        )
    finally:
        df: DataFrame = pd.read_html(
            io=StringIO(element.get_attribute("outerHTML")),
        )[0]
        df = df.drop(0, axis=1)

        # date column
        df[1] = df[1].apply(
            lambda x: pd.to_datetime(str(x)[4:], dayfirst=True).date(),
        )
        df = df.rename(columns={1: "date"})

        # split other columns
        df[["times", "full_name"]] = df[2].str.split(" : ", expand=True)
        df = df.drop(2, axis=1)

        # create start- and end time
        df[["start_time", "end_time"]] = df["times"].str.split(" - ", expand=True)
        df["start_time"] = df["start_time"].apply(lambda x: pd.to_datetime(str(x)).time())
        df["end_time"] = df["end_time"].apply(lambda x: pd.to_datetime(str(x)).time())
        df = df.drop("times", axis=1)

        # name and code
        df[["code", "name"]] = df["full_name"].str \
            .replace("(8-12)", "").str \
            .strip().str \
            .split(" - ", n=1, expand=True)
        df = df.drop("full_name", axis=1)

        callback(df)


def _create_calendar(df: DataFrame) -> Calendar:
    cal: Final[Calendar] = Calendar()
    cal.add("prodid", "-//Satyr//satyr.ugent.be//")
    cal.add("version", "2.0")

    for row in df.itertuples():
        event: Event = Event()
        event.add(
            name="dtstart",
            value=datetime.combine(
                date=row.date,
                time=row.start_time,
                tzinfo=pytz.timezone("Europe/Brussels"),
            ),
        )
        event.add(
            name="dtend",
            value=datetime.combine(
                date=row.date,
                time=row.end_time,
                tzinfo=pytz.timezone("Europe/Brussels"),
            ),
        )
        event.add(name="summary", value=row.name)
        event.add(name="description", value=f"{row.name} ({row.code})")
        event.add(name="uuid", value=str(uuid.uuid4()))
        cal.add_component(event)

    return cal
