from requests import get
from loguru import logger
from time import sleep, strftime
from screenshot import ScreenAirAlerts
from alert_sound import AirSound
from services import is_network
import datetime
import os
import telebot
import sqlite3
import re
import threading
from qu import SmartSender


def get_path_file_last_time() -> str:
    fo = os.path.join(os.path.dirname(__file__), 'last_time_alert.txt')
    logger.debug(f"Memory last time stamp file {fo}")
    return fo


def set_last_time(time: int) -> None:
    logger.debug(f"Set last time stamp {time}")
    with open(get_path_file_last_time(), 'w') as f:
        f.write(str(time))


def get_last_time() -> int:
    with open(get_path_file_last_time(), 'r') as f:
        time = f.read()
    logger.debug(f"Get last time stamp {time}")
    return int(time)





class AirAlarmHorodische:
    def __init__(self, queue: SmartSender) -> None:
        self.log_file = 'air_{time}.log'
        self.timeout_loop = 10 # інтервал перевірки нових повідомлень про повітряні тривоги в секундах
        self.bot = telebot.TeleBot(os.getenv('TELEGRAM_TOKEN'))
        self.url_json_data_with_channel = os.getenv('JSON_SOURCE_URL')
        self.keywords_for_search_alerts = []
        self.keyword_air_start = 'Повітряна тривога'
        self.keyword_air_end = 'Відбій тривоги'
        self.message_air_alarm_start = '❗️❗️ ПОВІТРЯНА ТРИВОГА 🐔✈️🚀 ({keyword}), Пройдіть в найблище УКРИТТЯ 🛖 {date}\nКількість тривог за сьогодні: {la}.'
        self.message_air_alarm_end = '🟢 ВІДБІЙ ПОВІТРЯНОЇ ТРИВОГИ {date} 😃🌤.\nТривалість повітряної тривоги {dur}.'
        self.chat_id = os.getenv('CHAT_ID')
        self.data_channel = {}
        self.messages = []
        self.connection = sqlite3.connect(os.getenv('AIR_ALERT_DB'), check_same_thread=False)
        self.db_cursor = self.connection.cursor()
        self.last_time_stamp = 0
        self._work = True
        self.screen = ScreenAirAlerts(self.chat_id, os.getenv('TELEGRAM_TOKEN'))
        self.queue = queue
        self.air_s = AirSound()
        self.air_alarm_map_path = r'C:\Users\38093\Documents\py\air_alarm_map\map.png'
        
        self.init_table_for_db()


    def filter_symbol_for_city_tag(self, tag: str) -> str:
        return tag.replace("#", '').replace('_', ' ')


    def add_city_tag(self, city_tag: str) -> None:
        ''' Встановлює тег для пошуку тривог в каналі Telegram https://t.me/air_alert_ua '''
        self.keywords_for_search_alerts.append(city_tag)


    def save_log_to_file(self, file_path = None) -> None:
        if file_path is None:
            logger.add(self.log_file)
        else:
            logger.add(file_path)

    
    def save_log_file(self):
        root_dir = os.path.dirname(__file__)
        logs_dir = os.path.join(root_dir, 'logs')
        if not os.path.isdir(logs_dir) :
            os.mkdir(logs_dir)
        file_path_log = os.path.join(logs_dir, self.log_file)
        logger.add(file_path_log)


    def get_string_date(self, time_unix: int, format = '') -> str:
        date = datetime.datetime.fromtimestamp(time_unix)
        if format == '':
            format = "(%d.%m/%H:%M)"
        return date.strftime(format)


    def get_string_duration_alarm(self, duration_interval: int) -> str:
        duration = {
            "days": 0,
            "hours": 0,
            "minutes": 0
        }
        # duration_interval = int(duration_interval)
        if duration_interval <= 60:
            duration['minutes'] = 1
        elif duration_interval > 60:
            a = duration_interval % 60
            b = int( (duration_interval - a) / 60)
            if b < 60:
                duration['minutes'] = b
            else:
                am = b % 60
                bh = int( (b - am) / 60 )
                duration['minutes'] = am
                duration['hours'] = bh
        h = duration['hours']
        m = duration['minutes']
        return f'{h}год. {m}хв'


    def send_message(self, text: str):
        self.bot.send_message(self.chat_id, text)

    def send_error(self, text: str):
        text = 'Повітряні тривоги помилка: \n' + text
        logger.debug("Send error %s" % text)
        try:
            self.bot.send_message("@tester199922", text)
        except:
            logger.error(f"Неможливо відправити помилку {text}")


    def get_all_air_alerts_from_today(self) -> list:
        list_alerts = []
        format_time = '%d.%m.$Y'
        today_date = strftime(format_time)
        q = f'SELECT * FROM \'alert\' where message like "%{self.keyword_air_end}%" order by time_start desc'
        for row in self.db_cursor.execute(q):
            if self.get_string_date(row[0], format_time) == today_date:
                list_alerts.append(row)
        return list_alerts

    def _send_map_image(self, msg_text):
        sleep(15)
        logger.info("Send air alarm map")
        self.bot.send_photo(self.chat_id, open(self.air_alarm_map_path, 'rb'), msg_text)

    def air_start(self, message,  msg_text: str):
        self.last_time_stamp = int( message['date'])
        set_last_time(self.last_time_stamp)
        self.queue.enable_active()
        # logger.info("Створення скріна відімкнено!")
        threading.Thread(target=self._send_map_image, args=( msg_text, )).start()
        # try:
        #     self.screen.shot_screen()
        #     self.screen.send_scren_to_telegram(msg_text)
        # except:
        #     logger.error('Помилка відправки скріна...')
        

    def air_end(self, message) -> str:
        if  get_last_time() == 0:
            logger.error('Помилка вирахування часу тривоги, невірний останній таймштамп!')
            return ''
        date_end = message['date']
        q = f'UPDATE "alert" SET time_end = {date_end} WHERE time_start = {self.last_time_stamp}'
        self.db_cursor.execute(q)
        self.connection.commit()
        duration_interval = int(message['date']) - get_last_time()
        set_last_time(0)
        self.last_time_stamp = 0
        return self.get_string_duration_alarm(duration_interval)


    def send_start_or_end_air_alarm(self, message) -> None:
        if re.search(self.keyword_air_start, message['message']):
            alerts_from_today = self.get_all_air_alerts_from_today()
            len_alerts = len(alerts_from_today) + 1
            kw = message['keyword'].replace('#', '').replace('_', ' ')
            mess = self.message_air_alarm_start.format(keyword=kw,la=len_alerts, date=self.get_string_date(message['date']))
            self.send_message( mess )
            logger.info(mess)
            self.air_start(message, mess)
            self.air_s.alert_sound(start=True)
        if re.search(self.keyword_air_end, message['message']):
            dur = self.air_end(message)
            msg = self.message_air_alarm_end.format(dur=dur, date=self.get_string_date(message['date']))
            logger.info(msg)
            self.send_message(msg)
            self.air_s.alert_sound(stop=True)
            self.queue.start_q_sender()


    def init_table_for_db(self):
        sql = 'CREATE TABLE if not exists alert  (time_start int not NULL primary key, message text, time_end int, location text)'
        self.db_cursor.execute(sql)
        self.connection.commit()


    def get_data_channell(self):
        if not is_network():
            self.messages = []
            logger.error("No connection to network!")
            return
        try:
            req = get(self.url_json_data_with_channel)
            if req.status_code == 200:
                self.data_channel = req.json()
                
                if type(self.data_channel.get('messages')) is list:
                    self.messages = self.data_channel.get('messages')
                    # logger.debug(self.messages)
                else:
                    logger.error('Немає повідомлень')
                    self.send_error('Немає повідомлень')
            else:
                logger.error(req)
                self.send_error(f'невідома помилка, код: {req.status_code}')
        except:
            logger.error('Помилка інтернету, втрата зв\'язку.')
            self.send_error('Помилка інтернету, втрата зв\'язку.')


    def get_messages_for_search_keywords(self) -> list:
        self.get_data_channell()
        messages = []
        for keyword in self.keywords_for_search_alerts:
            messages_bufer = []
            for message in self.messages:
                if type(message['message']) is not(str):
                    continue
                if re.search(keyword, message['message']):
                    message['keyword'] = keyword
                    messages_bufer.append(message)
            messages += messages_bufer
        return messages


    def execute_scan_and_send_air_alarm(self):
        for alert in self.get_messages_for_search_keywords():
            last_message = self.get_last_alert()
            if last_message is None or alert['date'] > last_message[0]:
                self.send_start_or_end_air_alarm(alert)
                if self.is_unique_message(alert):
                    self.save_alert_to_db(alert)


    def save_alert_to_db(self, message):
        kw = self.filter_symbol_for_city_tag(message['keyword'])
        query = "INSERT INTO alert values (?, ?, ?, ?)"
        data_tuple = (message['date'], message['message'], 0, kw)
        self.db_cursor.execute(query, data_tuple)
        self.connection.commit()


    def is_unique_message(self, message) -> bool:
        self.db_cursor.execute('select * from alert where time_start = '+ str( message['date'] ) )
        if self.db_cursor.fetchone() is None:
            return True
        else:
            return None


    def get_last_alert(self):
        self.db_cursor.execute('select * from alert order by time_start desc' );
        return self.db_cursor.fetchone()


    def run(self):
        self._work = True


    def terminate(self):
        self._work = False


    def loop(self):
        try:
            logger.info(f"Початок роботи сканеру повітряних тривог. Канал {self.chat_id}, таймаут: {self.timeout_loop} секунд.")
            logger.info(self.keywords_for_search_alerts)
            while True:
                if not self._work:
                    logger.info('Повідомлення про тривоги вимкнено!')
                    break
                self.execute_scan_and_send_air_alarm()
                sleep(self.timeout_loop)
        except KeyboardInterrupt:
            logger.info("Програму зупинено.")


if __name__ == "__main__":
    air_alerts = AirAlarmHorodische()
    air_alerts.save_log_to_file()
    air_alerts.add_city_tag('#Черкаська_область')
    air_alerts.add_city_tag('Городищенська_територіальна_громада')
    air_alerts.loop()
    