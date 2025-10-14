"""
Logging configuration for the election scraper project.
"""
import logging
import os
from datetime import datetime
from typing import Optional


def setup_logger(name: str, log_level: str = "INFO", log_file: Optional[str] = None) -> logging.Logger:
    """
    Set up a logger with both console and file handlers.

    Args:
        name: Logger name (typically __name__)
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path. If None, creates timestamped log file.

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Avoid duplicate handlers if logger already configured
    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, log_level.upper()))

    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)

    # Create log file name if not provided
    if log_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = f"logs/election_scraper_{timestamp}.log"

    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    console_formatter = logging.Formatter(
        '%(levelname)s - %(name)s - %(message)s'
    )

    # File handler for detailed logs
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)

    # Console handler for important messages
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)

    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


class ScrapingStats:
    """Track scraping statistics and errors."""

    def __init__(self):
        self.total_attempts = 0
        self.successful_scrapes = 0
        self.failed_scrapes = 0
        self.errors = []

    def record_attempt(self):
        self.total_attempts += 1

    def record_success(self):
        self.successful_scrapes += 1

    def record_failure(self, url: str, error: str):
        self.failed_scrapes += 1
        self.errors.append({"url": url, "error": error})

    def get_summary(self) -> dict:
        return {
            "total_attempts": self.total_attempts,
            "successful_scrapes": self.successful_scrapes,
            "failed_scrapes": self.failed_scrapes,
            "success_rate": self.successful_scrapes / max(self.total_attempts, 1) * 100,
            "error_count": len(self.errors)
        }

    def log_summary(self, logger: logging.Logger):
        summary = self.get_summary()
        logger.info(f"Scraping Summary: {summary['successful_scrapes']}/{summary['total_attempts']} successful "
                   f"({summary['success_rate']:.1f}% success rate)")

        if self.errors:
            logger.warning(f"Failed to scrape {len(self.errors)} URLs")
            for error in self.errors[-5:]:  # Log last 5 errors
                logger.warning(f"Failed URL: {error['url']} - {error['error']}")