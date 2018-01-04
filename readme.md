# ChainerWing
GUI deep learning IDE based on chainer.

The interface may be changed.

![Screenshots](https://github.com/fukatani/ChainerWing/blob/master/doc/screenshot.png "Screenshots")

## Software Requirement

* Python (3.5 or later)
* chainer (2.0.0 or later)
* cupy (For GPU user)
* PyQt5
* chainercv (Optional, for image classification task)
```
pip install chainer
pip install cupy
pip install pyqt5
```

## Installation

```
git clone https://github.com/fukatani/ChainerWing.git
python setup.py install
```

## Example

https://github.com/fukatani/ChainerWing/blob/master/examples/mnist/readme.md

## Usage
```
python bin/ChainerWing.py
```
I'm preparing user manual.

https://github.com/fukatani/ChainerWing/blob/master/doc/step_by_step.md

### Use with chainerui

![chainerui](https://github.com/fukatani/ChainerWing/blob/master/doc/screenshot/chainerui.png "chainerui")

Please setup chainerui.
```
pip install chainerui
chainerui db create
chainerui db upgrade
```
If chainerui installed, ChainerWing creates project, startup server open report by web browser automatically.

## Licence

Many of GUI design is referenced by Floppy.
(https://github.com/JLuebben/Floppy)
Floppy is licenced by BSD 3 Clause.

Parts of chainer extension is referenced by chainer.
(https://github.com/pfnet/chainer)
chainer is licenced by MIT License.

## Blog Entry(Japanese)
http://segafreder.hatenablog.com/entry/2017/10/25/225047

