from ast import parse
from loguru import logger
from time import strftime, sleep

import telebot
import os
import re

class CommendantTime:
    def __init__(self) -> None:
        self.TIMEOUT = 0.65
        self.START_STOP_TRIGGER = False
        self.BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
        self.BOT_CHAT_ID = os.getenv("CHAT_ID")
        self.TIME_START = os.getenv("TIME_COMMENDANT_START")
        self.TIME_END = os.getenv("TIME_COMMENDANT_END")
        self.bot = telebot.TeleBot(self.BOT_TOKEN)
        self.log_filename_format = 'comendant_{time}.log'
        self.message_start = '❗️❗️КОМЕНДАНТСЬКА ГОДИНА - ПОЧАЛАСЬ, ТУСИТИ ПО МІСТІ ЗАБОРОНЕНО❗️❗️❗️❗️❗️❗️'
        self.message_end = '❗️❗️КОМЕНДАНТСЬКА ГОДИНА - ЗАКІНЧИЛАСЬ, ТУСИТИ ВЖЕ МОЖНА❗️😀😀'
        self._work = True



    def is_valid_format_time(self, time: str) -> bool:
        return bool( re.search(r'^\d\d\:\d\d$',  time) )


    def input_times(self):
        # self.TIME_START = input("Час початку комендантської години (наприклад 23:00): ")
        # self.TIME_END = input("Час кінця комендантської години (наприклад 05:00): ")
        if not( self.is_valid_format_time(self.TIME_START) ) :
            logger.error("Помилково введений час початку комендатської години, повторіть спробу.")
            self.input_times()
        if not( self.is_valid_format_time(self.TIME_END) ) :
            logger.error("Помилково введений час кінця комендатської години, повторіть спробу.")
            self.input_times()
        logger.info(f" Час початку {self.TIME_START}, кінця {self.TIME_END} ")


    def parse_time(self):
        self.input_times()
        time = {}
        time['startH'] = int( self.TIME_START.split(":")[0] )
        time['startM'] = int( self.TIME_START.split(":")[1] )
        time['stopH'] = int( self.TIME_END.split(":")[0] )
        time['stopM'] = int( self.TIME_END.split(":")[1] )
        return time


    def send_message(self, text: str):
        self.bot.send_message(self.BOT_CHAT_ID, text)


    def is_start_time(self, time_data: dict) -> bool:
        if strftime('%H:%M:%S') == self.TIME_START + ':00':
            return True
        return False
        # h = int( strftime("%H") )
        # m = int( strftime("%M") )
        # if time_data['startH'] == h and time_data['startM'] == m and not( self.START_STOP_TRIGGER ):
        #     self.START_STOP_TRIGGER = True
        #     return True
        # return False


    def is_stop_time(self, time_data: dict) -> bool:
        if strftime('%H:%M:%S') == self.TIME_END + ':00':
            return True
        return False
        # h = int( strftime("%H") )
        # m = int( strftime("%M") )
        # if time_data['stopH'] == h and time_data['stopM'] == m and  self.START_STOP_TRIGGER:
        #     self.START_STOP_TRIGGER = False
        #     return True
        # return False


    def save_log_file(self):
        root_dir = os.path.dirname(__file__)
        logs_dir = os.path.join(root_dir, 'logs')
        if not os.path.isdir(logs_dir) :
            os.mkdir(logs_dir)
        file_path_log = os.path.join(logs_dir, self.log_filename_format)
        logger.add(file_path_log)


    def run(self):
        self._work = True


    def terminate(self):
        self._work = False


    def loop(self):
        self.save_log_file()
        logger.info("Старт повідомлень про комендатську годину")
        time = self.parse_time()
        while True:
            if not self._work:
                logger.info('Процес відправлення повідомлень про ком. годину зупинено!')
                break
            if self.is_start_time(time):
                self.send_message(self.message_start)
                logger.info(self.message_start)
            if self.is_stop_time(time):
                self.send_message(self.message_end)
                logger.info(self.message_end)
            sleep(self.TIMEOUT)



if __name__ == "__main__":
    
    ct = CommendantTime()
    ct.loop()