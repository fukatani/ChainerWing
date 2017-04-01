from chainer_wing.data_fetch import DataManager
import numpy as np

if __name__ == '__main__':
    expect_x = np.array([[3., 4.],
                         [3., 5.],
                         [2., 6.],
                         [2., 7.],
                         [1., 8.],
                         [1., 9.]])
    expect_y = np.array([0., 0., 0., 0., 1., 1.])

    train_x, train_y = DataManager().get_data_from_file('sample_data.csv', True)
    assert (train_x == expect_x).all()
    assert (train_y == expect_y).all()

    np.savez('sample_data.npz', x=train_x, y=train_y)
    train_x, train_y = DataManager().get_data_from_file('sample_data.npz', True)
    assert (train_x == expect_x).all()
    assert (train_y == expect_y).all()
