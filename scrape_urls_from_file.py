"""
URL scraping script with improved error handling and logging.
"""
import csv
import sys
import os
from typing import Optional, List, Dict
from logger_config import setup_logger
from web_scraper import LineProcessor, ScrapingError


class CSVProcessor:
    """CSV processing class with comprehensive error handling."""

    def __init__(self, csv_file: str = 'sources/election_history_db.csv'):
        self.csv_file = csv_file
        self.logger = setup_logger(__name__)
        self.line_processor = LineProcessor()
        self.total_rows = 0
        self.processed_rows = 0
        self.error_rows = 0
        self.skipped_rows = 0

    def process_csv_file(self) -> bool:
        """
        Process the CSV file and scrape URLs.

        Returns:
            True if processing completed successfully, False otherwise
        """
        try:
            # Validate CSV file exists
            if not os.path.exists(self.csv_file):
                self.logger.error(f"CSV file not found: {self.csv_file}")
                return False

            self.logger.info(f"Starting to process CSV file: {self.csv_file}")

            # Read and validate CSV structure
            rows = self._read_and_validate_csv()
            if not rows:
                return False

            self.total_rows = len(rows)
            self.logger.info(f"Found {self.total_rows} rows to process")

            # Process each row
            for row_num, row in enumerate(rows, 1):
                try:
                    self._process_single_row(row, row_num)
                except Exception as e:
                    self.logger.error(f"Failed to process row {row_num}: {str(e)}")
                    self.error_rows += 1

            self._log_final_summary()
            return True

        except Exception as e:
            self.logger.error(f"Critical error processing CSV file: {str(e)}")
            return False

    def _read_and_validate_csv(self) -> Optional[List[Dict[str, str]]]:
        """Read and validate CSV file structure."""
        try:
            rows = []
            required_fields = ['Tech Platform', 'Publication Date', 'Link']

            with open(self.csv_file, 'r', newline='', encoding='utf-8') as csvfile:
                # Try to detect CSV structure
                sample = csvfile.read(1024)
                csvfile.seek(0)

                # Check if file is empty
                if not sample.strip():
                    self.logger.error("CSV file is empty")
                    return None

                reader = csv.DictReader(csvfile)

                # Validate required columns exist
                if not reader.fieldnames:
                    self.logger.error("CSV file has no headers")
                    return None

                missing_fields = [field for field in required_fields if field not in reader.fieldnames]
                if missing_fields:
                    self.logger.error(f"CSV file missing required columns: {missing_fields}")
                    self.logger.info(f"Available columns: {list(reader.fieldnames)}")
                    return None

                # Read all rows
                for row_num, row in enumerate(reader, 1):
                    if self._validate_row(row, row_num):
                        rows.append(row)
                    else:
                        self.skipped_rows += 1

            if not rows:
                self.logger.error("No valid rows found in CSV file")
                return None

            self.logger.info(f"Successfully read {len(rows)} valid rows from CSV")
            return rows

        except FileNotFoundError:
            self.logger.error(f"CSV file not found: {self.csv_file}")
            return None
        except csv.Error as e:
            self.logger.error(f"CSV parsing error: {str(e)}")
            return None
        except Exception as e:
            self.logger.error(f"Error reading CSV file: {str(e)}")
            return None

    def _validate_row(self, row: Dict[str, str], row_num: int) -> bool:
        """Validate a single CSV row."""
        try:
            # Check for required fields
            if not row.get('Link') or not row.get('Link').strip():
                self.logger.warning(f"Row {row_num}: Missing or empty URL")
                return False

            if not row.get('Tech Platform') or not row.get('Tech Platform').strip():
                self.logger.warning(f"Row {row_num}: Missing or empty Tech Platform")
                return False

            if not row.get('Publication Date') or not row.get('Publication Date').strip():
                self.logger.warning(f"Row {row_num}: Missing or empty Publication Date")
                return False

            # Basic URL validation
            url = row['Link'].strip()
            if not (url.startswith('http://') or url.startswith('https://')):
                self.logger.warning(f"Row {row_num}: Invalid URL format: {url}")
                return False

            return True

        except Exception as e:
            self.logger.error(f"Error validating row {row_num}: {str(e)}")
            return False

    def _process_single_row(self, row: Dict[str, str], row_num: int) -> None:
        """Process a single CSV row."""
        try:
            self.logger.debug(f"Processing row {row_num}: {row.get('Link', 'unknown')}")

            # Process the line using LineProcessor
            result = self.line_processor.process_line(row)

            if result:
                self.processed_rows += 1
                self.logger.debug(f"Successfully processed row {row_num}")
            else:
                self.logger.warning(f"Failed to process row {row_num} - no output file created")
                self.error_rows += 1

        except ScrapingError as e:
            self.logger.error(f"Scraping error for row {row_num}: {str(e)}")
            self.error_rows += 1
        except Exception as e:
            self.logger.error(f"Unexpected error processing row {row_num}: {str(e)}")
            self.error_rows += 1

    def _log_final_summary(self) -> None:
        """Log final processing summary."""
        self.logger.info(f"CSV processing complete:")
        self.logger.info(f"  Total rows: {self.total_rows}")
        self.logger.info(f"  Successfully processed: {self.processed_rows}")
        self.logger.info(f"  Errors: {self.error_rows}")
        self.logger.info(f"  Skipped (invalid): {self.skipped_rows}")

        success_rate = (self.processed_rows / max(self.total_rows, 1)) * 100
        self.logger.info(f"  Success rate: {success_rate:.1f}%")

        # Log scraping statistics
        self.line_processor.log_final_summary()

        if self.error_rows > 0:
            self.logger.warning(f"Processing completed with {self.error_rows} errors")


def main():
    """Main function to run CSV processing."""
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
    else:
        csv_file = 'sources/election_history_db.csv'

    processor = CSVProcessor(csv_file)

    try:
        success = processor.process_csv_file()
        return 0 if success else 1
    except Exception as e:
        logging.error(f"CSV processing failed: {str(e)}")
        return 1


if __name__ == "__main__":
    exit(main())
