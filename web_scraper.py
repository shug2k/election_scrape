from bs4 import BeautifulSoup
from os.path import exists
from typing import Optional, Dict, Any, List
import requests
import re
import json
import time
import logging
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from logger_config import setup_logger, ScrapingStats

OUT_FOLDER = 'scraped_sites'


class ScrapingError(Exception):
    """Custom exception for scraping-related errors."""
    pass


class NetworkError(ScrapingError):
    """Exception for network-related errors."""
    pass


class ContentError(ScrapingError):
    """Exception for content parsing errors."""
    pass


class LineProcessor:
    def __init__(self, max_retries: int = 3, delay_between_requests: float = 1.0):
        self.entries = {}
        self.logger = setup_logger(__name__)
        self.stats = ScrapingStats()
        self.max_retries = max_retries
        self.delay_between_requests = delay_between_requests
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """Create a requests session with retry strategy."""
        session = requests.Session()

        # Define retry strategy
        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        # Set a reasonable timeout and user agent
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Election Scraper Bot 1.0; Educational Use)'
        })

        return session

    def parse_site(self, url: str) -> Dict[str, Any]:
        """
        Parse a website and extract content with robust error handling.

        Args:
            url: The URL to scrape

        Returns:
            Dictionary containing scraped data

        Raises:
            NetworkError: For network-related issues
            ContentError: For content parsing issues
        """
        if not url or not url.strip():
            raise ContentError("Empty or invalid URL provided")

        url = url.strip()
        if not (url.startswith('http://') or url.startswith('https://')):
            raise ContentError(f"Invalid URL format: {url}")

        self.logger.info(f"Scraping URL: {url}")
        self.stats.record_attempt()

        try:
            # Add delay to be respectful to servers
            time.sleep(self.delay_between_requests)

            # Make request with timeout
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            # Check content type
            content_type = response.headers.get('content-type', '').lower()
            if 'text/html' not in content_type:
                raise ContentError(f"Non-HTML content type: {content_type}")

            # Check if we got actual content
            if len(response.content) < 100:
                raise ContentError("Response too short, likely not a valid page")

            soup = BeautifulSoup(response.content, 'html.parser')

            # Validate that we got parseable HTML
            if not soup.find('body') and not soup.find('html'):
                raise ContentError("Invalid HTML structure")

            data = self._extract_content(soup, url)
            self._validate_extracted_data(data)

            self.stats.record_success()
            self.logger.debug(f"Successfully scraped {url}")

            return data

        except requests.exceptions.Timeout:
            error_msg = f"Timeout while accessing {url}"
            self.logger.error(error_msg)
            self.stats.record_failure(url, error_msg)
            raise NetworkError(error_msg)

        except requests.exceptions.ConnectionError as e:
            error_msg = f"Connection error for {url}: {str(e)}"
            self.logger.error(error_msg)
            self.stats.record_failure(url, error_msg)
            raise NetworkError(error_msg)

        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP error for {url}: {response.status_code} - {str(e)}"
            self.logger.error(error_msg)
            self.stats.record_failure(url, error_msg)
            raise NetworkError(error_msg)

        except requests.exceptions.RequestException as e:
            error_msg = f"Request error for {url}: {str(e)}"
            self.logger.error(error_msg)
            self.stats.record_failure(url, error_msg)
            raise NetworkError(error_msg)

        except Exception as e:
            error_msg = f"Unexpected error parsing {url}: {str(e)}"
            self.logger.error(error_msg)
            self.stats.record_failure(url, error_msg)
            raise ContentError(error_msg)

    def _extract_content(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Extract content from parsed HTML."""
        data = {'url': url}

        try:
            # Extract titles
            html_titles = soup.find_all(['h1', 'h2', 'title'])
            titles = []
            for item in html_titles:
                if item.text and item.text.strip():
                    titles.append(item.text.strip())
            data['title'] = '\n'.join(titles[:3])  # Limit to first 3 titles

            # Extract links
            html_links = soup.find_all('a', href=True)
            if html_links:
                links = set()
                for item in html_links:
                    href = item.get('href')
                    if href and ('http' in href or href.startswith('/')):
                        links.add(href)
                data['links'] = list(links)[:50]  # Limit to 50 links
            else:
                data['links'] = []

            # Extract main text content
            paragraphs = soup.find_all(['p', 'div', 'article'])
            text_parts = []
            for item in paragraphs:
                if item.text and len(item.text.strip()) > 20:  # Only substantial text
                    text_parts.append(item.text.strip())

            data['text'] = ' '.join(text_parts)

            return data

        except Exception as e:
            raise ContentError(f"Error extracting content: {str(e)}")

    def _validate_extracted_data(self, data: Dict[str, Any]) -> None:
        """Validate that extracted data is reasonable."""
        if not data.get('text') or len(data['text']) < 50:
            raise ContentError("Insufficient text content extracted")

        if len(data['text']) > 1000000:  # 1MB text limit
            self.logger.warning("Very large text content, truncating")
            data['text'] = data['text'][:1000000]

    @staticmethod
    def get_metadata_from_line(in_data: dict[str, str]) -> dict[str, str]:
        return {
            'date': in_data['Publication Date'],
            'country': in_data['Country'],
            'platform': in_data['Tech Platform'],
            'type': in_data['Product Type'],
            'url': in_data['Link'],
        }

    def scrape_line(self, in_data: Dict[str, str]) -> Dict[str, Any]:
        """
        Scrape a single line/URL with error handling.

        Args:
            in_data: Input data containing URL and metadata

        Returns:
            Combined metadata and scraped data

        Raises:
            ScrapingError: For any scraping-related issues
        """
        try:
            out_data = self.get_metadata_from_line(in_data)
            site_data = self.parse_site(out_data['url'])

            # Merge scraped data with metadata
            for key, value in site_data.items():
                out_data[key] = value

            return out_data

        except (NetworkError, ContentError) as e:
            # Re-raise scraping errors
            raise e
        except Exception as e:
            raise ScrapingError(f"Unexpected error scraping line: {str(e)}")

    def process_line(self, in_data: Dict[str, str], manual_data: Dict[str, Dict[str, str]] = None,
                     scrape_data: bool = True) -> Optional[str]:
        """
        Process a single line of input data with comprehensive error handling.

        Args:
            in_data: Input data containing URL and metadata
            manual_data: Optional manual data override
            scrape_data: Whether to scrape data or just use manual data

        Returns:
            Path to output file if successful, None if failed
        """
        if manual_data is None:
            manual_data = {}

        try:
            # Validate input data
            required_fields = ['Tech Platform', 'Publication Date', 'Link']
            for field in required_fields:
                if field not in in_data or not in_data[field]:
                    raise ValueError(f"Missing required field: {field}")

            # Create safe filename
            platform = re.sub(r'[^\w\-_]', '_', in_data['Tech Platform'])
            date = re.sub(r'[^\w\-_]', '-', in_data['Publication Date'])
            filename_prefix = f"{platform}_{date}"

            if filename_prefix not in self.entries:
                self.entries[filename_prefix] = 0
            self.entries[filename_prefix] += 1

            filename = f"{filename_prefix}_{self.entries[filename_prefix]}.json"
            filename_with_path = f"{OUT_FOLDER}/{filename}"

            # Create output directory if it doesn't exist
            import os
            os.makedirs(OUT_FOLDER, exist_ok=True)

            # Check if file already exists and we're not overriding
            if exists(filename_with_path) and in_data['Link'] not in manual_data:
                self.logger.info(f"File already exists, skipping: {filename_with_path}")
                return filename_with_path

            out_data = None

            # Process manual data or scrape
            if in_data['Link'] in manual_data:
                self.logger.info(f"Using manual data for: {in_data['Link']}")
                out_data = self.get_metadata_from_line(in_data)
                out_data.update(manual_data[in_data['Link']])
            elif scrape_data:
                out_data = self.scrape_line(in_data)

            # Save data if we have it
            if out_data:
                try:
                    with open(filename_with_path, 'w', encoding='utf-8') as f:
                        json.dump(out_data, f, ensure_ascii=False, indent=4)

                    self.logger.info(f"Successfully saved: {filename_with_path}")
                    return filename_with_path

                except IOError as e:
                    self.logger.error(f"Failed to write file {filename_with_path}: {str(e)}")
                    return None
            else:
                self.logger.warning(f"No data to save for: {in_data['Link']}")
                return None

        except (NetworkError, ContentError) as e:
            self.logger.error(f"Scraping failed for {in_data.get('Link', 'unknown')}: {str(e)}")
            return None

        except ValueError as e:
            self.logger.error(f"Invalid input data: {str(e)}")
            return None

        except Exception as e:
            self.logger.error(f"Unexpected error processing {in_data.get('Link', 'unknown')}: {str(e)}")
            return None

    def process_line_with_manual_copy(self, in_data: Dict[str, str]) -> Optional[str]:
        """
        Process line with manual copy handling and improved error handling.

        Args:
            in_data: Input data containing URL and metadata

        Returns:
            Path to output file if successful, None if failed
        """
        try:
            # Create safe filename
            platform = re.sub(r'[^\w\-_]', '_', in_data['Tech Platform'])
            date = re.sub(r'[^\w\-_]', '-', in_data['Publication Date'])
            filename_prefix = f"{platform}_{date}"

            if filename_prefix not in self.entries:
                self.entries[filename_prefix] = 0
            self.entries[filename_prefix] += 1

            filename = f"{filename_prefix}_manual_{self.entries[filename_prefix]}.json"
            filename_with_path = f"{OUT_FOLDER}/{filename}"

            # Create output directory if it doesn't exist
            import os
            os.makedirs(OUT_FOLDER, exist_ok=True)

            if not exists(filename_with_path):
                out_data = self.scrape_line(in_data)
                with open(filename_with_path, 'w', encoding='utf-8') as f:
                    json.dump(out_data, f, ensure_ascii=False, indent=4)

                self.logger.info(f"Successfully saved manual copy: {filename_with_path}")
                return filename_with_path
            else:
                self.logger.info(f"Manual file already exists: {filename_with_path}")
                return filename_with_path

        except Exception as e:
            self.logger.error(f"Error processing manual copy for {in_data.get('Link', 'unknown')}: {str(e)}")
            return None

    def get_stats_summary(self) -> Dict[str, Any]:
        """Get summary of scraping statistics."""
        return self.stats.get_summary()

    def log_final_summary(self) -> None:
        """Log final scraping summary."""
        self.stats.log_summary(self.logger)
