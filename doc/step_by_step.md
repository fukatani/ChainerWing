# Step by Step ChainerWing

## 0.Define your task and Prepare data.

chainer can handle various problem, but currect version ChainerWing support only simple regression simple classification, and image classification by supervised training.


Simple classification:
From the input feature, model predict which class the sample belongs to.

Simple regression:
From the input feature, model predict the quantity of the objective variable of the sample.
For example, problem like predicting stock price from profit margin and sales is regression.

Image classification:
From the jpg image, model predict which class the sample belongs to.
You can see Example.

![ImageExample](https://github.com/fukatani/ChainerWing/blob/master/example/image_classification/readme.md "ImageExample")

All of these task is called "supervised training", data with correct answer is required.

Typically, the data may contains several thousand, or tens of thousands or more samples.

If you don't have any data for deep learning, it is good option for you to start from example.
https://github.com/fukatani/ChainerWing/blob/master/examples/mnist/readme.md

## 1.Set up data to ChainerWing

You can open data configuration window by push button here.

![OpenData](https://github.com/fukatani/ChainerWing/blob/master/doc/screenshot/open_data.png "OpenData")

Set Train Data button:
You can select which file you will use data for training.
Train data file's extention should be .csv, .npz or .py.

When input data is csv, it is necessary to follow the following format.

![DataDetail](https://github.com/fukatani/ChainerWing/blob/master/doc/screenshot/data_detail.png "DataDetail")

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
In order to speed up learning or improve the accuracy of the model, preprocessing may be effective.

MinMaxscaler can be selected for chainerWing now. 

MinMaxscaler scales so that the maximum value of input data becomes 1 and the minimum value becomes 0

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

## 5.Deploy and Predicti by your model.

After training, you have already got trained deep learning model.
So you can prediction by them.

![Prediction](https://github.com/fukatani/ChainerWing/blob/master/doc/screenshot/prediction.png "Prediction")

To execute prediction you need input data which you want to know prediction result. (*.csv, *.npz or *.py)
And you also need trained model.(*.npz)

If you want to save prediction result, you have to set "Output File"

Push "Execute Prediction" button and wait, you can get prediction result by deep learning model.

