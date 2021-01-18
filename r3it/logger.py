import logging, config
from datetime import datetime, timezone

# instantiate logger
# if is needed because Werkzeug apparently starts the server twice,
# which ends up adding two handlers to the logger which ends up
# causing everything to be logged twice
logger = logging.getLogger('interconnectionLogger')
logger.setLevel(logging.DEBUG)
if len(logger.handlers)==0:
    handler = logging.FileHandler(config.LOG_FILENAME)
    formatter = logging.Formatter('%(levelname)s,\t%(message)s')
    logger.addHandler(handler)
    handler.setFormatter(formatter)
    handler.setLevel(logging.DEBUG)

def log(message, level='info'):
    nowUTC = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S:%f %Z')
    toWrite = nowUTC + ',\t' + '"' + message + '"'
    
    if level=='debug':
        logger.debug('\t' + toWrite)
    elif level=='info':
        logger.info('\t' + toWrite)
    elif level=='warning':
        logger.warning(toWrite)
    elif level=='error':
        logger.error('\t' + toWrite)
    elif level=='critical':
        logger.critical(toWrite)