# -*- coding: utf-8 -*-
# @Date    : 2017/10/31
# @Author  : hrwhisper
"""
    Given a user feature, predict the price. the predicted price will be use as a feature for predicting shop_id.
"""
import os

import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.externals import joblib
from sklearn.model_selection import KFold

from common_helper import ModelBase, DataVector
from parse_data import read_train_join_mall, read_test_data
from use_category2 import CategoryToVec2
from use_location import LocationToVec2
from use_price import PriceToVec
from use_strong_wifi import WifiStrongToVec
from use_time import TimeToVec
from use_wifi import WifiToVec
from use_wifi_kstrong import WifiKStrongToVec


class CategoryPredicted(ModelBase):
    def __init__(self):
        super().__init__()
        self.feature_save_path = './feature_save/predicted_price3.csv'

    def _get_classifiers(self):
        """
        :return: dict. {name:classifier}
        """
        return {
            'RandomForestRegressor ': RandomForestRegressor(n_estimators=100, n_jobs=self.n_jobs, random_state=42)
        }

    def train_test(self, vec_func, target_column='price', fold=10):
        """

        :param vec_func: list of vector function
        :param target_column: the target column you want to predict.
        :param fold: the fold of cross-validation.
        :return: None
        """
        # ------input data -----------
        _train_data = read_train_join_mall()
        _train_data = _train_data.sort_values(by='time_stamp')
        _train_label = _train_data[target_column].values
        _test_data = read_test_data()

        kf = KFold(n_splits=fold, random_state=self._random_state)
        oof_train = np.zeros((_train_data.shape[0],))
        oof_test = np.zeros((_test_data.shape[0],))
        oof_test_skf = np.zeros((fold, _test_data.shape[0]))

        fold_error = 0
        for i, (train_index, test_index) in enumerate(kf.split(_train_data)):
            print(i)
            fold_error += self._trained_and_predict(vec_func, _train_data, _train_label, _test_data, oof_train,
                                                    oof_test_skf,
                                                    train_index, test_index, i)

        oof_test[:] = oof_test_skf.mean(axis=0)

        joblib.dump(oof_train, self.feature_save_path + '_oof_train.pkl', compress=3)
        joblib.dump(oof_test, self.feature_save_path + '_oof_test.pkl', compress=3)

        print(fold_error / fold)

        with open(self.feature_save_path, 'w') as f:
            f.write('row_id,p_price\n')
            for i, row_id in enumerate(_train_data['row_id']):
                f.write('{},{}\n'.format(row_id, oof_train[i]))
            for i, row_id in enumerate(_test_data['row_id']):
                f.write('{},{}\n'.format(row_id, oof_test[i]))
        print('done')

    def _trained_and_predict(self, vec_func, _train_data, _train_label, R_X_test,
                             oof_train, oof_test, _train_index, _test_index, cur_fold):
        mall_id_list = sorted(list(_train_data.iloc[_train_index]['mall_id'].unique()))
        _train_index = set(_train_index)
        _test_index = set(_test_index)
        clf = list(self._get_classifiers().values())[0]
        total_error = 0
        for ri, mall_id in enumerate(mall_id_list):
            # 先得到当前商场的所有下标，然后和训练的下标做交集才对。
            index = set(np.where(_train_data['mall_id'] == mall_id)[0])

            train_index = np.array(list(_train_index & index))
            test_index = np.array(list(_test_index & index))

            data = _train_data
            label = _train_label

            fold_X_train, fold_y_train = data.iloc[train_index], label[train_index]
            fold_X_test, fold_y_test = data.iloc[test_index], label[test_index]

            assert len(fold_X_train['mall_id'].unique()) == 1

            X_train, y_train, X_test, y_test = DataVector.train_and_test_to_vec(mall_id, vec_func, fold_X_train,
                                                                                fold_y_train, fold_X_test, fold_y_test)
            print('fit...')
            clf.fit(X_train, y_train)
            # print(X_train.shape, y_train.shape, X_test.shape)

            print('predict.....')
            predicted = clf.predict(X_test)

            # predicted = np.array([round(i) for i in predicted])
            # print(predicted.shape)

            oof_train[test_index] = predicted

            # print(y_test.shape)
            # print(y_test[:100])
            # print(predicted[:100])
            error = np.average(np.abs(predicted - y_test))
            total_error += error
            # mean_absolute_error(y_test, predicted, multioutput='raw_values')
            print(ri, mall_id, error)

            X_test, _ = DataVector.data_to_vec(mall_id, vec_func, R_X_test, None, is_train=False)
            oof_test[cur_fold, np.where(R_X_test['mall_id'] == mall_id)[0]] += clf.predict(X_test)

        return total_error / len(mall_id_list)


def train_test():
    task = CategoryPredicted()
    func = [LocationToVec2(), WifiToVec(), WifiStrongToVec(), WifiKStrongToVec(), CategoryToVec2()]
    task.train_test(func, 'price', fold=20)
    # task.train_and_on_test_data(func, 'price')


def recovery_price_from_pkl():
    _train_data = read_train_join_mall()
    _train_data = _train_data.sort_values(by='time_stamp')
    _test_data = read_test_data()

    oof_train = joblib.load('./feature_save/predicted_price.csv_oof_train.pkl')
    oof_test = joblib.load('./feature_save/predicted_price.csv_oof_test.pkl')
    print(oof_train.shape, _train_data.shape)
    print(oof_test.shape, _test_data.shape)

    with open('./feature_save/predicted_price.csv', 'w') as f:
        f.write('row_id,p_price\n')
        for row_id, p in zip(_train_data['row_id'], oof_train):
            f.write('{},{}\n'.format(row_id, p))
        for row_id, p in zip(_test_data['row_id'], oof_test):
            f.write('{},{}\n'.format(row_id, p))


if __name__ == '__main__':
    train_test()
    # recovery_price_from_pkl()
