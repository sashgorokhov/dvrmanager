"""
Logging configuration
"""
import logging
import logging.config

from dvrmanager import config


def configure():
    """
    Contifure logging facilites
    """
    config.LOGS_DIR.mkdir(parents=True, exist_ok=True)
    logging.config.dictConfig(LOGGING_CONFIG)


LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'default': {
            'format': '[%(asctime)s] [%(levelname)-5s] [%(name)s] %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
        'short': {
            'format': '%(levelname)s: %(message)s',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'formatter': 'default',
            'class': 'logging.StreamHandler',
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'default',
            'filename': config.LOGS_DIR / f'{config.APP_NAME}.log',
            'maxBytes': 1024 * 1024,  # 1 mb
            'backupCount': 2
        },
    },
    'loggers': {
        'dvrmanager': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
    'root': {
        'handlers': ['file'],
        'level': 'ERROR'
    },
}
