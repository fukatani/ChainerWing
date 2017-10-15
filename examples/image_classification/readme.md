## Image Classification Example

Image Classification is popular theme of deep learning.
This document explains how to do image classification.

#### 1.Load Project
Push button here, and select example/image_classification/image.json.

![LoadButton](https://github.com/fukatani/ChainerWing/blob/master/doc/screenshot/load.png "LoadButton")

#### 2.Confirm Train Configuration
Confirm task is Image Classification.
![ImageTask](https://github.com/fukatani/ChainerWing/blob/master/doc/screenshot/image_classification_task.png "ImageTask")
If you create image classification project from scratch, you should set this option by yourself.

#### 3.Load Training Data
Push button here, and select example/mnist/image_classification/data

![LoadButton](https://github.com/fukatani/ChainerWing/blob/master/doc/screenshot/selectdata.png "SelectData")

"data" directory includes "Green" and "Spanish" subdirectory. Each subdirectory contains an image corresponding to that directory name.
If you create your own image classification project, you should make similar directory structure.

#### 4.Data Augmentaion
To improve model performance, you can use data augmentation technic.
![DataAugmentation](https://github.com/fukatani/ChainerWing/blob/master/doc/screenshot/data_augmentation.png "DataAugmentation")
By preview update button, You can check data augmentation result visually.

#### 5.Start training
Push button here.

![StartTrain](https://github.com/fukatani/ChainerWing/blob/master/doc/screenshot/start_train.png "StartTrain")

#### 6.Confirm result
Plot on rightbottom shows training result.

Here, accuracy shows how how many classifications succeeded (in %).
Loss is also an index showing the goodness of the performance of the model, the smaller the loss, the better model.

![report](https://github.com/fukatani/ChainerWing/blob/master/doc/screenshot/report.png "report")

#### 7.Change net configuration to improve model performance
For example, you can add Convolution layer for more complicated task.
Or you can tuning parameter such as ksize, pad or stride.


#### 8. Predict your data.
Push button here.
![Prediction](https://github.com/fukatani/ChainerWing/blob/master/doc/screenshot/prediction.png "Prediction")

![PredictionWindow](https://github.com/fukatani/ChainerWing/blob/master/doc/screenshot/prediction_window.png "PredictionWindow")
Please confirm to be selected learning model.
Default, it is example/image_classification/result/MyModel.npz.

Next, please directory which contains input image file for prediction.

![InputImageData](https://github.com/fukatani/ChainerWing/blob/master/doc/screenshot/select_image_data.png "InputImageData")

Finally, press "Execute prediction" button.

You can confirm prediction data by table.



