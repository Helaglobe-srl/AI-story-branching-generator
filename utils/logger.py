import logging
import sys
import os
from datetime import datetime
from typing import Optional, List, Callable, Any

class StoryBranchLogger:
    """Centralized logger for the Story Branch application
    
    This class provides consistent logging across the application with
    capabilities for file logging and console output.
    """
    
    def __init__(self, 
                 name: str = "story_branch_maker",
                 log_level: int = logging.INFO,
                 log_file: str = "story_branch_maker.log",
                 log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"):
        """Initialize the logger
        
        Args:
            name: The name of the logger
            log_level: The logging level (e.g., logging.INFO)
            log_file: The file to write logs to
            log_format: The format for log messages
        """
        self.name = name
        self.log_level = log_level
        self.log_file = log_file
        self.log_format = log_format
        
        # logs directory
        os.makedirs("logs", exist_ok=True)
        
        # logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(log_level)
        
        # clear handlers
        if self.logger.hasHandlers():
            self.logger.handlers.clear()
        
        # handlers
        console_handler = logging.StreamHandler(sys.stdout)
        file_handler = logging.FileHandler(os.path.join("logs", log_file))
        
        # formatter
        formatter = logging.Formatter(log_format)
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)
        
        # add handlers to logger
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
        
        # status text for Streamlit
        self.status_text = None
    
    def get_child(self, child_name: str) -> logging.Logger:
        """Get a child logger with the given name
        
        Args:
            child_name: The name of the child logger
            
        Returns:
            A child logger
        """
        return logging.getLogger(f"{self.name}.{child_name}")
    
    def set_status_text(self, status_component: Any) -> None:
        """Set the status text component for displaying messages
        
        Args:
            status_component: A Streamlit text component to display status
        """
        self.status_text = status_component
    
    def info(self, message: str) -> None:
        """Log an info message
        
        Args:
            message: The message to log
        """
        self.logger.info(message)
        if self.status_text is not None:
            self.status_text.text(message)
    
    def warning(self, message: str) -> None:
        """Log a warning message
        
        Args:
            message: The message to log
        """
        self.logger.warning(message)
        if self.status_text is not None:
            self.status_text.text(f"Warning: {message}")
    
    def error(self, message: str) -> None:
        """Log an error message
        
        Args:
            message: The message to log
        """
        self.logger.error(message)
        if self.status_text is not None:
            self.status_text.text(f"Error: {message}")
    
    def debug(self, message: str) -> None:
        """Log a debug message
        
        Args:
            message: The message to log
        """
        self.logger.debug(message)
    
    def critical(self, message: str) -> None:
        """Log a critical message
        
        Args:
            message: The message to log
        """
        self.logger.critical(message)
        if self.status_text is not None:
            self.status_text.text(f"Critical: {message}")

# singleton instance for the app
app_logger = StoryBranchLogger()

def get_logger(module_name: str = None) -> logging.Logger:
    """Get the application logger
    
    Args:
        module_name: Optional module name to get a child logger
        
    Returns:
        The application logger or a child logger
    """
    if module_name:
        return logging.getLogger(f"{app_logger.name}.{module_name}")
    return app_logger.logger 