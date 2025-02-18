import logging
import os
from logging.handlers import TimedRotatingFileHandler
import datetime
from colors import *

class ColoredFormatter(logging.Formatter):
    """Custom formatter that adds colors to console output"""
    
    COLORS = {
        'DEBUG': BLUE,
        'INFO': RESET_ALL,
        'WARNING': YELLOW,
        'ERROR': RED,
        'CRITICAL': RED
    }

    def format(self, record):
        # Save original levelname to restore it later
        orig_levelname = record.levelname
        # Add color to levelname for console output
        record.levelname = f"{self.COLORS.get(record.levelname, RESET_ALL)}{record.levelname}{RESET_ALL}"
        result = super().format(record)
        # Restore original levelname
        record.levelname = orig_levelname
        return result

class MarkdownFormatter(logging.Formatter):
    """Custom formatter for markdown log files"""
    
    def format(self, record):
        # Convert log level to markdown heading level
        level_to_heading = {
            'DEBUG': '###',
            'INFO': '##',
            'WARNING': '##',
            'ERROR': '##',
            'CRITICAL': '#'
        }
        
        heading = level_to_heading.get(record.levelname, '##')
        formatted_time = datetime.datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        
        # Format message with markdown
        msg = record.getMessage()
        if record.levelno >= logging.ERROR:
            msg = f"❌ {msg}"
        elif record.levelno >= logging.WARNING:
            msg = f"⚠️ {msg}"
        elif record.levelno == logging.INFO:
            msg = f"✓ {msg}"
        else:  # DEBUG
            msg = f"🔍 {msg}"
            
        return f"{heading} {formatted_time} - {record.levelname}\n{msg}\n"

def setup_logging(log_dir="logs", log_level="INFO"):
    """Set up logging configuration
    
    Args:
        log_dir (str): Directory for log files
        log_level (str): Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Convert string level to logging constant
    try:
        numeric_level = getattr(logging, log_level.upper())
    except (AttributeError, TypeError):
        print(f"Invalid log level: {log_level}, defaulting to INFO")
        numeric_level = logging.INFO
    
    # Create logs directory if it doesn't exist
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Create logger
    logger = logging.getLogger('rooykup')
    logger.setLevel(numeric_level)

    # Create console handler with colored output
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    colored_formatter = ColoredFormatter(
        fmt='%(levelname)s %(message)s'
    )
    console_handler.setFormatter(colored_formatter)

    # Create file handler with markdown formatting and daily rotation
    today = datetime.date.today()
    log_file = os.path.join(log_dir, f"log-{str(today)}.md")
    file_handler = TimedRotatingFileHandler(
        log_file,
        when='midnight',
        interval=1,
        backupCount=30,  # Keep last 30 days
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    markdown_formatter = MarkdownFormatter()
    file_handler.setFormatter(markdown_formatter)

    # Add handlers to logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    # Log initial entry
    logger.info(f"Backup session started")

    return logger