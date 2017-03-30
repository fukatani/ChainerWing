## MNIST Example

MNIST is popular classification problem.
In this example, you have to distingish hand written digit (0~9).

#### 1.Load Project
Push button here, and select example/mnist/mnist.json.

![LoadButton](https://github.com/fukatani/ChainerWing/blob/master/doc/screenshot/load.png "LoadButton")

#### 2.Start training
Push button here.

![StartTrain](https://github.com/fukatani/ChainerWing/blob/master/doc/screenshot/start_train.png "StartTrain")

#### 3.Confirm result
Plot on rightbottom shows training result.

Here, accuracy shows how how many classifications succeeded (in %).
Loss is also an index showing the goodness of the performance of the model, the smaller the loss, the better model

![report](https://github.com/fukatani/ChainerWing/blob/master/doc/screenshot/report.png "report")

#### 4.Change net configuration to improve model performance
For example, you can add dropout layer between linear units for preventing "overfitting".
Or you can increase layer.

To add layer, please drag and drop from function list at right side to net field.

![add_layer](https://github.com/fukatani/ChainerWing/blob/master/doc/screenshot/add_layer.png "add_layer")

In general more layer, more comlicated problem can be solved.
But deep architecture need many learning epoch. 
i.e. You have to consumpt many computation time.

#### 5.Change training configuration
Training configuration is key factor of deep learning.

![OpenTrainConfig](https://github.com/fukatani/ChainerWing/blob/master/doc/screenshot/open_trainconfig.png "OpenTrainConfig")


![TrainConfig](https://github.com/fukatani/ChainerWing/blob/master/doc/screenshot/training.png "TrainConfig")

**Batch size:**
Defines size of mini-batch. 

**Epoch:**
Epoch means how many times model repeat about each sample in data.
If epoch is too less, performance does not rise sufficiently.
Too many epoch introduce overfitting.
You have to find adequate epoch.

**GPU:**
If you installed CUDA in your PC, you can acceralate deep learning computation (~10X or more).
To install CUDA for chainer, please see https://github.com/pfnet/chainer#installation-with-cuda .


**Optimizer:**
Optimizer defines how much model weight can be moved.
All of optimizer have tuning parameters.
For example one of standard optimizer, SGD have lr.
*lr* stands for learning rate, so if *lr* is large value, model weight can be changed largely.
Normally, to prevent overfitting, *lr* is set to small value (ex.lr = 0.01). 

You can get detailed information about each optimizer in chainer official documentation.
http://docs.chainer.org/en/latest/reference/optimizers.html

