"""
logger.py

This module sets up a logging system that writes messages to both the console and a log file.
It uses a rotating file handler to limit the size of the log file and maintain backup copies.

Functions:
- setup_logging: Configures logging with customizable options such as log level, file name, 
  maximum file size, and the number of backup copies.

Usage:
    log = setup_logging(name="my_logger", log_level=logging.DEBUG, log_file="my_log.log")
    log.info("This is an informational message")
    log.error("This is an error message")

Author:
- Erik Pereira
"""

import logging
import os
from logging.handlers import RotatingFileHandler  # Importar RotatingFileHandler correctamente

def setup_logging(name="log", log_level=logging.INFO, log_file="log.log", log_dir="logs", max_bytes=1024*1024*16, backup_count=5):
    """
    Configures the logging system to write messages to the console and a log file.

    Parameters:
        name (str): Name of the logger. Default is "log".
        log_level (int): Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL). Default is logging.INFO.
        log_file (str): Name of the log file. Default is "log.log".
        log_dir (str): Directory where the log file will be stored. Default is "logs".
        max_bytes (int): Maximum size of the log file in bytes before rotating. Default is 16 MB.
        backup_count (int): Maximum number of backup log files to keep. Default is 5.

    Returns:
        logging.Logger: Configured logger instance.

    Example:
        log = setup_logging(name="my_logger", log_level=logging.DEBUG, log_file="my_log.log")
        log.info("This is an informational message")
    """
    # Create a logger instance with the specified name
    log = logging.getLogger(name)
    log.setLevel(log_level)  # Set the logging level

    # Define the format for log messages
    log_formatter = logging.Formatter('%(asctime)s - %(levelname)s: %(message)s')

    # Configure the console log handler
    log_str_handler = logging.StreamHandler()
    log_str_handler.setFormatter(log_formatter)
    log.addHandler(log_str_handler)

    # Create the log directory if it does not exist
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Configure the rotating file log handler
    log_file_path = os.path.join(log_dir, log_file)
    log_file_handler = RotatingFileHandler(  # Usar RotatingFileHandler correctamente
        log_file_path, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
    )
    log_file_handler.setFormatter(log_formatter)
    log.addHandler(log_file_handler)

    # Return the configured logger instance
    return log