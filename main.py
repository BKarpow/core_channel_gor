import math
from air import AirAlarmHorodische
from commendant import CommendantTime
from weather import HorWBot
from cron import CronDemon
from rsswatch import RssNewsSender
from loguru import logger 
import threading
import os
import time
import telebot

# log file for core
logs_dir = os.path.join(os.path.dirname(__file__), 'core_logs')
if not os.path.isdir(logs_dir):
    os.mkdir(logs_dir)
log_file_core = os.path.join(logs_dir, 'core_log-{time}.log')
logger.add(log_file_core)
logger.info('Початок роботи сервісів для каналу ' + os.getenv('CHAT_ID'))


# rss
rss = RssNewsSender()
rss.save_log_file()


# cron
cron = CronDemon()
cron.start_logger()



# Weather
w = HorWBot()
w.save_log_file()



# commendant
comendant = CommendantTime()


# air 
air = AirAlarmHorodische()
air.save_log_file()
air.add_city_tag('#Черкаська_область')
air.add_city_tag('Городищенська_територіальна_громада')


# help info
def help():
    commands = [
        ('start', 'Запуск всіх модулів.'),
        ('start-air', 'Запуск повідомлень про тривогу.'),
        ('start-com', 'Запуск повідомлень про комендантську годину.'),
        ('start-wea', 'Запуск повідомлень про погоду.'),
        ('start-cron', 'Запуск крону для відображення новини.'),
        ('start-rss', 'Запуск відображення новини.'),
        ('stop', 'Зупиняє всі модулі.'),
        ('stop-air', 'Зупиняє повідомленя про тривогу.'),
        ('stop-com', 'Зупиняє повідомленя про комендантську годину.'),
        ('stop-wea', 'Зупиняє повідомленя про погоду.'),
        ('stop-cron', 'Зупиняє крон.'),
        ('stop-rss', 'Зупиняє сканування новин.'),
        ('status', 'Показує статуси модулдів.'),
        ('exit', 'Вийти із сервісу.'),
    ]
    for c in commands:
        print(f'{c[0]} - {c[1]}')


status_modules = {
    'AirAlertUa': False,
    'RssNewsSender': False,
    'ComendantAlert': False,
    'WeatherAlert': False,
    'CronAlert': False,
}


def get_status_modul(status: bool) -> str:
    if status:
        return 'Увімкнено'
    else:
        return 'Вимкнено'


def show_status():
    print('Статус модулів:')
    print()
    for m, s in  status_modules.items():
        s = get_status_modul(s)
        print(f'{m} - {s}.')


while True:
    comm = input("Command>")
    match comm:
        case 'status' | 'list' | 'info':
            show_status()
        case 'start-rss':
            rss.run()
            threading.Thread(target=rss.loop).start()
            status_modules['RssNewsSender'] = True
        case 'start-cron':
            cron.run()
            threading.Thread(target=cron.loop).start()
            status_modules['CronAlert'] = True
        case 'start-wea':
            w.run()
            threading.Thread(target= w.loop).start()
            logger.info('Повідомляти про погоду - запущений.')
            status_modules['WeatherAlert'] = True
        case 'start-com':
            comendant.run()
            threading.Thread(target=comendant.loop).start()
            logger.info('Повідомляти про ком. годину - запущений.')
            status_modules['ComendantAlert'] = True
        case 'start-air':
            air.run()
            threading.Thread(target=air.loop).start()
            logger.info('Сканер повітряних тривог - запущений.')
            status_modules['AirAlertUa'] = True
        case 'start' | 'run' | 'go':
            rss.run()
            threading.Thread(target=rss.loop).start()
            status_modules['RssNewsSender'] = True
            air.run()
            threading.Thread(target=air.loop).start()
            logger.info('Сканер повітряних тривог - запущений.')
            comendant.run()
            threading.Thread(target=comendant.loop).start()
            logger.info('Повідомляти про ком. годину - запущений.')
            w.run()
            threading.Thread(target= w.loop).start()
            logger.info('Повідомляти про погоду - запущений.')
            
            status_modules['AirAlertUa'] = True
            status_modules['ComendantAlert'] = True
            status_modules['WeatherAlert'] = True
        case 'stop':
            rss.terminate()
            status_modules['RssNewsSender'] = False
            comendant.terminate()
            logger.info('Повідомляти про ком. годину - зупинено.')
            air.terminate()
            logger.info('Сканер повітряних тривог - зупинено.')
            w.terminate()
            logger.info('Повідомляти про погоду - зупинено.')
           
            status_modules['AirAlertUa'] = False
            status_modules['ComendantAlert'] = False
            status_modules['WeatherAlert'] = False
        case 'stop-rss':
            rss.terminate()
            status_modules['RssNewsSender'] = False
        case 'stop-cron':
            cron.terminate()
            logger.info('Крон - зупинено.')
            status_modules['CronAlert'] = False
        case 'stop-air':
            air.terminate()
            logger.info('Сканер повітряних тривог - зупинено.')
            status_modules['AirAlertUa'] = False
        case 'stop-com':
            comendant.terminate()
            logger.info('Повідомляти про ком. годину - зупинено.')
            status_modules['ComendantAlert'] = False
        case 'stop-wea':
            w.terminate()
            logger.info('Повідомляти про погоду - зупинка...')
            status_modules['WeatherAlert'] = False
        case 'help' | '?' | '-h' | '/?':
            help()
        case 'ex' | 'close' | 'exit':
            logger.info('Вихід із програми.')
            break
        case _:
            continue