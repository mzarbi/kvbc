import logging.config

def setup_logger():
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s [%(levelname)s] %(filename)s %(funcName)s: %(message)s"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "INFO",
                "formatter": "standard",
                "stream": "ext://sys.stdout"
            }
        },
        "root": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False
        },
        "kv-store": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False
        }
    }
    # Configure logging
    logging.config.dictConfig(logging_config)


setup_logger()
logger = logging.getLogger("kv-store")