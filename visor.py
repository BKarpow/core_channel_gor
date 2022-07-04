from loguru import logger
import threading

class Visor():
	"""docstring for ClassName"""
	def __init__(self, proc_name: str, proc):
		self.proc_name = proc_name
		self.proc = proc
		self.restart = False


		def restartOn(self):
			logger.debug(f'Restart On: {self.proc_name}')
			self.restart = True


		def restartOff(self):
			self.restart = False


		def sleep_restart():
