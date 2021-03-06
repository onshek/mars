# Copyright 1999-2020 Alibaba Group Holding Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest

import numpy as np
import pandas as pd

import mars.tensor as mt
import mars.dataframe as md
from mars.session import new_session
from mars.learn.contrib.xgboost import MarsDMatrix, train, predict
from mars.tests.core import ExecutorForTest

try:
    import xgboost
    from xgboost import Booster
except ImportError:
    xgboost = None


@unittest.skipIf(xgboost is None, 'XGBoost not installed')
class Test(unittest.TestCase):
    def setUp(self):
        n_rows = 1000
        n_columns = 10
        chunk_size = 20
        rs = mt.random.RandomState(0)
        self.X = rs.rand(n_rows, n_columns, chunk_size=chunk_size)
        self.y = rs.rand(n_rows, chunk_size=chunk_size)
        self.X_df = md.DataFrame(self.X)
        self.y_series = md.Series(self.y)

        self.session = new_session().as_default()
        self._old_executor = self.session._sess._executor
        self.executor = self.session._sess._executor = \
            ExecutorForTest('numpy', storage=self.session._sess._context)

    def tearDown(self) -> None:
        self.session._sess._executor = self._old_executor

    def testLocalPredictTensor(self):
        dtrain = MarsDMatrix(self.X, self.y)
        booster = train({}, dtrain, num_boost_round=2)
        self.assertIsInstance(booster, Booster)

        prediction = predict(booster, self.X)
        self.assertIsInstance(prediction.to_numpy(), np.ndarray)

        prediction = predict(booster, dtrain)
        self.assertIsInstance(prediction.fetch(), np.ndarray)

        with self.assertRaises(TypeError):
            predict(None, self.X)

    def testLocalPredictDataFrame(self):
        dtrain = MarsDMatrix(self.X_df, self.y_series)
        booster = train({}, dtrain, num_boost_round=2)
        self.assertIsInstance(booster, Booster)

        prediction = predict(booster, self.X_df)
        self.assertIsInstance(prediction.to_pandas(), pd.Series)
