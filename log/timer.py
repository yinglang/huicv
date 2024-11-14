import time
import logging

# 配置日志
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# 创建日志记录器
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def class_timer(func):
    def wrapper(self, *args, **kwargs):
        try:
            start = time.time()
            result = func(self, *args, **kwargs)
            end = time.time()
            # AgentLoggerControler._record_time(func, self, end - start)
            # if AgentLoggerControler.info["print_timer_log"]:
            name = self
            if hasattr(self, '__class__'):
                name = self.__class__.__name__ 
            elif hasattr(self, '__name__'):
                name = self.__name__
            logger.info(f"[{name}.{func.__name__}] Time elapsed: {end - start:.1f} seconds")
            return result
        except Exception as e:
            logger.info(f"Error in {func}({self}): {e}")
            raise e
    return wrapper


def func_timer(func):
    def wrapper(*args, **kwargs):
        try:
            start = time.time()
            result = func(*args, **kwargs)
            end = time.time()
            # AgentLoggerControler._record_time(func, self, end - start)
            # if AgentLoggerControler.info["print_timer_log"]:
            name = func
            logger.info(f"[{name}] Time elapsed: {end - start:.1f} seconds")
            return result
        except Exception as e:
            logger.info(f"Error in {func}({self}): {e}")
            raise e
    return wrapper


    