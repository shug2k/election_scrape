"""
Word cloud generation script with improved error handling and logging.
"""
import os
import sys
import matplotlib.pyplot as plt
from wordcloud import WordCloud, STOPWORDS
from typing import Set, List, Optional
from logger_config import setup_logger


class WordCloudGenerator:
    """Word cloud generator with comprehensive error handling."""

    def __init__(self, source_folder: str = 'processed_text', output_folder: str = 'wordclouds'):
        self.source_folder = source_folder
        self.output_folder = output_folder
        self.logger = setup_logger(__name__)
        self.stopwords = set(STOPWORDS)
        self.processed_files = 0
        self.error_files = 0

    def generate_wordcloud(self, stopwords_file: str = 'sources/election_stopwords.txt',
                          output_filename: str = 'overall.png') -> bool:
        """
        Generate a word cloud from processed text files.

        Args:
            stopwords_file: Path to custom stopwords file
            output_filename: Name of output image file

        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info("Starting word cloud generation")

            # Load custom stopwords
            if not self._load_custom_stopwords(stopwords_file):
                self.logger.warning("Proceeding without custom stopwords")

            # Load and combine all text files
            all_text = self._load_all_text_files()
            if not all_text:
                self.logger.error("No text content available for word cloud generation")
                return False

            # Create output directory
            os.makedirs(self.output_folder, exist_ok=True)

            # Generate word cloud
            success = self._create_and_save_wordcloud(all_text, output_filename)

            self._log_summary()
            return success

        except Exception as e:
            self.logger.error(f"Critical error generating word cloud: {str(e)}")
            return False

    def _load_custom_stopwords(self, stopwords_file: str) -> bool:
        """Load custom stopwords from file."""
        try:
            if not os.path.exists(stopwords_file):
                self.logger.warning(f"Stopwords file not found: {stopwords_file}")
                return False

            with open(stopwords_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        word = line.strip()
                        if word and not word.startswith('#'):  # Skip comments
                            self.stopwords.add(word.lower())
                    except Exception as e:
                        self.logger.warning(f"Error reading stopword line {line_num}: {str(e)}")

            self.logger.info(f"Loaded {len(self.stopwords)} total stopwords")
            return True

        except Exception as e:
            self.logger.error(f"Error loading stopwords from {stopwords_file}: {str(e)}")
            return False

    def _load_all_text_files(self) -> Optional[str]:
        """Load and combine all text files from source folder."""
        try:
            if not os.path.exists(self.source_folder):
                self.logger.error(f"Source folder not found: {self.source_folder}")
                return None

            text_files = [f for f in os.listdir(self.source_folder)
                         if f.endswith('.txt') and not f.startswith('.')]

            if not text_files:
                self.logger.error(f"No text files found in {self.source_folder}")
                return None

            self.logger.info(f"Processing {len(text_files)} text files")

            all_text_parts = []
            for filename in text_files:
                try:
                    text_content = self._load_single_text_file(filename)
                    if text_content:
                        all_text_parts.append(text_content)
                        self.processed_files += 1
                    else:
                        self.error_files += 1
                except Exception as e:
                    self.logger.error(f"Error processing {filename}: {str(e)}")
                    self.error_files += 1

            if not all_text_parts:
                self.logger.error("No valid text content found in any files")
                return None

            combined_text = ' '.join(all_text_parts)

            # Validate combined text
            if len(combined_text.strip()) < 100:
                self.logger.error("Combined text too short for meaningful word cloud")
                return None

            self.logger.info(f"Combined text length: {len(combined_text)} characters")
            return combined_text

        except Exception as e:
            self.logger.error(f"Error loading text files: {str(e)}")
            return None

    def _load_single_text_file(self, filename: str) -> Optional[str]:
        """Load a single text file with error handling."""
        file_path = os.path.join(self.source_folder, filename)

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            if not content or len(content.strip()) < 10:
                self.logger.warning(f"File {filename} has insufficient content")
                return None

            return content.strip()

        except UnicodeDecodeError:
            self.logger.warning(f"Unicode decode error in {filename}, trying different encoding")
            try:
                with open(file_path, 'r', encoding='latin-1') as f:
                    return f.read().strip()
            except Exception as e:
                self.logger.error(f"Failed to read {filename} with any encoding: {str(e)}")
                return None

        except Exception as e:
            self.logger.error(f"Error reading {filename}: {str(e)}")
            return None

    def _create_and_save_wordcloud(self, text: str, output_filename: str) -> bool:
        """Create and save the word cloud image."""
        try:
            # Configure word cloud parameters
            wordcloud_config = {
                'width': 1000,
                'height': 800,
                'stopwords': self.stopwords,
                'max_words': 100,
                'background_color': 'white',
                'colormap': 'viridis',
                'relative_scaling': 0.5,
                'min_font_size': 10
            }

            self.logger.info("Generating word cloud...")
            wordcloud = WordCloud(**wordcloud_config).generate(text)

            # Create the plot
            plt.figure(figsize=(12, 8))
            plt.imshow(wordcloud, interpolation='bilinear')
            plt.axis('off')
            plt.tight_layout()

            # Save the image
            output_path = os.path.join(self.output_folder, output_filename)
            plt.savefig(output_path, dpi=600, bbox_inches='tight')

            self.logger.info(f"Word cloud saved to: {output_path}")

            # Show the plot (if in interactive environment)
            try:
                plt.show()
            except Exception:
                self.logger.info("Display not available, image saved only")

            plt.close()  # Clean up
            return True

        except ImportError as e:
            self.logger.error(f"Missing required dependencies: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"Error creating word cloud: {str(e)}")
            return False

    def _log_summary(self) -> None:
        """Log processing summary."""
        total_files = self.processed_files + self.error_files
        self.logger.info(f"Word cloud generation complete:")
        self.logger.info(f"  Files processed: {self.processed_files}")
        self.logger.info(f"  Files with errors: {self.error_files}")
        self.logger.info(f"  Total files: {total_files}")

        if self.error_files > 0:
            self.logger.warning(f"Completed with {self.error_files} file errors")


def main():
    """Main function to run word cloud generation."""
    # Parse command line arguments
    source_folder = sys.argv[1] if len(sys.argv) > 1 else 'processed_text'
    output_filename = sys.argv[2] if len(sys.argv) > 2 else 'overall.png'

    generator = WordCloudGenerator(source_folder=source_folder)

    try:
        success = generator.generate_wordcloud(output_filename=output_filename)
        return 0 if success else 1
    except Exception as e:
        import logging
        logging.error(f"Word cloud generation failed: {str(e)}")
        return 1


if __name__ == "__main__":
    exit(main())
