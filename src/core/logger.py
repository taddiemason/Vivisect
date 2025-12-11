"""Logging system for forensics operations"""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

class ForensicsLogger:
    """Centralized logging for all forensics operations"""

    def __init__(self, log_dir: str = '/var/log/vivisect', log_level: int = logging.INFO):
        self.log_dir = log_dir
        self.log_level = log_level
        self.loggers = {}

        os.makedirs(log_dir, exist_ok=True)

        # Create main logger
        self.main_logger = self._create_logger('vivisect', 'main.log')

    def _create_logger(self, name: str, filename: str) -> logging.Logger:
        """Create a logger with file and console handlers"""
        logger = logging.getLogger(name)
        logger.setLevel(self.log_level)

        # Prevent duplicate handlers
        if logger.handlers:
            return logger

        # File handler
        log_file = os.path.join(self.log_dir, filename)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(self.log_level)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)

        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        return logger

    def get_logger(self, module_name: str) -> logging.Logger:
        """Get or create a logger for a specific module"""
        if module_name not in self.loggers:
            filename = f"{module_name}.log"
            self.loggers[module_name] = self._create_logger(
                f"vivisect.{module_name}",
                filename
            )
        return self.loggers[module_name]

    def log_operation(self, module: str, operation: str, details: str, level: str = 'info'):
        """Log a forensics operation"""
        logger = self.get_logger(module)
        log_method = getattr(logger, level.lower(), logger.info)
        log_method(f"{operation}: {details}")

    def log_error(self, module: str, error: Exception, context: str = ""):
        """Log an error with context"""
        logger = self.get_logger(module)
        logger.error(f"{context} - Error: {str(error)}", exc_info=True)

    def create_case_log(self, case_id: str) -> logging.Logger:
        """Create a dedicated logger for a specific case"""
        case_logger = self._create_logger(
            f"case.{case_id}",
            f"case_{case_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        )
        return case_logger
