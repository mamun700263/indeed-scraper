import os
import csv
import json
import time
import random
import sqlite3
import requests
import pandas as pd

from urllib.parse import urljoin

from typing import Dict, List, Optional

from bs4 import BeautifulSoup, FeatureNotFound

from selenium.common.exceptions import WebDriverException, TimeoutException

from requests.exceptions import RequestException, Timeout, ConnectionError

from logger import get_logger
logger = get_logger('utils.common')



def soup_maker(response: str) -> Optional[BeautifulSoup]:
    """
    Converts a response to a BeautifulSoup object for parsing  HTML
    with lxml.
    """
    try:
        soup = BeautifulSoup(response, "lxml")
        logger.info("✅ Soup created successfully")
        return soup
    except (FeatureNotFound or TypeError) as e:
        logger.error(f"❌ Failed to create soup: {e}")
        return None


def sleeper(minimum: float = 3, maximum: float = 8) -> None:
    """
    To mimic human behaviour
    Sleeps for a random time between minimum and maximum.
    """
    if minimum > maximum:
        minimum, maximum = maximum, minimum

    x = random.uniform(minimum, maximum)
    logger.debug(f"⏱️ Sleeping for {x:.2f} seconds...")
    time.sleep(x)


def driver_execute(driver) -> None:
    driver.execute_script("return document.body.scrollHeight")


def get_scroll_height(driver) -> int:
    """
    Returns the current scroll height of the page.
    """
    return driver.execute_script("return document.body.scrollHeight")


def scroll_and_wait(
    driver,
    wait_time: int = 2,
    scroll_pause: float = 0.5,
    max_scrolls: int = 10,
) -> None:
    """
    Simulates scrolling to the bottom of a dynamically loading page.
    Stops if no new content is loaded.
    """
    last_height = get_scroll_height(driver)

    for i in range(max_scrolls):
        driver.execute_script(
            "window.scrollTo(0, document.body.scrollHeight);"
        )
        time.sleep(scroll_pause)

        new_height = get_scroll_height(driver)
        logger.debug(f"🔁 Scroll {i+1}: height changed to {new_height}")

        if new_height == last_height:
            logger.info("📉 No new content loaded — stopping scroll")
            break

        last_height = new_height

    logger.info(f"✅ Scrolling completed with {i+1} scroll(s)")
    time.sleep(wait_time)


def loader(driver, url: str):
    """Sets timeout, loads URL, and scrolls to trigger lazy-loaded content."""
    driver.set_page_load_timeout(15)
    driver.get(url)
    sleeper()
    scroll_and_wait(driver)


def load_and_scroll(driver, url: str) -> None:
    """
    Loads a page and performs scrolling to ensure content is fully loaded.
    """
    try:
        logger.info(f"🌐 Navigating to: {url}")
        loader(driver, url)
        logger.info(f"✅ Successfully loaded and scrolled: {url}")
    except (TimeoutException, WebDriverException) as e:
        logger.error(f"❌ Failed to load {url}: {e}")


def pagination(soup: BeautifulSoup, base_url: str) -> Optional[str]:
    logger.debug("📄 Checking for pagination...")
    try:
        next_page = soup.find("a", class_="s-pagination-next")
        if not next_page or not next_page.get("href"):
            logger.warning("⚠️ No next page link found")
            return None
        next_url = urljoin(base_url, next_page["href"])
        logger.info(f"➡️ Found next page URL: {next_url}")
        return next_url
    except (AttributeError, TypeError) as e:
        logger.error(f"❌ Pagination error: {e}")
        return None


VALID_EXTENSIONS = {
    ".csv": "csv",
    ".json": "json",
    ".xlsx": "xlsx",
    ".sqlite": "sqlite"
}


def file_format_checker(file_name: str) -> str:
    """
    Checks the file format based on the file extension.
    """
    file_name = file_name.lower()

    for ext, format_type in VALID_EXTENSIONS.items():
        if file_name.endswith(ext):
            return format_type

    raise ValueError(
        f"Invalid file format. Supported formats:"
        f" {', '.join(VALID_EXTENSIONS.values())}."
    )


def save_to_sqlite(
    items: List[Dict[str, str]], db_name: str, table_name: str = "products"
) -> None:
    """
    Saves data to an SQLite database.
    """
    if not items:
        logger.warning("⚠️ No data to save to SQLite.")
        return

    try:
        # Use with statement to ensure the connection is closed properly
        with sqlite3.connect(db_name) as conn:
            cursor = conn.cursor()

            # Dynamically create table columns based on the data keys
            columns = ", ".join([f"{key} TEXT" for key in items[0].keys()])
            cursor.execute(f"CREATE TABLE IF NOT EXISTS "
                           f"{table_name} ({columns})")

            # Insert data into the table
            for item in items:
                placeholders = ", ".join(["?"] * len(item))
                values = tuple(item.values())
                cursor.execute(f"INSERT INTO {table_name} "
                               f"VALUES ({placeholders})", values)

            conn.commit()  # Commit the changes
            logger.info(f"✅ Data saved to SQLite: {db_name} → {table_name}")

    except sqlite3.DatabaseError as e:
        logger.error(f"❌ SQLite database error: {e}")
    except Exception as e:
        logger.error(f"❌ Failed to save to SQLite: {e}")


