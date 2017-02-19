import subprocess

from floppy.train_configuration import TrainParamServer

#TODO(fukatani): implement all
class Runner(object):
    def __init__(self):
        self.is_running = False
        self.run_process = None

    def run(self):
        self.is_running = True
        net_file = TrainParamServer()['NetName'] + '.py'
        self.run_process = subprocess.Popen(net_file)

    def kill(self):
        if self.is_running:
            self.run_process.kill()
        self.is_running = False
