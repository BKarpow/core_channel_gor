import os
import re
import time

from telebot import TeleBot
from requests import get
from loguru import logger
from pathlib import Path


class RadiationAlert:
    def __init__(self) -> None:
        self.bot = TeleBot(os.getenv('TELEGRAM_TOKEN'))
        self.chat_id = os.getenv('CHAT_ID')
        self.source_url = os.getenv('JSON_SOURCE_URL')
        self.timeout = 13
        self.regions = []
        self.radiation_mark = 'Радіаційна небезпека'
        self.chemical_mark = 'Хімічна небезпека'
        self._work = True
        logger.add('dev.log')

    def send_radiation_alert(self, message) -> None:
        t = '☢️☢️☢️РАДІАЦІЙНА НЕБЕЗПЕКА - ❗️❗️УВІМКНІТЬ МІСЦЕВЕ ТЕЛЕБАЧЕННЯ ЧИ РАДІО❗️❗️'
        t += f'\n Зараз у {message["region"]} ☢️ РАДІАЦІЙНА НЕБЕЗПЕКА ☢️'
        self.bot.send_message(self.chat_id, t)

    def send_chemical_alert(self, message) -> None:
        t = '☠️☠️☠️ХІМІЧНА НЕБЕЗПЕКА - ❗️❗️УВІМКНІТЬ МІСЦЕВЕ ТЕЛЕБАЧЕННЯ ЧИ РАДІО❗️❗️'
        t += f'\n Зараз у {message["region"]} ☠️ ХІМІЧНА НЕБЕЗПЕКА ☠️'
        self.bot.send_message(self.chat_id, t)

    def get_data(self) -> list | None:
        try:
            req = get(self.source_url)
            if req.status_code != 200:
                logger.error("Помилка мережі...")
                logger.debug(req)
            elif req.json().get('messages') is not None:
                return req.json().get('messages')
            else:
                logger.error("Щось пішло не так...")
                logger.debug(req)
        except:
            logger.error("Помилка мережі, сервер не відплвів")

    def get_message_my_regions(self) -> list:
        ms = []
        messages = self.get_data()
        for region in self.regions:
            for message in messages:
                if message['message'] is None: continue
                if re.search(region, message['message']):
                    message['region'] = region
                    ms.append(message)
        return ms

    def get_last_file(self, message) -> str:
        file_name = ''
        if re.search(self.radiation_mark, message['message']):
            file_name = 'rad.txt'
        if re.search(self.chemical_mark, message['message']):
            file_name = 'che.txt'
        return file_name

    def is_unique_message(self, message) -> bool:
        file = Path(self.get_last_file(message))

        def write_file() -> None:
            with open(file.absolute(), 'w') as f:
                f.write(str(message['date']))

        def read_file() -> int:
            with open(file.absolute(), 'r') as f:
                r = f.read()
                logger.debug(r)
                return int(0 if r == '' else r)

        if not file.exists():
            write_file()
            return True
        if read_file() < int(message['date']):
            write_file()
            return True
        return False
            
    def send_alert(self) -> None:
        for msg in self.get_message_my_regions():
            if re.search(self.radiation_mark, msg['message']):
                if self.is_unique_message(msg):
                    self.send_radiation_alert(msg)
            if re.search(self.chemical_mark, msg['message']):
                if self.is_unique_message(msg):
                    self.send_chemical_alert(msg)
    
    def run(self) -> None:
        self._work = True

    def terminate(self) -> None:
        self._work = False

    def loop(self) -> None:
        logger.debug('Початок роботи сканеру радіаційної небезпеки')
        while True:
            if not self._work:
                logger.debug("Зупинка циклу...")
                break
            self.send_alert()
            time.sleep(self.timeout)


if  __name__ == "__main__":
    rad = RadiationAlert()
    rad.regions = ['#Черкаська_область', '#Городищенська_територіальна_громада']
    rad.loop()




