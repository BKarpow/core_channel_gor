from telebot import types
from selenium import webdriver
from loguru import logger

import telebot
import time
import os


class ScreenAirAlerts:
    def __init__(self, telegram_chat_id='', telegram_bot_token='') -> None:
        self.webdrive = {}
        self.url_source = 'https://alerts.in.ua/'
        self.root_dir = os.path.dirname(__file__)
        self.screens_dir = os.path.join(self.root_dir, 'screens')
        self.last_path_screen = ''
        self.format_filename_screen = 'alerts_in_{dt}.png'
        self.tg_chat_id = telegram_chat_id
        self.tg_bot_token = telegram_bot_token


    def get_screen_path(self) -> str:
        if not os.path.isdir(self.screens_dir):
            os.mkdir(self.screens_dir)
            logger.info(f'Створено папку для скрінів {self.screens_dir}')
        date = time.strftime('%d%m%y%H%M%S')
        filename = self.format_filename_screen.format(dt=date)
        sp = os.path.join(self.screens_dir, filename)
        self.last_path_screen = sp
        return sp


    def shot_screen(self):
        self.webdrive = webdriver.Chrome()
        self.webdrive.get(self.url_source)
        screen_name = self.get_screen_path()
        time.sleep(22)
        self.webdrive.save_screenshot(screen_name)
        logger.info(f'Файл скріну тривог здережено як: {screen_name}')
        self.webdrive.close()


    def send_scren_to_telegram(self, msg: str):
        if self.tg_chat_id == '' or self.tg_bot_token == '':
            logger.error('Не вказано назву каналу, або токен боту каналу для Telegram')
            return
        if self.last_path_screen == '' or not os.path.isfile(self.last_path_screen):
            logger.error('Немає запису про останній скрін карти тривог. Останній запис: {self.last_path_screen}')
            return
        bot = telebot.TeleBot(self.tg_bot_token)
        fc = open(self.last_path_screen, 'rb')
        bot.send_photo(self.tg_chat_id, fc, caption=msg)


    def run(self):
        pass


    def terminate(self):
        pass


if __name__ == "__main__":
    sc = ScreenAirAlerts('', '')
    sc.shot_screen()
    sc.send_scren_to_telegram()