from __future__ import division
import datetime
import os
import sys
import time

from chainer.training import extension
from chainer.training.extensions import util
from chainer.training import trigger

from PyQt5.QtWidgets import QProgressBar
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import Qt

from floppy.runner import StopTraining


class CWProgressBar(extension.Extension, QDialog):

    def __init__(self, *args, update_interval=100):
        self._update_interval = update_interval
        self._recent_timing = []
        self._training_length = None

        super(CWProgressBar, self).__init__(*args)
        self.setWindowTitle('progress')

        mainLayout = QVBoxLayout()
        self.pbar = QProgressBar()
        self.pbar.setGeometry(25, 40, 200, 25)
        mainLayout.addWidget(self.pbar)

        self._stat_label = QLabel('')
        mainLayout.addWidget(self._stat_label)
        self._est_label = QLabel('')
        mainLayout.addWidget(self._est_label)

        stopButton = QPushButton('Stop')
        stopButton.clicked.connect(self.finalize)
        mainLayout.addWidget(stopButton)

        self.setLayout(mainLayout)

        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.setStyleSheet('''SettingsDialog {
                                background: rgb(75,75,75);
                            }
                            QPushButton {
                                background-color: rgb(205,85,85);
                                color: white;
                            }
                            QLabel {
                                color: black;
                            }
        ''')
        self.show()
        self.raise_()

    def __call__(self, trainer):
        training_length = self._training_length

        # initialize some attributes at the first call
        t = trainer.stop_trigger
        if not isinstance(t, trigger.IntervalTrigger):
            raise TypeError(
                'cannot retrieve the training length from %s' % type(t))
        training_length = self._training_length = t.period, t.unit

        stat_template = (
                '{0.iteration:10} iter, {0.epoch} epoch / %s %ss\n' %
                training_length)

        length, unit = training_length
        iteration = trainer.updater.iteration
        self.pbar.setRange(0, length)

        # print the progress bar
        if iteration % self._update_interval == 0:
            epoch = trainer.updater.epoch_detail
            recent_timing = self._recent_timing
            now = time.time()

            recent_timing.append((iteration, epoch, now))

            self.pbar.setValue(epoch)

            self._stat_label.setText(stat_template.format(trainer.updater))
            # out.write(status)

            old_t, old_e, old_sec = recent_timing[0]
            span = now - old_sec
            if span != 0:
                speed_t = (iteration - old_t) / span
                speed_e = (epoch - old_e) / span
            else:
                speed_t = float('inf')
                speed_e = float('inf')

            if unit == 'iteration':
                estimated_time = (length - iteration) / speed_t
            else:
                estimated_time = (length - epoch) / speed_e
            self._est_label.setText('{:10.5g} iters/sec. Estimated time to finish: {}.\n'
                                    .format(speed_t,
                                    datetime.timedelta(seconds=estimated_time)))

            if len(recent_timing) > 100:
                del recent_timing[0]
        QApplication.instance().processEvents()

    def finalize(self):
        # delete the progress bar
        super(CWProgressBar, self).close()
        raise StopTraining
