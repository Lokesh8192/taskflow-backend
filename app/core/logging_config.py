import logging
import logging.config


def setup_logging(log_level: str = "INFO") -> None:
    """
    Configure application-wide logging.

    Logs are written to stdout so they can be viewed locally
    and by deployment platforms such as Render.
    """

    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": (
                    "%(asctime)s | "
                    "%(levelname)s | "
                    "%(name)s | "
                    "%(message)s"
                )
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
                "stream": "ext://sys.stdout",
            }
        },
        "root": {
            "level": log_level.upper(),
            "handlers": ["console"],
        },
    }

    logging.config.dictConfig(logging_config)