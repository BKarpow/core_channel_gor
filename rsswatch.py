from rss_parser import Parser
from loguru import logger
import requests as req

import datetime
import re
import telebot
import time
import os
import sqlite3
from qu import SmartSender

class RssNewsSender:
    def __init__(self, sender: SmartSender) -> None:
        self._work = True
        self.log_file_name = 'rss_news.log'
        self.log_file_name_debug = 'rss_news_debug.log'
        self.log_file_name_error = 'rss_news_error.log'
        self.bot = telebot.TeleBot(os.getenv('TELEGRAM_TOKEN'))
        self.chat_id = os.getenv('CHAT_ID')
        self.db_connect = sqlite3.connect(os.getenv('NAME_RSS_DB'), check_same_thread=False)
        self.db_cursor = self.db_connect.cursor()
        self.rss_xml_source_url = os.getenv('RSS_XML_SOURCE')
        self.format_rss_date = '%a, %d %b %Y %H:%M:%S %z'
        self.rss_feed = None
        self.timeout_loop = 300
        self.sender = sender

        self.init_table_for_db()


    def run(self) -> None:
        self._work = True


    def terminate(self) -> None:
        self._work = False


    def clear_html_nbsp(self, text: str) -> str:
        text = re.sub(r'\n+', '\n', text)
        return re.sub(r'&[a-z0-9]+;', '', text)


    @logger.catch
    def get_string_date(self, time_unix: int, format = '') -> str:
        date = datetime.datetime.fromtimestamp(time_unix)
        if format == '':
            format = "%d.%m.%Y/%H:%M"
        return date.strftime(format)


    @logger.catch
    def _convert_date_str_to_unix(self, date: str) -> int:
        return int( time.mktime(time.strptime(date, self.format_rss_date)))


    @logger.catch
    def init_table_for_db(self):
        sql = '''CREATE TABLE if not exists news  (
            id integer primary key,
            time_publick int not null,
            title varchar(250) NOT NULL,
            description text,
            url varchar(250) NOT NULL,
            dt varchar(25)
        )'''
        self.db_cursor.execute(sql)
        self.db_connect.commit()


    @logger.catch
    def insert_news_to_db(self, news) -> None:
        q = 'INSERT INTO news (time_publick, title, description, url, dt) VALUES (?, ?, ?, ?, ?)'
        date_unix = self._convert_date_str_to_unix(news.publish_date)
        data_news = (
            date_unix,
            news.title,
            news.description,
            news.link,
            self.get_string_date(date_unix)
        )
        self.db_cursor.execute(q, data_news)
        self.db_connect.commit()


    @logger.catch
    def is_unique_news(self, news) -> bool:
        date_public = self._convert_date_str_to_unix(news.publish_date)
        q = f'SELECT time_publick FROM news WHERE time_publick = {date_public}'
        self.db_cursor.execute(q)
        if self.db_cursor.fetchone() is None:
            return True
        else:
            return False


    @logger.catch
    def save_log_file(self) -> None:
        root_dir = os.path.dirname(__file__)
        logs_dir = os.path.join(root_dir, 'logs')
        if not os.path.isdir(logs_dir) :
            os.mkdir(logs_dir)
        file_path_log = os.path.join(logs_dir, self.log_file_name)
        file_path_log_d = os.path.join(logs_dir, self.log_file_name_debug)
        file_path_log_e = os.path.join(logs_dir, self.log_file_name_error)
        logger.add(file_path_log, level='INFO', rotation="10 kB", compression="zip")
        logger.add(file_path_log_d, level='DEBUG', rotation="100 kB", compression="zip")
        logger.add(file_path_log_e, level='ERROR', rotation="10 kB", compression="zip")
    

    @logger.catch
    def get_data_xml(self) -> str:
        try:
            resp = req.get(self.rss_xml_source_url)
            if resp.status_code == 200:
                # logger.debug('XML Отримано!')
                return resp.content
            else:
                logger.error(resp)
        except:
            logger.error('Помилка, немає інтернету!')

    @logger.catch
    def parse_rss(self):
        xml = self.get_data_xml()
        if xml != None:
            parser = Parser(xml=xml)
            self.rss_feed = parser.parse()
        else:
            logger.error('Нмає даних xml.')


    @logger.catch
    def execute_rss_news(self) -> None:
        self.parse_rss()
        for news in self.rss_feed.feed:
            if self.is_unique_news(news):
                self.insert_news_to_db(news)
                mess = self.template_news_for_telegram(news)
                self.send_message(mess)
                logger.info(mess)
    
    
    @logger.catch  
    def send_message(self, text: str):
        # self.bot.send_message(self.chat_id, text)
        self.sender.send('text', text)

    
    @logger.catch
    def template_news_for_telegram(self, news) -> str:
        dt = self.get_string_date(self._convert_date_str_to_unix(news.publish_date))
        title = self.clear_html_nbsp(news.title)
        des = self.clear_html_nbsp(news.description)
        return f'''{dt}
{title}
{des}

{news.link}
'''


    @logger.catch
    def loop(self):
        logger.info(f'Початок роботи сканеру новини, на канал {self.chat_id}')
        while True:
            if not self._work:
                logger.info('Сканер новин зупинено!')
                break
            self.execute_rss_news()
            time.sleep(self.timeout_loop)

if __name__ == "__main__":
    news = RssNewsSender()
    news.save_log_file()
    # news.loop()
    # logger.debug(news.rss_feed)


