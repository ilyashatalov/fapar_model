import logging

FORMAT = '%(levelname)-8s [%(asctime)s] %(message)s'
logging.basicConfig(format=FORMAT, level=logging.INFO)
logger = logging.getLogger(__name__)
