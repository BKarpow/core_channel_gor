import sqlite3
import os
import time
import telebot
from os import path
from loguru import logger


class SmartSender:
    def __init__(self, token: str, chat_id: str) -> None:
        self.sleep_timeout_send = 300
        self.chat_id = chat_id
        self.bot = telebot.TeleBot(token, parse_mode='html')
        self.connect = sqlite3.connect(
            path.join(path.dirname(__file__), 'queue.db'),
            check_same_thread=False
         )
        self.cursor = self.connect.cursor()
        self._active = False

        self._create_queue_table()

    def _create_queue_table(self) -> None:
        self.cursor.execute(""" CREATE TABLE IF NOT EXISTS qq (
            type varchar(100) NOT NULL default 'text',
            path_file text,
            msg text
        ) """)
        self.connect.commit()

    def enable_active(self):
        logger.info('Enable Air alert status active!')
        self._active = True

    def disable_active(self):
        logger.info('Disable Air alert status not active!')
        self._active = False

    def is_active(self):
        return bool(self._active)

    def send_text(self, msg: str):
        if self.is_active():
            self._add_text_msg_to_q(msg)
        else:
            logger.info(f'Send text: {msg}')
            self.bot.send_message(self.chat_id, msg)

    def _add_text_msg_to_q(self, msg):
        q = 'INSERT INTO qq (type, msg) VALUES (?, ?)'
        self.cursor.execute(q, ('text', msg))
        self.connect.commit()
        logger.info(f'Save to q: {msg}')

    def send_photo(self, path_file: str, msg: str):
        if self.is_active():
            self._add_photo_msg_to_q(path_file, msg)
        else:
            with open(path_file, 'rb') as photo:
                self.bot.send_photo(self.chat_id, photo, caption=msg)
            logger.info(f'Send photo: {path_file}, caption: {msg}')
            
    def _add_photo_msg_to_q(self, path_file, msg):
        q = 'INSERT INTO qq (type, path_file, msg) VALUES (?, ?, ?)'
        self.cursor.execute(q, ('photo', path_file, msg))
        self.connect.commit()
        logger.info(f'Save to queue: file - {path_file}, caption: {msg}')

    def send_video(self, path_file: str, msg: str):
        if self.is_active():
            self._add_video_msg_to_q(path_file, msg)
        else:
            with open(path_file, 'rb') as photo:
                self.bot.send_video(self.chat_id, photo, caption=msg)
            logger.info(f'Send video: {path_file}, caption: {msg}')
            
    def _add_video_msg_to_q(self, path_file, msg):
        q = 'INSERT INTO qq (type, path_file, msg) VALUES (?, ?, ?)'
        self.cursor.execute(q, ('video', path_file, msg))
        self.connect.commit()
        logger.info(f'Save video to queue: file - {path_file}, caption: {msg}')

    def send(self, type, msg:str, path_file=None):
        match type:
            case 'text':
                self.send_text(msg)
            case 'photo':
                self.send_photo(path_file, msg)
            case 'video':
                self.send_video(path_file, msg)
            case _:
                logger.error(f'None type: {type}')

    def get_all_messages_from_q(self) -> list:
        q = "SELECT rowid, type, path_file, msg FROM qq ORDER BY rowid DESC"
        res = self.cursor.execute(q)
        return res.fetchall()

    def _remove_msg_from_q(self, rowid: int):
        self.cursor.execute(f'DELETE FROM qq WHERE rowid = {rowid}')
        self.connect.commit()
        logger.debug(f'Deleted msg in queue: rowid - {rowid}')

    def start_q_sender(self):
        self.disable_active()
        logger.info('Start sender of queue')
        for msg in self.get_all_messages_from_q():
            time.sleep(self.sleep_timeout_send)
            self.send(type=msg[1], path_file=msg[2], msg=msg[3])
            self._remove_msg_from_q(msg[0])
        logger.info('Sender stop: Queue - cleaning')




if __name__ == "__main__":
    pf = path.join(path.dirname(__file__), 'minute_mute.mp4')
    ms = 'Загальні бойові втрати противника з 24.02 по 08.09 (орієнтовно)'
    q = SmartSender('5234818902:AAG1OaZf1nw6aeiTVhO9XJB8TJCdrgu_QmA', '@tester199922')
    q.enable_active()
    q.send('video', ms + '1', pf)
    q.send('video', ms + '2', pf)
    q.send('video', ms + '3', pf)
    # q.send('photo', ms + '1', pf)
    # q.send('photo', ms + '2', pf)
    # q.send('photo', ms + '3', pf)
    # q.send('photo', ms + '4', pf)
    # q.send('text', 'Hi i  am string! 2')
    # q.send('text', 'Hi i  am string! 3')
    q.start_q_sender()