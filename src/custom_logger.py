import asyncio
import functools
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

import structlog


class CustomLogger:
    """
    Structured logging using structlog with stdlib backend.
    - Console: colored human-readable output (or JSON if not a TTY)
    - File: JSON lines for easy parsing
    """

    _configured = False
    _log_file = None

    def __init__(self, component_name: str, log_dir: str = "logs"):
        if not CustomLogger._configured:
            self._setup_logging(log_dir)
            CustomLogger._configured = True

        self.logger = structlog.get_logger(component_name)
        self.component_name = component_name

    @classmethod
    def _setup_logging(cls, log_dir: str):
        """Configure structlog with stdlib backend"""
        log_path = Path(log_dir)
        log_path.mkdir(exist_ok=True)

        current_date = datetime.now().strftime("%Y-%m-%d")
        cls._log_file = log_path / f"application_{current_date}.log"

        # Get log level from env (default INFO=20)
        log_level = int(os.environ.get("LOG_LEVEL", "20"))

        # Configure stdlib logging - set root to DEBUG, handlers control actual filtering
        logging.basicConfig(
            format="%(message)s",
            stream=sys.stdout,
            level=logging.DEBUG,  # Root logger at DEBUG, handlers filter
            force=True,
        )

        # Set console handler level from env
        console_handler = logging.root.handlers[0]
        console_handler.setLevel(log_level)

        # Add file handler for JSON output - always DEBUG
        file_handler = logging.FileHandler(cls._log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter("%(message)s"))
        logging.root.addHandler(file_handler)

        # Ensure all loggers propagate to root
        logging.root.setLevel(logging.DEBUG)

        # Structlog configuration
        structlog.configure(
            processors=[
                structlog.contextvars.merge_contextvars,
                structlog.stdlib.add_log_level,
                structlog.stdlib.add_logger_name,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.UnicodeDecoder(),
                structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
            ],
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            context_class=dict,
            cache_logger_on_first_use=True,
        )

        # Configure different output formats for console vs file
        console_handler.setFormatter(
            structlog.stdlib.ProcessorFormatter(
                foreign_pre_chain=[
                    structlog.stdlib.add_log_level,
                    structlog.processors.TimeStamper(fmt="iso"),
                ],
                processors=[
                    structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                    structlog.dev.ConsoleRenderer(colors=sys.stdout.isatty()),
                ],
            )
        )

        # JSON formatter for file handler
        file_handler.setFormatter(
            structlog.stdlib.ProcessorFormatter(
                foreign_pre_chain=[
                    structlog.stdlib.add_log_level,
                    structlog.processors.TimeStamper(fmt="iso"),
                ],
                processors=[
                    structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                    structlog.processors.JSONRenderer(),
                ],
            )
        )

    def debug(self, msg: str, **kwargs):
        self.logger.debug(msg, component=self.component_name, **kwargs)

    def info(self, msg: str, **kwargs):
        self.logger.info(msg, component=self.component_name, **kwargs)

    def warning(self, msg: str, **kwargs):
        self.logger.warning(msg, component=self.component_name, **kwargs)

    def error(self, msg: str, **kwargs):
        self.logger.error(msg, component=self.component_name, **kwargs)

    def critical(self, msg: str, **kwargs):
        self.logger.critical(msg, component=self.component_name, **kwargs)


def log_function_call(logger: CustomLogger):
    """
    Decorator to log function entries and exits with parameters
    """

    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            func_name = func.__name__
            logger.debug(f"Entering {func_name}", args=str(args)[:100], kwargs=str(kwargs)[:100])
            try:
                result = await func(*args, **kwargs)
                logger.debug(f"Exiting {func_name}", result=str(result)[:100])
                return result
            except Exception as e:
                logger.error(f"Error in {func_name}", error=str(e), exc_info=True)
                raise

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            func_name = func.__name__
            logger.debug(f"Entering {func_name}", args=str(args)[:100], kwargs=str(kwargs)[:100])
            try:
                result = func(*args, **kwargs)
                logger.debug(f"Exiting {func_name}", result=str(result)[:100])
                return result
            except Exception as e:
                logger.error(f"Error in {func_name}", error=str(e), exc_info=True)
                raise

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator


logger = CustomLogger("root")