def save_as(
    items: List[Dict[str, str]],
    file_name: Optional[str] = None,
    post_api_url: Optional[str] = None,
    table_name: str = "products",
) -> None:
    """
    Saves data to the specified format
    (CSV, JSON, Excel, SQLite) or POSTs it to an API.
    """
    if not items:
        logger.warning("⚠️ No items to save.")
        return

    # POST the data to the API if we have the URL
    if post_api_url:
        post_data_to_api(post_api_url, items)
        return  # Stop here if only posting to the API (do not save to file)

    # Save to file if no post_api_url was provided
    if file_name:
        save_data_to_file(file_name, items, table_name)
    else:
        logger.warning("⚠️ No file name provided and no API endpoint.")


def post_data_to_api(post_api_url: str, items: List[Dict[str, str]]) -> None:
    """Handles the logic for posting data to an API."""
    try:
        if post_with_retry(post_api_url, items):
            logger.info(f"✅ Successfully posted data to API: {post_api_url}")
        else:
            logger.error(f"❌ Failed to post data to API: {post_api_url}")
    except Exception as e:
        logger.error(f"❌ Exception while POSTing to API: {e}")


def save_data_to_file(
        file_name: str,
        items: List[Dict[str, str]],
        table_name: str) -> None:
    """Handles the logic for saving data to a file."""
    try:
        file_ext = os.path.splitext(file_name)[1][1:].lower()

        if file_ext == "csv":
            save_to_csv(file_name, items)
        elif file_ext == "json":
            save_to_json(file_name, items)
        elif file_ext in ["xlsx", "xls"]:
            save_to_excel(file_name, items)
        elif file_ext == "sqlite":
            save_to_sqlite(items, file_name, table_name)
        else:
            logger.error(f"❌ Unsupported file format: {file_ext}")
    except Exception as e:
        logger.error(f"❌ Failed to save data: {e}")


def save_to_csv(file_name: str, items: List[Dict[str, str]]) -> None:
    """Saves data to a CSV file."""
    try:
        with open(file_name, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=items[0].keys())
            writer.writeheader()
            writer.writerows(items)
        logger.info(f"✅ Data saved as CSV: {file_name}")
    except Exception as e:
        logger.error(f"❌ Failed to save CSV: {e}")


def save_to_json(file_name: str, items: List[Dict[str, str]]) -> None:
    """Saves data to a JSON file."""
    try:
        with open(file_name, "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=4)
        logger.info(f"✅ Data saved as JSON: {file_name}")
    except Exception as e:
        logger.error(f"❌ Failed to save JSON: {e}")


def save_to_excel(file_name: str, items: List[Dict[str, str]]) -> None:
    """Saves data to an Excel file."""
    try:
        df = pd.DataFrame(items)
        df.to_excel(file_name, index=False)
        logger.info(f"✅ Data saved as Excel: {file_name}")
    except Exception as e:
        logger.error(f"❌ Failed to save Excel: {e}")


def post_with_retry(
    url: str,
    data: List[Dict[str, str]],
    max_retries: int = 3,
    delay: int = 2,
    timeout: int = 10,
    backoff: bool = False
) -> bool:
    """
    Attempts to POST data to the given URL with retry logic.
    Returns True if successful, False otherwise.
    """
    for attempt in range(1, max_retries + 1):
        try:
            # Making the POST request
            res = requests.post(url, json=data, timeout=timeout)

            # Checking if the response is successful
            if res.status_code in [200, 201]:
                logger.info(
                    f"✅ Data successfully POSTed to API on attempt {attempt}"
                )
                return True
            else:
                logger.warning(
                    f"⚠️ Attempt {attempt}: API POST failed "
                    f"({res.status_code}) - {res.text}"
                )

        except Timeout as e:
            logger.warning(f"⚠️ Attempt {attempt}: "
                           f"Timeout error during POST - {e}")
        except ConnectionError as e:
            logger.warning(f"⚠️ Attempt {attempt}: "
                           f"Connection error during POST - {e}")
        except RequestException as e:
            logger.warning(f"⚠️ Attempt {attempt}: "
                           f"RequestException during POST - {e}")

        # Wait before retrying, with optional exponential backoff
        if backoff:
            delay = delay * 2  # Exponential backoff
        time.sleep(delay)

    logger.error("❌ All retry attempts for API POST failed.")
    return False
