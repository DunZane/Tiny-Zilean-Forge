import logging
import datetime

def setup_logger(logger_name, log_level=logging.INFO):
    logger = logging.getLogger(logger_name)
    logger.setLevel(log_level)
    # Create a formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    # Create a file handler
    log_file_path = "logs/{}_{}.log".format(logger_name, datetime.datetime.now().strftime("%Y-%m-%d_%H"))
    # For output to file
    file_handler = logging.FileHandler(log_file_path)
    file_handler.setLevel(log_level)
    # Add the formatter to the file handler
    file_handler.setFormatter(formatter)
    # Add the file handler to the logger
    logger.addHandler(file_handler)
    # Create a console handler (optional, for simultaneous output to console)
    ch = logging.StreamHandler()
    ch.setLevel(log_level)
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    return logger
