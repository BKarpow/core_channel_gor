from ast import parse
from statistics import mode
import telebot
import time
import os
import re
from requests import get
from pathlib import Path, PosixPath
from loguru import logger


class CombatLosses:
    def __init__(self) -> None:
        self.timeout_loop = 300
        self.json_data_url = 'https://tg.i-c-a.su/json/GeneralStaffZSU'
        self.data_media_url = 'https://tg.i-c-a.su/media/GeneralStaffZSU/{message_id}'
        self.bot_token = os.getenv('TELEGRAM_TOKEN')
        self.chat_id = os.getenv('CHAT_ID')
        self.bot = telebot.TeleBot(self.bot_token, parse_mode='HTML')
        self.losses_img_dir = self.get_path_dir( Path('losses_images') )
        self.logs_dir = self.get_path_dir( Path('logs') )
        self.log_file_info = self.logs_dir / 'combat_losses_info.log'
        self.log_file_error = self.logs_dir / 'combat_losses_error.log'
        self.json_data =  {}
        self._work = True
        self.losses_list = []
        self.text_losses = r'Загальні бойові втрати противника'
        logger.add(self.log_file_info.absolute(), level='INFO', rotation='10 KB', compression='zip')
        logger.add(self.log_file_error.absolute(), level='ERROR', rotation='10 KB', compression='zip')


    def run(self) -> None:
        self._work = True


    def terminate(self) -> None:
        self._work = False


    def get_path_dir(self, dir: PosixPath) -> PosixPath:
        if not dir.exists():
            os.mkdir(dir.absolute())
        return dir


    def get_json_data(self) -> dict:
        try:
            req = get(self.json_data_url)
            if req.status_code == 200:
                logger.info(req)
                return req.json()
            else:
                logger.error(req)
        except:
            logger.error('Помилка звя\'зку з мерехою')


    def get_message_losses(self) -> list:
        ''' Повертає список повідомлення про втрати противника  '''
        msg = []
        self.json_data = self.get_json_data()
        for m in self.json_data['messages']:
            if re.search(self.text_losses, m['message']):
                msg.append(m)
        return msg


    def download_losses(self, msg) -> PosixPath:
        url = self.data_media_url.format(message_id=msg['id'])
        file_image = self.losses_img_dir / (str(msg['media']['photo']['date']) + '.jpg')
        try:
            logger.debug(file_image)
            req = get(url, allow_redirects=True)
            logger.debug(req)
            logger.debug(file_image.absolute())
            if not file_image.exists():
                with open(file_image.absolute(), 'wb') as f:
                    f.write(req.content)
                logger.info(f'Завантажено {file_image}')
                return file_image
            else:
                logger.error('Такий файл вже завантажено!')
        except:
            logger.error('Помилка завантаження зображення')


    def strip_tags(self, text: str) -> str:
        text = text.replace('<br />', '\n')
        text = text.replace('Підписатися', 'Джерело')
        text = text.replace('ГШ ЗСУ', '@GeneralStaffZSU')
        t = re.sub(r'<[^>]+?>', '', text);
        t = re.sub(r'\n+', '\n', t)
        t = re.sub(r'#[\w]+', '', t)
        t += '\n #втрати_рашистів'
        return t


    def send_message(self, img: PosixPath, text: str) -> None:
        logger.info(f'Віжправлено інформацію про втрати на канал {self.chat_id}.')
        text = self.strip_tags(text)
        self.bot.send_photo(self.chat_id, img.open(mode='rb'), caption=text)


    def is_unique_losses(self, msg) -> bool:
        uniq = True
        file_image = self.losses_img_dir / (str(msg['media']['photo']['date']) + '.jpg')
        if file_image.exists():
            uniq = False
            logger.debug(f'Такі втрати вже було відправлено! {file_image}')
        return uniq


    def execute_send_combat_losses(self):
        messages = self.get_message_losses()
        for message in messages:
            if self.is_unique_losses(message):
                ph = self.download_losses(message)
                self.send_message(ph, message['message'])


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



# if __name__ == '__main__':
#     m = CombatLosses()
#     ms = m.get_message_losses()
#     m.loop()


    