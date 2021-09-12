import os

import pandas as pd
import numpy as np
import pickle as cp

pd.options.mode.chained_assignment = None


def load_dataset(dataset, cutoff_train, cutoff_valid, pred_type='actions', include_null=False):
    if dataset == 'wetlab':
        if pred_type == 'actions':
            class_names = ['cutting', 'inverting', 'peeling', 'pestling', 'pipetting', 'pouring', 'stirring',
                           'transfer']
        elif pred_type == 'tasks':
            class_names = ['1solvent', '2catalysator', '3cutting', '4mixing', '5catalysator', '6waterbath', '7solvent',
                           '8catalysator', '9cutting', '10mixing', '11catalysator', '12waterbath', '13waterbath',
                            '14catalysator', '15pestling', '16filtrate', '17catalysator', '18pouring', '19detect',
                            '20waterbath', '21catalysator', '22pestling', '23filtrate', '24catalysator', '25pouring',
                            '26detect', '27end']
        sampling_rate = 50
        has_null = True
    elif dataset == 'sbhar':
        class_names = ['walking', 'walking_upstairs', 'walking_downstairs', 'sitting', 'standing', 'laying',
                       'stand_to_sit', 'sit_to_stand', 'sit_to_lie', 'lie_to_sit', 'stand_to_lie', 'lie_to_stand']
        sampling_rate = 50
        has_null = True
    elif dataset == 'rwhar':
        class_names = ['climbingdown', 'climbingup', 'jumping', 'lying', 'running', 'sitting', 'standing', 'walking']
        sampling_rate = 50
        has_null = False
    elif dataset == 'hhar':
        class_names = ['biking', 'sitting', 'standing', 'walking', 'stair up', 'stair down']
        sampling_rate = 100
        has_null = True
    elif dataset == 'opportunity' or dataset == 'opportunity_ordonez':
        sampling_rate = 30
        has_null = True
        if pred_type == 'gestures':
            class_names = ['open_door_1', 'open_door_2', 'close_door_1', 'close_door_2', 'open_fridge',
                           'close_fridge', 'open_dishwasher', 'close_dishwasher', 'open_drawer_1', 'close_drawer_1',
                           'open_drawer_2', 'close_drawer_2', 'open_drawer_3', 'close_drawer_3', 'clean_table',
                           'drink_from_cup', 'toggle_switch']
        elif pred_type == 'locomotion':
            class_names = ['stand', 'walk', 'sit', 'lie']

    data = pd.read_csv(os.path.join('data/', dataset + '_new_data.csv'), sep=',', header=None, index_col=None)

    len_data = data.shape[0]
    print("Size of original data")
    print(len_data)

    # down-sampling of data
    df_down = data[data.index % 4 == 0]
    len_down = df_down.shape[0]
    print("down sampled length of data is")
    print(len_down)

    print("Down sampled dataframe is")
    print(df_down)

    # Create csv for down-sampled data
    df_down.to_csv('C:/Users/karti/PycharmProjects/HAR/data/rwhar_down.csv', sep=',', encoding='utf-8')

    # up-sampling of data
    for i in range(len_data):
        if i % 4 != 0:
            df_down.loc[i] = [None, None, None, None, None]

    df_up = df_down.sort_index()

    print("Up-sampled dataframe is")
    print(df_up)

    print("Dataframe after interpolation is")
    df_up = df_up.interpolate(method='linear')
    print(df_up)
    df_up.to_csv('C:/Users/karti/PycharmProjects/HAR/data/rwhar_up.csv', sep=',', encoding='utf-8')

    data = df_up

    X_train, y_train, X_val, y_val, X_test, y_test = \
        preprocess_data(data, dataset, cutoff_train, cutoff_valid, pred_type, has_null, include_null)
    print("Sampling rate used is")
    print(sampling_rate)
    print(" ..from file {}".format(os.path.join('data/', dataset + '_data.csv')))
    print(" ..reading instances: train {0}, val {1}, test {2}".format(X_train.shape, X_val.shape, X_test.shape))

    X_train = X_train.astype(np.float32)
    X_val = X_val.astype(np.float32)

    # The targets are casted to int8 for GPU compatibility.
    y_train = y_train.astype(np.uint8)
    y_val = y_val.astype(np.uint8)

    if has_null and include_null:
        class_names = ['null'] + class_names

    return X_train, y_train, X_val, y_val, X_test, y_test, len(class_names), class_names, sampling_rate, has_null


