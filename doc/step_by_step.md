# Step by Step ChainerWing

## 0.Define your task and Prepare data.

chainer can handle various problem, but currect version ChainerWing support only simple regression and simple classification.
For example, image classification will be suported in future version.

#### Simple regression
#### Simple calssification

If you don't have any data for deep learning, it is good option for you to start from example.
https://github.com/fukatani/ChainerWing/blob/master/examples/mnist/readme.md

## 1.Set up data to ChainerWing

You can open data configuration window by push button here.

![OpenData](https://github.com/fukatani/ChainerWing/blob/master/doc/screenshot/open_data.png "OpenData")

Set Train Data button:
You can select which file you will use data for training.
Train data file's extention should be .csv, .npz or .py.

Same data with training:
If checked, train data will be separated and one of them used for test only.

Shuffle:
If checked, data will be shuffled before separating.
This option is valid when "Same data with training" is checked.

Test data ratio:
This option determines how much data to use for testing.
Test data ratio must be float, larger than zero and smaller than one. (ex. 0.8)
The remaining data is used for training.
This option is valid when "Same data with training" is checked.

Preprocess:
If you select MinMaxScaler

## 2.Construct Net

See
https://github.com/fukatani/ChainerWing/tree/master/examples/mnist#4change-net-configuration-to-improve-model-performance


#### About loss function:

Basically, for classification task, cross entropy functions are adequate.
On the other hand, for regression task, mean squared error is adequate.

## 3.Start training
Push button here.

![StartTrain](https://github.com/fukatani/ChainerWing/blob/master/doc/screenshot/start_train.png "StartTrain")

## 4.Save and load project file
Constructed net and training configuration can be saved/loaded as .json file by GUI button.

## 5.Deploy and Prediction by your model.

After training, you have already got trained deep learning model.
So you can prediction by them.

