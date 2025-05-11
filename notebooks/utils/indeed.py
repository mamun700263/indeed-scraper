import time, random
from logger import get_logger
logger = get_logger('utils.amazon')
from utils.selenium_utils import ScraperConfig
from utils.common import load_and_scroll, soup_maker, pagination

from typing import List, Optional, Union, Dict
from urllib.parse import quote_plus

from bs4 import BeautifulSoup, Tag

class ProductExtractor:
    def __init__(self, soup: BeautifulSoup, base_url: str):
        self.soup = soup
        self.base_url = base_url

    def list_items(self) -> List[Tag]:
        """Locate all product list items from the soup."""
        try:
            items = self.soup.select('div[role="listitem"]') or []
            logger.info(f"✅ Found {len(items)} product items")
            return items
        except Exception as e:
            logger.error(f"❌ Error locating list items: {e}")
            return []


    @staticmethod
    def extract_text(item: Tag, selector: str, attr: str = None) -> str:
        """Extract text or attribute value from an HTML element."""
        try:
            element = item.find(selector) or ""
            return element.get(attr) if attr else element.text.strip()
        except Exception as e:
            logger.warning(f"⚠️ Extraction failed for selector '{selector}': {e}")
            return ""


    def extract_field(self, item: Tag, field_type: str) -> str:
        """Extract specific field (title, image, link) from product item."""
        field_selectors = {
            'title': "h2",
            'image': "img",
            'link': "a"
        }

        attrs = {
            'image': "src",
            'link': "href",
        }

        selector = field_selectors.get(field_type)
        attr = attrs.get(field_type)  # Will be None for title

        if not selector:
            logger.warning(f"⚠️ Unknown field type: {field_type}")
            return ""

        extracted = self.extract_text(item, selector, attr)

        if field_type == 'link' and extracted:
            return f"{self.base_url}{extracted}"
        return extracted

    def extract(self) -> List[Dict[str, str]]:
        """Main extraction logic."""
        if not self.soup:
            logger.error("❌ No soup provided to extractor")
            return []

        items = self.list_items()
        results = []

        for item in items:
            title = self.extract_field(item, 'title')
            if not title:
                continue  # Skip items with no title

            product = {
                "Title": title,
                "Image": self.extract_field(item, 'image'),
                "Link": self.extract_field(item, 'link'),
            }
            logger.debug(f"📝 Product extracted: {title}")
            results.append(product)

        logger.info(f"✅ Extracted {len(results)} products successfully")
        return results


class AmazonScraper:
    def __init__(self, config: ScraperConfig):
        self.config = config
        self.driver = config.driver
        self.url = "https://www.amazon.com"
        logger.info("🚀 AmazonScraper initialized")

    def get_search_url(self, keyword: str) -> str:
        encoded = quote_plus(keyword)
        search_url = f"{self.url}/s?k={encoded}"
        logger.debug(f"🔗 Generated search URL: {search_url}")
        return search_url

    def scrape_search_results(self, keyword: str, wait_time: int=3) -> str:
        url = self.get_search_url(keyword)
        logger.info(f"🌐 Navigating to search page: {url}")
        try:
            load_and_scroll(self.driver,url)
            logger.info("✅ Page loaded and ready for scraping")
            return self.driver.page_source
        except Exception as e:
            logger.error(f"❌ Error loading page for keyword '{keyword}': {e}")
            return ""

    def scrape_all_pages(self, keyword: str, max_pages=5)-> List[Dict[str, str]]:
        results = []
        response = self.scrape_search_results(keyword)
        soup = soup_maker(response)
        page = 0
        amazon_extractor = ProductExtractor(soup,self.url)

        while soup and page < max_pages: #apply retry here
            data = amazon_extractor.extract()
            results += data

            logger.info(f"📄 Page {page + 1} scraped.")

            next_page_url = pagination(soup,self.url)
            # next_page_url = next_page_url[:-1]+(next_page_url[-1]+1)
            if not next_page_url:
                break

            self.driver.get(next_page_url)
            time.sleep(random.uniform(2, 4))  # can swap with sleeper()
            soup = soup_maker(self.driver.page_source)
            page += 1

        return results

    def quit(self):
        logger.info("🛑 Quitting WebDriver")
        self.driver.quit()