def preprocess_data(data, dataset, cutoff_train, cutoff_valid, pred_type='actions', has_null=False, include_null=True):
    """
    Function to preprocess the wetlab dataset according to settings.

    :param dataset: string
        Wetlab data
    :param cutoff_train: integer
        Subject number up to which to contain in the training dataset
    :param cutoff_valid: integer
        Subject number up to which to contain in the validation dataset. All other sequences will be test.
    :param pred_type: string, ['actions' (default), 'tasks']
        Type of labels that are to be used
    :param has_null: boolean, default: True
        Boolean signaling whether dataset has a null class
    :param include_null: boolean, default: True
        Boolean signaling whether to include or not include the null class in the dataset
    :return numpy float arrays
        Training and validation datasets that can be used for training
    """
    print('Processing dataset files ...')
    if dataset == 'opportunity_ordonez':
        if pred_type == 'locomotion':
            X_train, y_train = data.iloc[:497014, 1:114], data.iloc[:497014, -2]
            X_val, y_val = data.iloc[497014:557963, 1:114], data.iloc[497014:557963:, -2]
            X_test, y_test = data.iloc[557963:, 1:114], data.iloc[557963:, -2]
        elif pred_type == 'gestures':
            X_train, y_train = data.iloc[:497014, 1:114], data.iloc[:497014, -1]
            X_val, y_val = data.iloc[497014:557963, 1:114], data.iloc[497014:557963:, -1]
            X_test, y_test = data.iloc[557963:, 1:114], data.iloc[557963:, -1]
    elif has_null:
        if (dataset == 'wetlab' and pred_type == "actions" and not include_null) or \
           (dataset == 'opportunity' and pred_type == "gestures" and not include_null):
            train = data[(data.iloc[:, 0] <= cutoff_train)
                         & (data.iloc[:, -2] != '0') & (data.iloc[:, -2] != 0)]
            val = data[(data.iloc[:, 0] <= cutoff_valid) & (data.iloc[:, 0] > cutoff_train)
                       & (data.iloc[:, -2] != '0') & (data.iloc[:, -2] != 0)]
            test = data[(data.iloc[:, 0] > cutoff_valid) & (data.iloc[:, -2] != '0') & (data.iloc[:, -2] != 0)]
        elif not include_null:
            train = data[(data.iloc[:, 0] <= cutoff_train)
                         & (data.iloc[:, -1] != '0') & (data.iloc[:, -1] != 0)]
            val = data[(data.iloc[:, 0] <= cutoff_valid) & (data.iloc[:, 0] > cutoff_train)
                       & (data.iloc[:, -1] != '0') & (data.iloc[:, -1] != 0)]
            test = data[(data.iloc[:, 0] > cutoff_valid) & (data.iloc[:, -1] != '0') & (data.iloc[:, -1] != 0)]
        else:
            train = data[(data.iloc[:, 0] <= cutoff_train)]
            val = data[(data.iloc[:, 0] <= cutoff_valid) & (data.iloc[:, 0] > cutoff_train)]
            test = data[(data.iloc[:, 0] > cutoff_valid)]
    else:
        train = data[(data.iloc[:, 0] <= cutoff_train)]
        val = data[(data.iloc[:, 0] <= cutoff_valid) & (data.iloc[:, 0] > cutoff_train)]
        test = data[(data.iloc[:, 0] > cutoff_valid)]

    if (dataset == 'wetlab' and pred_type == 'actions') or (dataset == 'opportunity' and pred_type == "locomotion"):
        X_train, X_val, X_test = train.iloc[:, :-2], val.iloc[:, :-2], test.iloc[:, :-2]
        y_train = adjust_labels(train.iloc[:, -2], dataset, pred_type).astype(int)
        y_val = adjust_labels(val.iloc[:, -2], dataset, pred_type).astype(int)
        y_test = adjust_labels(test.iloc[:, -2], dataset, pred_type).astype(int)
    elif dataset == 'opportunity_ordonez':
        pass
    else:
        X_train, X_val, X_test = train.iloc[:, :-1], val.iloc[:, :-1], test.iloc[:, :-1]
        y_train = adjust_labels(train.iloc[:, -1], dataset, pred_type).astype(int)
        y_val = adjust_labels(val.iloc[:, -1], dataset, pred_type).astype(int)
        y_test = adjust_labels(test.iloc[:, -1], dataset, pred_type).astype(int)

    if dataset == 'rwhar':
        y_train -= 1
        y_val -= 1
        y_test -= 1

    # if no null class in dataset subtract one from all labels
    if has_null and not include_null and dataset != 'oppportunity_ordonez':
        y_train -= 1
        y_val -= 1
        y_test -= 1
    print("Final datasets with size: | train {0} | val {1} | test {2} | ".format(X_train.shape, X_val.shape,
                                                                                 X_test.shape))

    return X_train.to_numpy(), y_train.to_numpy(), X_val.to_numpy(), y_val.to_numpy(), X_test.to_numpy(), y_test.to_numpy()


