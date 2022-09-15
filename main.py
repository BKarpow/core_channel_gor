import math
from air import AirAlarmHorodische
from commendant import CommendantTime
from weather import HorWBot
from cron import CronDemon
from rsswatch import RssNewsSender
from loguru import logger
from losses import CombatLosses
from radiation import RadiationAlert
from parse_rad import RadInformer
from qu import  SmartSender
from rocket_strike import RocketStrikeInformer
import argparse
import threading
import os
import time
import telebot


parser = argparse.ArgumentParser(description="Команда для автозапуску")
parser.add_argument("-c", dest="comand", default=False, help='Вкажіть команду з якою запускати програму.')
args = parser.parse_args()


# log file for core
logs_dir = os.path.join(os.path.dirname(__file__), 'core_logs')
if not os.path.isdir(logs_dir):
    os.mkdir(logs_dir)
log_file_core = os.path.join(logs_dir, 'core_log-{time}.log')
logger.add(log_file_core)
logger.info('Початок роботи сервісів для каналу ' + os.getenv('CHAT_ID'))


# Smart Sender queue
queue = SmartSender(os.getenv('TELEGRAM_TOKEN'), os.getenv('CHAT_ID'))

# air 
air = AirAlarmHorodische(queue)
air.save_log_file()
air.add_city_tag('#Черкаська_область')
air.add_city_tag('Городищенська_територіальна_громада')

# Rocket strike
rocket = RocketStrikeInformer(queue)

# combat losses
combat_losses = CombatLosses(queue)


# rss
rss = RssNewsSender(queue)
rss.save_log_file()


# cron
cron = CronDemon()
cron.start_logger()



# Weather
w = HorWBot(queue)
w.save_log_file()



# commendant
comendant = CommendantTime(queue)


# Radioation alert
rad = RadiationAlert()
rad.regions.append('#Черкаська_область')
rad.regions.append('Городищенська_територіальна_громада')


# Radiation send level
rad_level = RadInformer(queue)

# help info
def help():
    commands = [
        ('start', 'Запуск всіх модулів.'),
        ('start-losses', 'Запуск повідомлень про бойові втрати.'),
        ('start-air', 'Запуск повідомлень про тривогу.'),
        ('start-com', 'Запуск повідомлень про комендантську годину.'),
        ('start-wea', 'Запуск повідомлень про погоду.'),
        ('start-cron', 'Запуск крону для відображення новини.'),
        ('start-rss', 'Запуск відображення новини.'),
        ('start-rad', 'Запуск відображення радіаційних та хімічних загроз.'),
        ('start-rad-level', 'Запуск інформера радіаційного рівні по місту.'),
        ('start-rock', 'Запуск інформера загрози ракетних ударів.'),
        ('stop', 'Зупиняє всі модулі.'),
        ('stop-air', 'Зупиняє повідомленя про тривогу.'),
        ('stop-com', 'Зупиняє повідомленя про комендантську годину.'),
        ('stop-wea', 'Зупиняє повідомленя про погоду.'),
        ('stop-cron', 'Зупиняє крон.'),
        ('stop-rss', 'Зупиняє сканування новин.'),
        ('stoo-losses', 'Зупинка повідомлень про бойові втрати.'),
        ('stop-rad', 'Запуск відображення радіаційних та хімічних загроз.'),
        ('stop-rad-level', 'Зупинка інформера радіаційного рівні по місту.'),
        ('stop-rock', 'Зупинка інформера загрози ракетних ударів.'),
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
    'CombatLosses': False,
    'RadiationAlert': False,
    'RadInformer': False,
    "RocketStrikeInformer": False
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

def start_module(module, status_name: str) -> None:
    global status_modules
    if not status_modules[status_name]:
        module.run()
        threading.Thread(target=module.loop).start()
        status_modules[status_name] = True
    else:
        logger.error(f"Модуль {status_name} вже запущено")


def stop_module(module, status_name: str) -> None:
    global status_modules
    if status_modules[status_name]:
        module.terminate()
        status_modules[status_name] = False
    else:
        logger.error(f"Модуль {status_name} вже зупинено!")


def start_all_modules():
    global status_modules
    start_module(combat_losses, 'CombatLosses')
    start_module(rss, 'RssNewsSender')
    start_module(air, 'AirAlertUa')
    start_module(comendant, 'ComendantAlert')
    start_module(w, 'WeatherAlert')
    start_module(rad, 'RadiationAlert')
    start_module(rad_level, 'RadInformer')
    start_module(rocket, "RocketStrikeInformer")


def stop_all_modules():
    global status_modules
    stop_module(rss, 'RssNewsSender')
    stop_module(comendant, 'ComendantAlert')
    stop_module(air, 'AirAlertUa')
    stop_module(w, 'WeatherAlert')
    stop_module(combat_losses, 'CombatLosses')
    stop_module(rad, 'RadiationAlert')
    stop_module(rad_level, 'RadInformer')
    stop_module(rocket, "RocketStrikeInformer")


if args.comand == 'all':
    start_all_modules()


while True:
    comm = input("Command>")
    match comm:
        case 'status' | 'list' | 'info':
            show_status()
        case "start-rock":
            start_module(rocket, "RocketStrikeInformer")
        case 'start-rad-level':
            start_module(rad_level, 'RadInformer')
        case 'start-rad':
            start_module(rad, 'RadiationAlert')
        case 'start-losses':
            start_module(combat_losses, 'CombatLosses')
        case 'start-rss':
            start_module(rss, 'RssNewsSender')
        case 'start-cron':
            start_module(cron, 'CronAlert')
        case 'start-wea':
            start_module(w, 'WeatherAlert')
        case 'start-com':
            start_module(comendant, 'ComendantAlert')
        case 'start-air':
            start_module(air, 'AirAlertUa')
        case 'start' | 'run' | 'go':
            start_all_modules()
        case 'stop':
            stop_all_modules()
        case 'stop-losses':
            stop_module(combat_losses, 'CombatLosses')
        case 'stop-rss':
            stop_module(rss, 'RssNewsSender')
        case 'stop-cron':
            stop_module(cron, 'CronAlert')
        case 'stop-air':
            stop_module(air, 'AirAlertUa')
        case 'stop-com':
            stop_module(comendant, 'ComendantAlert')
        case 'stop-wea':
            stop_module(w, 'WeatherAlert')
        case 'stop-rad':
            stop_module(rad, 'RadiationAlert')
        case 'stop-rad-level':
            stop_module(rad_level, 'RadInformer')
        case "stop-rock":
            stop_module(rocket, "RocketStrikeInformer")
        case 'help' | '?' | '-h' | '/?':
            help()
        case 'ex' | 'close' | 'exit':
            logger.info('Вихід із програми.')
            break
        case _:
            continue