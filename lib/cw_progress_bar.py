from __future__ import division

import datetime
import time

from PyQt5.QtCore import Qt
from PyQt5 import QtWidgets

from chainer.training import extension
from chainer.training.triggers import interval


class CWProgressBar(extension.Extension, QtWidgets.QDialog):

    def __init__(self, epoch, update_interval=100, *args):
        self._update_interval = update_interval
        self._recent_timing = []
        self.stop_trigger = None
        self.interval_trigger = interval.IntervalTrigger(epoch, 'epoch')
        self.epoch = epoch

        super(CWProgressBar, self).__init__(*args)
        self.setWindowTitle('progress')

        main_layout = QtWidgets.QVBoxLayout()
        self.pbar = QtWidgets.QProgressBar()
        self.pbar.setGeometry(25, 40, 200, 25)
        main_layout.addWidget(self.pbar)

        self._stat_label = QtWidgets.QLabel('')
        main_layout.addWidget(self._stat_label)
        self._est_label = QtWidgets.QLabel('')
        main_layout.addWidget(self._est_label)

        stop_button = QtWidgets.QPushButton('Stop')
        stop_button.clicked.connect(self.finalize)
        main_layout.addWidget(stop_button)

        self.setLayout(main_layout)

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

        # initialize some attributes at the first call
        training_length = self.epoch, 'epoch'

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
            self._est_label.setText('{:10.5g} iters/sec. '
                                    'Estimated time to finish: {}.\n'
                                    .format(speed_t,
                                    datetime.timedelta(seconds=estimated_time)))

            if len(recent_timing) > 100:
                del recent_timing[0]
        QtWidgets.QApplication.instance().processEvents()

    def finalize(self):
        # delete the progress bar and exit training
        self.stop_trigger = True
        super(CWProgressBar, self).close()

    def get_stop_trigger(self, trainer):
        return self.stop_trigger or self.interval_trigger(trainer)
