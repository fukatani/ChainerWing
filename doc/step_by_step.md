#Step by Step ChainerWing

##Your task

0.Define your task and Prepare data.

chainer, but currect version ChainerWing support only simple regression and simple 

1.Set up data to ChainerWing
If you don't have any data for deep learning, you can play by example.

2.Construct Net


About Loss function:
Basically, for classification, cross entropy functions are adequate.
On the other hand, 


3.Start training

4.Save and load project file
Constructed net and training configuration can be saved as .json file.

5.Deploy and Prediction by your model.

After training, you have already got trained deep learning model.
So you can prediction by them.


##MNIST Example

MNIST is popular classification problem.
In this example you have to distingish hand written digit (0~9).

1.Load Project
Push button here, and select example/mnist/mnist.json.

2.Start training
Push button here.

3.Confirm result
Plot on rightbottom shows training result.
Accuracy means 

4.Change net configuration
For example, you can add dropout layer for preventing "overfit".
Or you can increase layer.
In general more layer, More comlicated.
But deep architecture need many learning epoch.

5.Change training configuration
Training configuration is key factor of deep learning.
"Batch size":
Defines size of mini-batch. 

"Epoch":
Epoch means how many times model repeat about each sample in data.
Too less epoch, model .Too many epoch introduce over fitting.
You have to find adequate epoch.
"GPU":
If you installed CUDA in your PC, you can acceralate deep learning computation.

"Optimizer":
Optimizer defines how much model weight can be moved.
All of optimizer have tuning parameters.
For example one of standard optimizer, SGD have lr.
*lr* stands for learning rate, so if *lr* is large value, model weight can be changed largely.
Normally, to prevent overfitting, *lr* is set to small value (ex.lr = 0.01). 

You can get detailed information about each optimizer in chainer official documentation.
http://docs.chainer.org/en/latest/reference/optimizers.html


##Kaggle credit card analysis

1.Load Project

2.Start training

3.Confirm result

4.Change net configuration

5.Change training configuration
