import random, os

import undetected_chromedriver as uc
from selenium.webdriver.chrome.options import Options as ChromeOptions

from typing import List, Optional, Union

from dotenv import load_dotenv
load_dotenv()

from seleniumwire import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from logger import get_logger
logger = get_logger('utils.selenium')

SCRAPEOPS_API_KEY: str =  os.getenv("SCRAPEOPS_API_KEY")

class ScraperConfig:
    """
    Scraper configuration manager for initializing Selenium WebDriver instances.

    This class supports various configurations such as:
    - Headless mode
    - Incognito mode
    - Proxy configuration (ScrapeOps)
    - SeleniumWire support
    - Random User-Agent rotation

    Attributes:
        SCRAPEOPS_API_KEY (str): API key for ScrapeOps service.
        use_uc (bool): Whether to use undetected_chromedriver (UC).
        headless (bool): Whether to enable headless mode for the WebDriver.
        incognito (bool): Whether to start the browser in incognito mode.
        user_agent (Optional[str]): Custom User-Agent string for the WebDriver.
        use_scrapeops (bool): Whether to use ScrapeOps proxy service.
        use_seleniumwire (bool): Whether to use SeleniumWire for intercepting requests.
        proxy (Optional[str]): Proxy URL for ScrapeOps (if applicable).
        user_agents (List[str]): List of User-Agent strings for random rotation.
        random_user_agent (str): A randomly selected or custom User-Agent string.
        driver (Union[webdriver.Chrome, "seleniumwire.webdriver.Chrome", uc.Chrome]):
            The initialized WebDriver instance.
    """

    SCRAPEOPS_API_KEY: str =  os.getenv("SCRAPEOPS_API_KEY")

    def __init__(
        self,
        use_uc: bool = False,
        headless: bool = False,
        incognito: bool = True,
        user_agent: Optional[str] = None,
        use_scrapeops: bool = False,
        use_seleniumwire: bool = False,
    ) -> None:
        """
        Initializes the ScraperConfig object with the given configuration parameters.

        Args:
            use_uc (bool): Whether to use undetected_chromedriver (UC).
            headless (bool): Whether to run the browser in headless mode.
            incognito (bool): Whether to run the browser in incognito mode.
            user_agent (Optional[str]): Custom User-Agent to use.
            use_scrapeops (bool): Whether to use ScrapeOps proxy service.
            use_seleniumwire (bool): Whether to use SeleniumWire.

        Initializes:
            Sets the attributes based on the passed configuration.
            Initializes the WebDriver according to the selected options.
        """
        self.use_uc = use_uc
        self.headless = headless
        self.incognito = incognito
        self.use_scrapeops = use_scrapeops
        self.use_seleniumwire = use_seleniumwire

        self.uc_options = uc.ChromeOptions()
        self.chrome_options = ChromeOptions()

        self.proxy = (
            f"http://scrapeops.headless_browser_mode=true:{self.SCRAPEOPS_API_KEY}@proxy.scrapeops.io:5353"
            if self.use_scrapeops else None
        )


        self.user_agents: List[str] = self._load_user_agents()
        self.random_user_agent: str = (
            user_agent or
            random.choice(self.user_agents)
        )

        self.driver = self._init_driver()


    def _init_driver(
        self,
    ) -> Union[webdriver.Chrome, "seleniumwire.webdriver.Chrome", uc.Chrome]:
        """
        Initializes the appropriate driver based on the configuration.

        Returns:
            Union[webdriver.Chrome, seleniumwire.webdriver.Chrome, uc.Chrome]:
            The configured WebDriver instance.

        Notes:
            This function selects the appropriate driver based on whether
            undetected_chromedriver (UC) is enabled or a regular Chrome driver
            is to be used, with or without SeleniumWire.
        """
        if self.use_uc:
            logger.info("⚙️ Using undetected_chromedriver (UC)")
            return self._get_uc_driver()

        logger.info("⚙️ Using standard Chrome driver")
        return self._get_normal_driver()

    def _get_uc_driver(self) -> uc.Chrome:
        """
        Configures and returns an undetected_chromedriver (UC) instance.

        Returns:
            uc.Chrome: The configured undetected Chrome driver.

        Notes:
            This method configures the driver with additional stealth options
            to avoid detection as a bot, such as disabling automation features.
        """
        self._apply_common_options(self.uc_options)

        # Additional stealth options for UC
        self.uc_options.add_argument\
            ("--disable-blink-features=AutomationControlled")

        return uc.Chrome(options=self.uc_options)

    def _get_normal_driver(
        self,
    ) -> Union[webdriver.Chrome, "seleniumwire.webdriver.Chrome"]:
        """
        Configures and returns a standard Chrome WebDriver.

        Returns:
            Union[webdriver.Chrome, seleniumwire.webdriver.Chrome]:
            The configured normal Chrome driver.

        Notes:
            If SeleniumWire is enabled, this function configures the driver
            with SeleniumWire proxy options for intercepting requests.
        """
        self._apply_common_options(self.chrome_options)

        if self.use_seleniumwire:
            from seleniumwire import webdriver as wire_webdriver

            seleniumwire_options = (
                {
                    "proxy": {
                        "http": self.proxy,
                        "https": self.proxy,
                        "no_proxy": "localhost,127.0.0.1",
                    }
                }
                if self.proxy
                else {}
            )

            return wire_webdriver.Chrome(
                options=self.chrome_options,
                seleniumwire_options=seleniumwire_options
            )

        return webdriver.Chrome(
            service=ChromeService(ChromeDriverManager().install()),
            options=self.chrome_options,
        )

    def _apply_common_options(
        self, options: Union[ChromeOptions, uc.ChromeOptions]
    ) -> None:
       """
        Applies common options for Chrome based on the current configuration.

        Args:
            options (Union[ChromeOptions, uc.ChromeOptions]):
            The options object to configure.

        This function adds configurations for:
        - Headless mode
        - Incognito mode
        - Proxy settings (if any)
        - Other browser performance-related settings
        """
       if self.headless:
           options.add_argument("--headless=new")
       if self.incognito:
           options.add_argument("--incognito")
       if self.proxy:
           options.add_argument(f"--proxy-server={self.proxy}")
       options.add_argument("--no-sandbox")
       options.add_argument("--disable-dev-shm-usage")
       options.add_argument("--disable-popup-blocking")
       options.add_argument("--disable-infobars")
       options.add_argument("--start-maximized")
       options.add_argument("--window-size=1920,1080")
       options.add_argument(f"user-agent={self.random_user_agent}")


    def _load_user_agents(self) -> List[str]:
        """
        Loads a list of User-Agent strings.

        Returns:
            List[str]: List of user-agent strings.
        """
        return [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/537.36 (KHTML, like Gecko) Version/17.0 Mobile Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/122.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/120.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0",
            "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 13; Pixel 7 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 12; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
            "Mozilla/5.0 (Android 13; Mobile; rv:120.0) Gecko/120.0 Firefox/120.0",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/537.36 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/537.36",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/537.36 (KHTML, like Gecko) CriOS/120.0.0.0 Mobile/15E148 Safari/537.36",
            "Mozilla/5.0 (iPad; CPU OS 16_1 like Mac OS X) AppleWebKit/537.36 (KHTML, like Gecko) Version/16.1 Mobile/15E148 Safari/537.36"
        ]
