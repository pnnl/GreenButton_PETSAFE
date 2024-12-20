import logging
from config import LOG_FILE

# TODO: log rotation
def config_logger():
    logging.basicConfig(level=logging.INFO, filename=LOG_FILE, encoding='utf-8', format='%(asctime)s %(levelname)s: %(message)s')
    logger = logging.getLogger(__name__)
    return logger