def compute_mean_and_std(data):
    """
    Function which computes the mean and standard deviation per column of a given dataset.

    :param data: numpy float array
        Dataset which is to be used
    :return: numpy float array
        Mean and standard deviation column per column contained in dataset
    """
    results = np.empty((data.shape[0], data.shape[1] * 2))
    if data.size != 0:
        for i, column in enumerate(data.T):
            results[:, i] = np.full((data.shape[0]), np.mean(column))
            results[:, data.shape[1] + i] = np.full((data.shape[0]), np.std(column))
    return results.astype(np.float32)


def adjust_labels(data_y, dataset, pred_type='actions'):
    """
    Transforms original labels into the range [0, nb_labels-1]

    :param data_y: numpy integer array
        Sensor labels
    :param pred_type: string, ['gestures', 'locomotion', 'actions', 'tasks']
        Type of activities to be recognized
    :return: numpy integer array
        Modified sensor labels
    """
    if dataset == 'wetlab':
        data_y[data_y == "0"] = 0
        if pred_type == 'tasks':  # Labels for tasks are adjusted
            data_y[data_y == "1solvent"] = 1
            data_y[data_y == "2catalysator"] = 2
            data_y[data_y == "3cutting"] = 3
            data_y[data_y == "4mixing"] = 4
            data_y[data_y == "5catalysator"] = 5
            data_y[data_y == "6waterbath"] = 6
            data_y[data_y == "7solvent"] = 7
            data_y[data_y == "8catalysator"] = 8
            data_y[data_y == "9cutting"] = 9
            data_y[data_y == "10mixing"] = 10
            data_y[data_y == "11catalysator"] = 11
            data_y[data_y == "12waterbath"] = 12
            data_y[data_y == "13waterbath"] = 13
            data_y[data_y == "14catalysator"] = 14
            data_y[data_y == "15pestling"] = 15
            data_y[data_y == "16filtrate"] = 16
            data_y[data_y == "17catalysator"] = 17
            data_y[data_y == "18pouring"] = 18
            data_y[data_y == "19detect"] = 19
            data_y[data_y == "20waterbath"] = 20
            data_y[data_y == "21catalysator"] = 21
            data_y[data_y == "22pestling"] = 22
            data_y[data_y == "23filtrate"] = 23
            data_y[data_y == "24catalysator"] = 24
            data_y[data_y == "25pouring"] = 25
            data_y[data_y == "26detect"] = 26
            data_y[data_y == "27end"] = 27
        elif pred_type == 'actions':  # Labels for actions are adjusted
            data_y[data_y == "cutting"] = 1
            data_y[data_y == "inverting"] = 2
            data_y[data_y == "peeling"] = 3
            data_y[data_y == "pestling"] = 4
            data_y[data_y == "pipetting"] = 5
            data_y[data_y == "pouring"] = 6
            data_y[data_y == "pour catalysator"] = 6
            data_y[data_y == "stirring"] = 7
            data_y[data_y == "transfer"] = 8
    elif dataset == 'sbhar':
        pass
    elif dataset == 'rwhar':
        pass
    elif dataset == 'hhar':
        data_y[data_y == 0] = 0
        data_y[data_y == 'bike'] = 1
        data_y[data_y == 'sit'] = 2
        data_y[data_y == 'stand'] = 3
        data_y[data_y == 'walk'] = 4
        data_y[data_y == 'stairsup'] = 5
        data_y[data_y == 'stairsdown'] = 6
    elif dataset == 'opportunity':
        pass
    return data_y
