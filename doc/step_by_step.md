#Step by Step ChainerWing

##Your task

0.Define your task and Prepare data.

chainer can handle various problem, but currect version ChainerWing support only simple regression and simple classification.
For example, image classification will be suported in future version.

====Simple regression====
====Simple calssification====

1.Set up data to ChainerWing
If you don't have any data for deep learning, you can play by example.

2.Construct Net

About link:


About activate functions:
Non-linear activation function such as 

About loss function:

Basically, for classification task, cross entropy functions are adequate.
On the other hand, for regression task, mean squared error is adequate.

3.Start training

4.Save and load project file
Constructed net and training configuration can be saved as .json file.

5.Deploy and Prediction by your model.

After training, you have already got trained deep learning model.
So you can prediction by them.

