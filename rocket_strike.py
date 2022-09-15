from qu import SmartSender
from requests import get
from pathlib import Path
from loguru import logger
from os import getenv
from time import sleep


class RocketStrikeInformer:

    def __init__(self, sender: SmartSender) -> None:
        self.sender = sender
        self.url_data = getenv("JSON_SOURCE_URL")
        self.timeout_getting_data = 35
        self.last_rs_file = Path("last_rs_timestamp.txt")
        self._work = True

    def run(self):
        logger.info("Working start")
        self._work = True

    def terminate(self):
        logger.info("Working stop")
        self._work = False

    def get_last_timestamp(self) -> int:
        if not self.last_rs_file.exists():
            with open(self.last_rs_file.absolute(), 'w') as f:
                f.write('0')
            return 0
        else:
            with open(self.last_rs_file.absolute(), 'r') as f:
                res = f.read()
            return int(res)

    def set_last_timestamp(self, timestamp: int) -> None:
        with open(self.last_rs_file.absolute(), 'w') as f:
                f.write(str(timestamp))
    
    def get_data(self) -> dict:
        data = {
            "active": False,
            "msg": "",
            "id": 0
        }
        try:
            res = get(self.url_data)
            if res.status_code != 200:
                logger.error("Error network: {res.status_code}")
                return data
            res = res.json()
            if res.get("rocketStrike") == None:
                logger.error("Invalid JSON data response.")
                return data
            return res["rocketStrike"]
        except:
            logger.error("Error in getting JSON data.")
            return data

    def is_unique_warning(self, id: int) -> bool:
        last_id = self.get_last_timestamp()
        if id > last_id:
            self.set_last_timestamp(id)
            return True
        return False
    
    def execute(self) -> None:
        data = self.get_data()
        if data["active"] and self.is_unique_warning(data["id"]):
            logger.info("Rocket strike WARNING!!!!")
            self.sender.send_text_now(data["msg"])

    def loop(self):
        logger.info("Start alert sender for rocket strike warning.")
        while True:
            if not self._work:
                logger.info("Rocket strike warning - stopped!")
                break
            self.execute()
            sleep(self.timeout_getting_data)
