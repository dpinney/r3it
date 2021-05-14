import logging, config
import datetime as dt

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
    nowUTC = dt.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S:%f %Z')
    toWrite = nowUTC + ',\t' + '"' + message + '"'
    
    if level=='debug':
        logger.debug(toWrite)
    elif level=='info':
        logger.info( toWrite)
    elif level=='warning':
        logger.warning(toWrite)
    elif level=='error':
        logger.error(toWrite)
    elif level=='critical':
        logger.critical(toWrite)
    else: raise Exception('invalid logging level')