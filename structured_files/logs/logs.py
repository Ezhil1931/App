import logging
import os
from datetime import datetime

# Configure logger
logger = logging.getLogger('application')
logger.setLevel(logging.INFO)

# Create formatters
formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

# Create console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

# Create file handler
log_file = os.path.join(os.getcwd(), 'application.log')
file_handler = logging.FileHandler(log_file)
file_handler.setFormatter(formatter)

# Add handlers to logger
if not logger.handlers:
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

# Utility functions
def log_info(message: str) -> None:
    logger.info(message)

def log_error(message: str) -> None:
    logger.error(message)

if __name__ == "__main__":
    # Example usage
    log_info("This is an info message.")
    log_error("This is an error message.")