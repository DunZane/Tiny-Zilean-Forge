import logging
import datetime


def setup_logger(logger_name,log_level=logging.INFO):
    logger = logging.getLogger(logger_name)
    logger.setLevel(log_level)
    # 创建一个格式化程序
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    # 创建一个文件处理程序
    log_file_path = "logs/{}_{}.log".format(logger_name,datetime.datetime.now().strftime("%Y-%m-%d_%H"))
    # 用于输出至文件
    file_handler = logging.FileHandler(log_file_path)
    file_handler.setLevel(log_level)
    # 将格式化程序添加到文件处理程序
    file_handler.setFormatter(formatter)
    # 将文件处理程序添加到日志记录器
    logger.addHandler(file_handler)
    # 创建一个控制台处理程序（可选，用于同时输出到控制台）
    ch = logging.StreamHandler()
    ch.setLevel(log_level)
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    return logger

