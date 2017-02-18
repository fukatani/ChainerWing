import numpy as np
import csv


class DataManeger(object):
    def __init__(self):
        self.train_columns = 0

    def get_data_from_file(self, file_name, is_supervised):
        if file_name[-4:] == '.csv':
            return self.csv_to_ndarray(file_name, is_supervised)
        elif file_name[-4:] == '.npz':
            data = np.load(file_name)
            if is_supervised:
                return data['x'], data['y']
            else:
                return data['x'], None

    def csv_to_ndarray(self, csv_file, is_supervised):
        exists_header = 0
        with open(csv_file, 'r') as f:
            reader = csv.reader(f)
            for line in reader:
                if isinstance(line[0], str):
                    exists_header = 1
        data = np.loadtxt(csv_file, delimiter=',', skiprows=exists_header)
        return self.separate_superviser(data, is_supervised)

    def separate_superviser(self, data, is_supervised):
        if is_supervised:
            self.train_columns = data.shape[1]
            superviser = data[:, -1]
            data = data[:, :-1]
            return data, superviser
        elif data.shape[1] == self.train_columns:
            superviser = data[:, -1]
            data = data[:, :-1]
            return data, superviser
        else:  # Not including superviser
            return data, None


if __name__ == '__main__':
    train_x, train_y = DataManeger().get_data_from_file('sample_data.csv', True)
    train_x, train_y = DataManeger().get_data_from_file('sample_data.npz', True)
