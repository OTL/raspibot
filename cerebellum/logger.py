import logging
import logging.handlers

import datetime as dt

class MyFormatter(logging.Formatter):
    converter=dt.datetime.fromtimestamp
    def formatTime(self, record, datefmt=None):
        ct = self.converter(record.created)
        if datefmt:
            s = ct.strftime(datefmt)
        else:
            t = ct.strftime("%Y-%m-%d %H:%M:%S")
            s = "%s,%03d" % (t, record.msecs)
        return s


def create_logger(name, level=logging.INFO):
    logger = logging.getLogger(name)
    formatter = MyFormatter(fmt='%(asctime)s [%(levelname)s] @%(name)s: %(message)s',
                            datefmt='%Y-%m-%d %l:%M:%S.%f')
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(level)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    file_handler = logging.handlers.RotatingFileHandler(filename='cerebellum_log.txt', maxBytes=10000000)
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.setLevel(level)
    return logger


def main():
    logger = create_logger('sample')
    logger.debug('d dayo')
    logger.info('info dayo')
    logger.warn('w dayo')
    logger.error('error kana?')

if __name__ == '__main__':
    main()
