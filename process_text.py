"""
Text processing script with improved error handling and logging.
"""
import json
import os
import re
import logging
from typing import List, Optional
from pathlib import Path
from logger_config import setup_logger

SOURCE_FOLDER = 'scraped_sites'
DESTINATION_FOLDER = 'processed_text'


class TextProcessor:
    """Text processing class with comprehensive error handling."""

    def __init__(self, source_folder: str = SOURCE_FOLDER, dest_folder: str = DESTINATION_FOLDER):
        self.source_folder = source_folder
        self.dest_folder = dest_folder
        self.logger = setup_logger(__name__)
        self.processed_count = 0
        self.error_count = 0
        self.skipped_count = 0

    def process_all_files(self) -> None:
        """Process all JSON files in the source folder."""
        try:
            # Validate source folder exists
            if not os.path.exists(self.source_folder):
                raise FileNotFoundError(f"Source folder not found: {self.source_folder}")

            # Create destination folder if it doesn't exist
            os.makedirs(self.dest_folder, exist_ok=True)

            # Get all JSON files
            json_files = [f for f in os.listdir(self.source_folder) if f.endswith('.json')]

            if not json_files:
                self.logger.warning(f"No JSON files found in {self.source_folder}")
                return

            self.logger.info(f"Processing {len(json_files)} files from {self.source_folder}")

            for filename in json_files:
                try:
                    self.process_single_file(filename)
                except Exception as e:
                    self.logger.error(f"Failed to process {filename}: {str(e)}")
                    self.error_count += 1

            self._log_summary()

        except Exception as e:
            self.logger.error(f"Error processing files: {str(e)}")
            raise

    def process_single_file(self, filename: str) -> Optional[str]:
        """
        Process a single JSON file and convert to text.

        Args:
            filename: Name of the JSON file to process

        Returns:
            Path to output file if successful, None if failed
        """
        input_path = os.path.join(self.source_folder, filename)

        # Create output filename by replacing .json with .txt
        if filename.endswith('.json'):
            output_filename = filename[:-5] + '.txt'  # Remove .json, add .txt
        else:
            output_filename = filename + '.txt'

        output_path = os.path.join(self.dest_folder, output_filename)

        try:
            # Check if output file already exists
            if os.path.exists(output_path):
                self.logger.debug(f"Output file already exists, skipping: {output_path}")
                self.skipped_count += 1
                return output_path

            # Load and validate JSON data
            data = self._load_json_file(input_path)
            if data is None:
                return None

            # Skip PDF files
            if 'url' in data and data['url'] and 'pdf' in data['url'].lower():
                self.logger.info(f"Skipping PDF file: {filename}")
                self.skipped_count += 1
                return None

            # Extract and process text
            processed_text = self._extract_and_process_text(data, filename)
            if not processed_text:
                self.logger.warning(f"No valid text extracted from {filename}")
                return None

            # Write processed text to file
            self._write_text_file(output_path, processed_text)

            self.processed_count += 1
            self.logger.debug(f"Successfully processed: {filename}")
            return output_path

        except Exception as e:
            self.logger.error(f"Error processing {filename}: {str(e)}")
            self.error_count += 1
            return None

    def _load_json_file(self, file_path: str) -> Optional[dict]:
        """Load and validate JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if not isinstance(data, dict):
                raise ValueError("JSON file does not contain a dictionary")

            return data

        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in {file_path}: {str(e)}")
            return None
        except FileNotFoundError:
            self.logger.error(f"File not found: {file_path}")
            return None
        except Exception as e:
            self.logger.error(f"Error reading {file_path}: {str(e)}")
            return None

    def _extract_and_process_text(self, data: dict, filename: str) -> Optional[str]:
        """Extract and process text from JSON data."""
        try:
            # Get text content
            text = data.get('text', '')
            if not text or not isinstance(text, str):
                self.logger.warning(f"No valid text field in {filename}")
                return None

            if len(text.strip()) < 10:
                self.logger.warning(f"Text too short in {filename}")
                return None

            # Process text: extract words, convert to lowercase, filter by length
            words = re.findall(r'\w+', text.lower())
            words = [word for word in words if len(word) > 2]

            if not words:
                self.logger.warning(f"No valid words extracted from {filename}")
                return None

            processed_text = ' '.join(words)

            # Validate processed text length
            if len(processed_text) < 20:
                self.logger.warning(f"Processed text too short in {filename}")
                return None

            return processed_text

        except Exception as e:
            self.logger.error(f"Error processing text from {filename}: {str(e)}")
            return None

    def _write_text_file(self, output_path: str, text: str) -> None:
        """Write processed text to file."""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(text)

        except IOError as e:
            raise IOError(f"Failed to write to {output_path}: {str(e)}")

    def _log_summary(self) -> None:
        """Log processing summary."""
        total_files = self.processed_count + self.error_count + self.skipped_count
        self.logger.info(f"Processing complete: {self.processed_count} processed, "
                        f"{self.skipped_count} skipped, {self.error_count} errors out of {total_files} total")

        if self.error_count > 0:
            self.logger.warning(f"Failed to process {self.error_count} files")


def main():
    """Main function to run text processing."""
    processor = TextProcessor()
    try:
        processor.process_all_files()
    except Exception as e:
        logging.error(f"Text processing failed: {str(e)}")
        return 1
    return 0


if __name__ == "__main__":
    exit(main())

