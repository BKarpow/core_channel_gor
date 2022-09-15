from dataclasses import dataclass
from requests import get
from loguru import logger
from datetime import datetime

import os
import telebot
import time

from qu import SmartSender


def get_time() -> int:
	''' Повертає часову мітку у форматі секунд unix '''
	d = time.strftime('%d.%m.%Y %H:%M:%S')
	return  int( time.mktime(time.strptime(d,"%d.%m.%Y %H:%M:%S")) )


class HorWBot:
    def __init__(self, sender: SmartSender) -> None:
        self.log_file = 'weather_{time}.log'
        self.API_KEY = os.getenv('W_API_KEY')
        self.API_URL = os.getenv('W_URL')
        self.bot = telebot.TeleBot(os.getenv('TELEGRAM_TOKEN'))
        self.CHAT_ID = os.getenv('CHAT_ID')
        # self.CHAT_ID = "@tester19992"
        self.time_send = '08:10'
        self.timeout_loop = 0.65
        self.w_data = {}
        self.current_w = {}
        self.hourly_w = {}
        self.do_send = True
        self.sender = sender
        self._work = True

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

    def send_message(self, text: str) -> None:
        logger.info(f'Відправлено повідомлення Telgram в чат {self.CHAT_ID}')
        self.sender.send('text', text)

    def get_url_for_api_request(self) -> str:
        params = {
            "exclude": "daily",
            "lat": "49.285",
            "lon": "31.445",
            "units": "metric",
            "appid": self.API_KEY,
            "lang": "ua"
        }
        http_query = "&".join([k+"="+v for k,v in params.items()])
        return f'{self.API_URL}?{http_query}'

    def get_api_data(self):
        try:
            logger.debug(self.get_url_for_api_request())
            req = get(self.get_url_for_api_request())
            if req.status_code != 200:
                logger.error(req)
            self.w_data = req.json()
            logger.info("Дані про погоду отримано успішно!")
        except:
            logger.error('Помилка інтернету...')

    def get_date(self,format: str, unix_time: int) -> str:
        return datetime.fromtimestamp(unix_time).strftime(format)

    def get_weather(self) -> None:
        self.get_api_data()
        if self.w_data.get('current') != None:
            self.current_w = self.w_data.get('current')
        else:
            logger.error("Не отримано поголу на поточний час.")
        if self.w_data.get('hourly') != None:
            self.hourly_w = self.w_data.get('hourly')
        else:
            logger.error("Не отримано прогноз погоди.")

    def template(self, item, current = True) -> str:
        if current:
            dt = self.get_date("(%d/%m) %H:%M", item['dt'])
        else:
            dt = self.get_date("%H:%M", item['dt'])
        temp = int( item['temp'])
        feels_like = int( item['feels_like'])
        # if current:
        #     sunrise = self.get_date("%H:%M",item['sunrise'])
        #     sunset = self.get_date("%H:%M", item['sunset'])
        clouds = item['clouds']
        wind_speed = int( item['wind_speed'] )
        wind_deg = self.get_mark_for_wind_angle(item['wind_deg'])
        weather_info = self.get_info_weather(item['weather'][0]['id'])
        weather_title = weather_info['title']
        weather_description = weather_info['description']
        if current:
            t = f"""
Дата: {dt}:
Температура 🌡 {temp}℃,
відчуваєтся як: 🌡 {feels_like}℃.
Вітер: 🪁 {wind_deg} {wind_speed}м/с.
{weather_title}
"""
        else: 
            t = f'''Прогноз на {dt}:
Температура 🌡 {temp}℃,
відчуваєтся як: 🌡 {feels_like}℃.
Вітер: 🪁 {wind_deg} {wind_speed}м/с.
{weather_title}
'''
        return t

    def get_current(self) -> str:
        return self.template(self.current_w)

    def get_today_weather(self) -> list:
        todays = []
        format = '%d'
        today_date = time.strftime(format)
        for h in self.hourly_w:
            if self.get_date(format, h['dt']) == today_date and int(self.get_date('%H', h['dt'])) % 2 == 0:
                todays.append(h)
        return todays

    def get_maximum_temp(self, w: list) -> int:
        ''' Метод повертатиме максимальну температуру з прогнозу '''
        mx_temp = 0
        for item in w:
            temp = int(item['temp'])
            if temp > mx_temp:
                mx_temp = temp
        return mx_temp

    def get_sun_times(self) -> tuple:
        return self.get_date("%H:%M", self.current_w['sunrise']), self.get_date("%H:%M",self.current_w['sunset'])

    def get_manimum_temp(self, w: list) -> int:
        ''' Метод повертатиме мінімальну температуру з прогнозу '''
        mn_temp = self.get_maximum_temp(w)
        for item in w:
            temp = int(item['temp'])
            if temp < mn_temp:
                mn_temp = temp
        return mn_temp

    def get_tomorow_weather(self) -> list:
        todays = []
        format = '%d'
        today_date = time.strftime(format)
        for h in self.hourly_w:
            tm_date = datetime.fromtimestamp(get_time() + 86400).strftime(format)
            if self.get_date(format, h['dt']) == tm_date and int(self.get_date('%H', h['dt'])) % 2 == 0:
                todays.append(h)
        return todays

    def get_today(self) -> str:
        w = self.get_today_weather()
        mx = self.get_maximum_temp(w)
        mn = self.get_manimum_temp(w)
        res = f"Максимальна: 🌡{mx}℃, мінімальна: 🌡{mn}℃\n"
        res += "\n".join([self.template(x, False) for x in w])
        return res

    def get_tomorow(self):
        w = self.get_tomorow_weather()
        dt = dict()
        for item in w:
            try:
                dt[item['weather'][0]['id']] += 1
            except KeyError:
                dt[item['weather'][0]['id']] = 1
        mx = 0
        mx_id = 0
        for id, count in dt.items():
            if count > mx:
                mx = count
                mx_id = int(id)
        w_desc = self.get_info_weather(mx_id)
        mx = self.get_maximum_temp(w)
        mn = self.get_manimum_temp(w)
        res = f"Максимальна: 🌡{mx}℃, мінімальна: 🌡{mn}℃\n"
        res += w_desc['title'] + "\n"
        # res += "\n".join([ self.template(x, True) for x in w] )
        return res

    def get_info_weather(self, weather_id:int) -> dict:
        data_trans = [
            {"id": 200, "title": "Гроза 🌩💧", "description": "гроза з невеликим дощем", "icon": ""},
            {"id": 201, "title": "Гроза 🌩💧💧", "description": "гроза з дощем", "icon": ""},
            {"id": 202, "title": "Гроза 🌩💧💧💧", "description": "гроза з сильним дощем", "icon": ""},
            {"id": 210, "title": "Гроза 🌩", "description": "легка гроза", "icon": ""},
            {"id": 211, "title": "Гроза 🌩🌩", "description": "Гроза", "icon": ""},
            {"id": 212, "title": "Гроза 🌩🌩🌩", "description": "сильна гроза", "icon": ""},
            {"id": 221, "title": "Гроза 🌩🌩🪁", "description": "гроза з поривами", "icon": ""},
            {"id": 230, "title": "Гроза 🌩🌧", "description": "гроза з дрібним дощем", "icon": ""},
            {"id": 231, "title": "Гроза 🌩🌧🌧", "description": "гроза з дождем", "icon": ""},
            {"id": 232, "title": "Гроза 🌩🌧🌧🌧", "description": "гроза з сильною дождем", "icon": ""},
            {"id": 300, "title": "Моросить ⛆", "description": "дрібний дощ", "icon": "09d"},
            {"id": 301, "title": "Моросить ⛆", "description": "Моросить", "icon": "09d"},
            {"id": 302, "title": "Моросить ⛆⛆", "description": "сильний дрібний дощ", "icon": "09d"},
            {"id": 310, "title": "Моросить ⛆⛆", "description": "невеликий дрібний дощ", "icon": "09d"},
            {"id": 311, "title": "Моросить ⛆🌧", "description": "дощ", "icon": "09d"},
            {"id": 312, "title": "Моросить ⛆🌧🌧", "description": "сильний дощ", "icon": "09d"},
            {"id": 313, "title": "Моросить ⛆🌧", "description": "дощ і мряка", "icon": "09d"},
            {"id": 314, "title": "Моросить ⛆🌧🌧🌧", "description": "сильний дощ і мряка", "icon": "09d"},
            {"id": 321, "title": "Моросить ⛆🌧", "description": "дощова мряка", "icon": "09d"},
            {"id": 500, "title": "Можливий дощ 💧", "description": "легкий дощ", "icon": "10d"},
            {"id": 501, "title": "Дощ поиірний 💧", "description": "помірний дощ", "icon": "10d"},
            {"id": 502, "title": "Дощ гарний 💧💧", "description": "сильний дощ", "icon": "10d"},
            {"id": 503, "title": "Дощ (як з відра) 💧💧💧", "description": "дуже сильний дощ", "icon": "10d"},
            {"id": 504, "title": "Дощара  💧💧💧💧", "description": "екстремальний дощ", "icon": "10d"},
            {"id": 511, "title": "Дощ 💧❄", "description": "холодний дощ", "icon": "13d"},
            {"id": 520, "title": "Дощ 💧💧", "description": "невеликий інтенсивний дощ ", "icon": "09d"},
            {"id": 521, "title": "Дощ 💧💧", "description": "дощ", "icon": "10d"},
            {"id": 522, "title": "Дощ 💧💧💧", "description": "сильний зливовий дощ", "icon": "10d"},
            {"id": 531, "title": "Дощ 💧", "description": "поривистий дощ", "icon": "10d"},
            {"id": 600, "title": "Сніг 🌨", "description": "невиликий сніг", "icon": "10d"},
            {"id": 601, "title": "Сніг 🌨", "description": "сніг", "icon": "10d"},
            {"id": 602, "title": "Сніг 🌨🌨🌨", "description": "сильний сніг", "icon": "10d"},
            {"id": 611, "title": "Сніг 🌨💧", "description": "мокрий сніг", "icon": "10d"},
            {"id": 612, "title": "Сніг 🌨💧", "description": "Легкий мокрий сніг", "icon": "10d"},
            {"id": 613, "title": "Сніг 🌨🌨❄", "description": "Зливовий сніг", "icon": "10d"},
            {"id": 615, "title": "Сніг 💧🌨", "description": "Невеликий дощ і сніг", "icon": "10d"},
            {"id": 616, "title": "Сніг 🌨💧❄", "description": "Дощ і сніг", "icon": "10d"},
            {"id": 620, "title": "Сніг 💧🌨", "description": "Невеликий дощ сніг", "icon": "10d"},
            {"id": 621, "title": "Сніг 💧🌨", "description": "Дощовий сніг", "icon": "10d"},
            {"id": 622, "title": "Сніг 💧🌨🌨🌨", "description": "Сильний зливовий сніг", "icon": "10d"},
            {"id": 701, "title": "Туман", "description": "Туман", "icon": "50d"},
            {"id": 711, "title": "Дим", "description": "Дим", "icon": "50d"},
            {"id": 721, "title": "Димка", "description": "Димка", "icon": "50d"},
            {"id": 731, "title": "Пил", "description": "Пил", "icon": "50d"},
            {"id": 741, "title": "Туман", "description": "Туман (fog)", "icon": "50d"},
            {"id": 751, "title": "Пісок", "description": "Пісок", "icon": "50d"},
            {"id": 761, "title": "Пил", "description": "Пил", "icon": "50d"},
            {"id": 762, "title": "Зола", "description": "вулканічний попіл", "icon": "50d"},
            {"id": 771, "title": "Шквал", "description": "Шквал", "icon": "50d"},
            {"id": 781, "title": "Торнадо 🌪", "description": "Торнадо", "icon": "50d"},
            {"id": 800, "title": "🔅", "description": "Чисте небо", "icon": "50d"},
            {"id": 801, "title": "🌤", "description": "мало хмар: 11-25%", "icon": "50d"},
            {"id": 802, "title": "🌤☁", "description": "невелика хмарність: 25-50%", "icon": "50d"},
            {"id": 803, "title": "🌤☁☁", "description": "розбита хмарність: 51-84%", "icon": "50d"},
            {"id": 804, "title": "☁☁☁", "description": "хмарність: 85-100%", "icon": "50d"}  
        ]
        for t in data_trans:
            if t['id'] == weather_id:
                return t
        logger.error(f'Немає перекладу для цього {weather_id}')
        return {"id": 804, "title": "Невідомо", "description": "Невідомо", "icon": "50d"}

    def get_mark_for_wind_angle(self, wind_angle:int) -> str:
        wind_angle = int( wind_angle )
        if wind_angle > 0 and wind_angle < 90:
            return f"Пн-Сх"
        elif wind_angle > 90 and wind_angle < 180:
            return f"Пд-Сх"
        elif wind_angle > 180 and wind_angle < 240:
            return f"Пд-Зх"
        elif wind_angle > 240 and wind_angle < 360:
            return f"Пн-Зх"
        elif wind_angle == 0:
            return "Пн"
        elif wind_angle == 90:
            return "Сх"
        elif wind_angle == 180:
            return "Пд"
        elif wind_angle == 240:
            return "Зх"
        else:
            return f"ХЗ?"

    def send_waather(self) -> None:
        mess = 'Доброго ранку 💟 Городище, трішки погоди 🔆\n'
        sunrise, sunset = self.get_sun_times()
        mess += f"\n🔆🔆🔆 cхід у {sunrise}, захід у {sunset}\n"
        # mess += self.get_current()
        mess += self.get_today()
        mess += "\n\n Завтра "
        mess += datetime.fromtimestamp(get_time() + 86400).strftime("%d.%m.%Y") + "\n"
        mess += self.get_tomorow()
        mess += '\n\nВдалого Вам дня ☑️‼️\n\n#погода'
        self.send_message(mess)

    def run(self):
        self._work = True

    def terminate(self):
        self._work = False

    def loop(self):
        logger.info(f'Почвток роботи боту прогнозу погоди для каналу {self.CHAT_ID}, спрацьовує у {self.time_send}, оновлюєтся кожні {self.timeout_loop} секунди.')
        # self.get_weather()
        # self.send_waather()
        m = 0
        try:
            while True:
                if not self._work:
                    logger.info('Відправлення прогнозу вимкнено')
                    break
                if time.strftime('%H:%M:%S') == self.time_send + ':00':
                    self.get_weather()
                    self.send_waather()
                time.sleep(self.timeout_loop)
        except KeyboardInterrupt:
            logger.info('Програму зупинено.')
        except:
            logger.error('Помилка в циклі loop!')


if __name__ == "__main__":
    bot = HorWBot()
    bot.save_log_to_file()
    bot.loop()

