# coding=utf-8
from __future__ import division
import time
import os
import re
import glob
from importlib import import_module

import numpy as np
from skimage.io import imread
import pandas as pd

from data import minibatch_img_iterator

if __name__ == '__main__':
    split = 'pub_train'
    df = pd.read_csv('{}/data.csv'.format(split))
    nb_minibatches = 0
    t0 = time.time()
    for X, y in minibatch_img_iterator(df, batch_size=128, include_y=True, folder=split):
        nb_minibatches += 1
    elapsed = time.time() - t0
    elapsed_per_minibatch = elapsed / nb_minibatches
    print('{:.3f} sec/minibatch'.format(elapsed_per_minibatch))
