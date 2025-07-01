import logging
import logging.handlers
import sys
from pathlib import Path
from app.core.config import settings

def setup_logging():
    """Setup logging configuration for FastAPI"""
    
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Configure logging format
    log_format = logging.Formatter(
        '[{asctime}] {levelname} {name} {message}',
        datefmt='%Y-%m-%d %H:%M:%S',
        style='{'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, settings.LOG_LEVEL))
    console_handler.setFormatter(log_format)
    
    # File handler
    file_handler = logging.handlers.RotatingFileHandler(
        log_dir / settings.LOG_FILE,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(log_format)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    # Configure specific loggers
    loggers = {
        'app': {
            'level': 'DEBUG',
            'handlers': ['console', 'file'],
            'propagate': False
        },
        'uvicorn': {
            'level': 'INFO',
            'handlers': ['console', 'file'],
            'propagate': False
        },
        'langchain': {
            'level': 'DEBUG',
            'handlers': ['console', 'file'],
            'propagate': False
        }
    }
    
    for logger_name, config in loggers.items():
        logger = logging.getLogger(logger_name)
        logger.setLevel(getattr(logging, config['level']))
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
        logger.propagate = config['propagate']
    
    logging.info("✅ Logging configuration setup complete") 