import asyncio
import functools
import logging
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path


class CustomLogger:
    """
    A custom logger class that logs all components to a single file with component-specific prefixes.
    """

    # Class-level handler to ensure single file usage
    _file_handler = None
    _initialized = False

    def __init__(
        self,
        component_name: str,
        log_dir: str = "logs",
        console_level: int = logging.INFO,
        file_level: int = logging.DEBUG,
        max_bytes: int = 5_242_880,  # 5MB
        backup_count: int = 5,
    ):
        self.component_name = component_name
        self.logger = logging.getLogger(f"app.{component_name}")
        self.logger.setLevel(logging.DEBUG)

        # Initialize shared file handler if not already done
        if not CustomLogger._initialized:
            self._setup_shared_handler(log_dir, file_level, max_bytes, backup_count)
            CustomLogger._initialized = True

        # Console Handler with component prefix
        console_formatter = logging.Formatter(
            "%(asctime)s - [%(component_name)s] - %(levelname)s - %(message)s",
            datefmt="%H:%M:%S",
        )

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(console_level)
        console_handler.setFormatter(console_formatter)

        # Add handlers
        self.logger.addHandler(console_handler)
        self.logger.addHandler(CustomLogger._file_handler)

        # Add component name as extra field
        self.logger = logging.LoggerAdapter(self.logger, {"component_name": component_name})

    @classmethod
    def _setup_shared_handler(cls, log_dir, file_level, max_bytes, backup_count):
        """Set up the shared file handler for all logger instances"""
        log_path = Path(log_dir)
        log_path.mkdir(exist_ok=True)

        file_formatter = logging.Formatter(
            "%(asctime)s - [%(component_name)s] - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
        )

        current_date = datetime.now().strftime("%Y-%m-%d")
        cls._file_handler = RotatingFileHandler(
            filename=log_path / f"application_{current_date}.log",
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        cls._file_handler.setLevel(file_level)
        cls._file_handler.setFormatter(file_formatter)

    def debug(self, msg, *args, **kwargs):
        self.logger.debug(msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        self.logger.info(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        self.logger.warning(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        self.logger.error(msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        self.logger.critical(msg, *args, **kwargs)


def log_function_call(logger):
    """
    Decorator to log function entries and exits with parameters
    """

    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            func_name = func.__name__
            logger.debug(f"Entering {func_name} - Args: {args}, Kwargs: {kwargs}")
            try:
                result = await func(*args, **kwargs)
                logger.debug(f"Exiting {func_name} - Result: {result}")
                return result
            except Exception as e:
                logger.error(f"Error in {func_name}: {str(e)}", exc_info=True)
                raise

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            func_name = func.__name__
            logger.debug(f"Entering {func_name} - Args: {args}, Kwargs: {kwargs}")
            try:
                result = func(*args, **kwargs)
                logger.debug(f"Exiting {func_name} - Result: {result}")
                return result
            except Exception as e:
                logger.error(f"Error in {func_name}: {str(e)}", exc_info=True)
                raise

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator


# Example usage:
if __name__ == "__main__":
    # Create logger instances for different components
    api_logger = CustomLogger("fastapi")
    discord_logger = CustomLogger("discord")
    steam_logger = CustomLogger("steam")

    # Example logging
    api_logger.info("API server starting")  # Will show: [fastapi] API server starting
    discord_logger.info("Bot connected")  # Will show: [discord] Bot connected
    steam_logger.error("Auth failed")  # Will show: [steam] Auth failed

    # Example usage with the decorator
    @log_function_call(api_logger)
    async def sample_api_endpoint():
        api_logger.info("Processing API request")

    @log_function_call(discord_logger)
    async def sample_discord_command():
        discord_logger.info("Processing Discord command")
