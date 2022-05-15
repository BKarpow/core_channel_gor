from xmlrpc.client import Boolean
from requests import get
from time import sleep
from loguru import logger
from os.path import dirname, join, isdir
from os import mkdir, getenv


class CronDemon:
    def __init__(self) -> None:
        self.LOG_DIR = join(dirname(__file__), 'cronLogs');
        self.LOG_FILE = join(self.LOG_DIR, "file_{time}.log")
        self.CRON_URL = getenv('CRON_URL')
        self.CRON_TIMEOUT = int( getenv('CRON_TIMEOUT') )
        self._work = True


    def create_dir_for_logs(self) -> None:
        if not(isdir(self.LOG_DIR)):
            mkdir(self.LOG_DIR)


    def start_logger(self) -> None:
        self.create_dir_for_logs()
        logger.add(self.LOG_FILE, encoding="utf8")


    def get_data(self) -> None:
        try:
            res = get(self.CRON_URL, headers={"CRON-TIMEOUT": str(self.CRON_TIMEOUT) })
            if res.status_code != 200:
                logger.debug(res)
        except:
            logger.error("Помилка зв'язку, немає мережі.")


    def run(self):
        self._work = True


    def terminate(self) -> None:
        self._work = False


    def loop(self) -> None:
        logger.info(f"Початок роботи крону з таймаутом в : {self.CRON_TIMEOUT} секунд, на адресу: {self.CRON_URL}")
        while True:
            if not self._work:
                logger.info('Луп крону зупинено!')
                break
            self.get_data()
            sleep(self.CRON_TIMEOUT)


if __name__ == "__main__":
    cron = CronDemon()
    cron.start_logger()
    cron.loop()
    

