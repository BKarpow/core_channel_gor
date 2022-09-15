
from tkinter.messagebox import NO
import telebot
import time
import os
import re
from requests import get
from pathlib import Path, PosixPath
from loguru import logger
from shutil import copy
from qu import SmartSender


class CombatLosses:
    def __init__(self,  queue: SmartSender) -> None:
        self.queue = queue
        self.timeout_loop = 120
        self.json_data_url = os.getenv('JSON_SOURCE_URL')
        self.bot_token = os.getenv('TELEGRAM_TOKEN')
        self.chat_id = os.getenv('CHAT_ID')
        self.bot = telebot.TeleBot(self.bot_token, parse_mode='HTML')
        self.logs_dir =  Path('logs')
        self.losses_folder = Path('losses_images')
        self.log_file_info = self.logs_dir / 'combat_losses_info.log'
        self.log_file_error = self.logs_dir / 'combat_losses_error.log'
        self.json_data =  {}
        self._work = True
        self.losses_list = []
        self.war_start_date = "24.02.2022 05:00:00"
        self.text_losses = r'Загальні бойові втрати противника'
        self.format_time_loses = "%d.%m.%Y %H:%M:%S"
        logger.add(self.log_file_info.absolute(), level='INFO', rotation='10 KB', compression='zip')
        logger.add(self.log_file_error.absolute(), level='ERROR', rotation='10 KB', compression='zip')


    def run(self) -> None:
        self._work = True


    def terminate(self) -> None:
        self._work = False


    def get_timestamp_from_date(self, date: str) -> int:
        ''' Конвертує рядок дати в формат unix (секунди) '''
        return int( time.mktime( time.strptime(date, self.format_time_loses) ) )


    def calc_duration_war(self) -> int:
        ''' Поверне тривалість війни в днях '''
        date_today = time.strftime(self.format_time_loses)
        unix_start_war = self.get_timestamp_from_date(self.war_start_date)
        unix_today = self.get_timestamp_from_date(date_today)
        res = (unix_today - unix_start_war) / 60 / 60
        # h = int( res % 24) години
        d = int(res / 24) # Дні війни
        d += 1 # Поправка
        logger.debug(f"result calc {d}, date start war: {self.war_start_date}")
        return d

    def get_json_data(self) -> dict:
        try:
            req = get(self.json_data_url)
            if req.status_code == 200:
                return req.json()
            else:
                logger.error(req.json())
        except:
            logger.error('Помилка звя\'зку з мерехою')


    def strip_tags(self, text: str) -> str:
        logger.debug(f"Фільтрція повідомлення: {text}")
        text = text.replace('<br />', '\n')
        text = text.replace('**', '')
        text = text.replace('Підписатися', 'Джерело')
        text = text.replace('ГШ ЗСУ', '@GeneralStaffZSU')
        text = text.replace('[|', '')
        t = re.sub(r'<[^>]+?>', '', text);
        t = re.sub(r'\|\]\(http[^\s]+', '', text);
        t = re.sub(r'\n+', '\n', t)
        t = re.sub(r'\s+', ' ', t)
        t = re.sub(r'#[\w]+', '', t)
        dw = self.calc_duration_war()
        t += f"\n{dw} день війнм з ₚосією.\n"
        t += '\n#втрати_рашистів'
        return t


    def send_message(self, img: PosixPath, text: str) -> None:
        logger.info(f'Віжправлено інформацію про втрати на канал {self.chat_id}.')
        text = self.strip_tags(text)
        self.queue.send('photo', text, img.absolute())
        # self.bot.send_photo(self.chat_id, img.open(mode='rb'), caption=text)

    def execute_send_combat_losses(self):
        messages = self.get_json_data()
        if messages.get('losses') is None:
            logger.error('Некоректна відповідь API...')
            return None
        message = messages['losses']
        if message.get('filename') is not None:
            ph = Path(message['path'])
            file_name = message['filename']
            to_dir = self.losses_folder / file_name
            if not to_dir.exists():
                self.send_message(ph, message['message'])
                copy(ph.absolute(), to_dir.absolute())
                logger.info(f"Coping to file")

        


    def loop(self) -> None:
        logger.info(f'Початок роботи чканеру бойових втрат рашистів та відправки їх на канал {self.chat_id}')
        try:
            while True:
                if not self._work:
                    logger.info('Відправку втрат зупинено')
                    break
                self.execute_send_combat_losses()
                time.sleep(self.timeout_loop)
        except KeyboardInterrupt:
            logger.info('Припинено користувачем.')


    