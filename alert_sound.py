import winsound
import threading
import time
from pathlib import Path
from loguru import logger

class AirSound:
    def __init__(self) -> None:
        logger.info('Початок озвучки триаог на компі')
        self.path_wav_start = Path('air_start.wav')
        self.path_wav_stop = Path('air_stop.wav')
        self.start_hour = 6
        self.stop_hour = 21

    def _play(self, path_file):
        winsound.PlaySound(path_file, winsound.SND_FILENAME)

    def play_start(self):
        logger.info('Start audio wav start')
        self._play(str(self.path_wav_start.absolute()))
        logger.info("Stop plaing")

    def play_stop(self):
        logger.info('Start audio wav stop')
        self._play(str(self.path_wav_stop.absolute()))
        logger.info("Stop plaing")

    def thread_sound_start(self):
        threading.Thread(target=self.play_start).start()

    def thread_sound_stop(self):
        threading.Thread(target=self.play_stop).start()

    def alert_sound(self, start=False, stop=False):
        this_hour = int(time.strftime("%H"))
        if this_hour >= self.start_hour and this_hour <= self.stop_hour:
            if start:
                self.thread_sound_start()
                logger.info('Air start sound play')
            elif stop:
                self.thread_sound_stop()
                logger.info('Air stop sound play')
            else:
                logger.error("incorrect enable trigger start or stop")
        else:
            logger.info("Уже пізно, звуку небуде, попаде то попаде!")




if __name__ == "__main__":
    Pl = AirSound()
    Pl.alert_sound(start=True)
    logger.info("Next code.... ")