# -*- coding: utf-8 -*-
# @Date    : 2017/10/28
# @Author  : hrwhisper

import pandas as pd
import numpy as np
from scipy.sparse import csr_matrix

from common_helper import ModelBase, XXToVec
from parse_data import read_mall_data


class CategoryToVec(XXToVec):
    """
        using the category feature which has been predicted by 'predict_category.py'
    """
    CATEGORY_ID = {_id: i for i, _id in enumerate(sorted(set(read_mall_data()['category_id'])))}
    TRAIN_CATEGORY = pd.read_csv('./feature_save/predicted_category.csv')

    def __init__(self):
        super().__init__('./feature_save/time_features_{}_{}.pkl')

    def _do_transform(self, data):
        d = data.join(self.TRAIN_CATEGORY.set_index('row_id'), on='row_id', rsuffix='_train')
        d = d['p_category_id']
        features = np.array([self.CATEGORY_ID[i] for i in d]).reshape(-1, 1)
        return csr_matrix(features)

    def _fit_transform(self, train_data, mall_id):
        return self._do_transform(train_data)

    def _transform(self, test_data, mall_id):
        return self._do_transform(test_data)



def train_test():
    task = ModelBase()
    task.train_test([CategoryToVec()], 'shop_id')
    # task.train_and_on_test_data([CategoryToVec()])


if __name__ == '__main__':
    train_test()