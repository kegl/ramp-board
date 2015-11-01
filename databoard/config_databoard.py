import os
# import socket
import pandas as pd
# import numpy as np
from git import Repo
# from multiprocessing import cpu_count

# XXX : this file should be called config
# import databoard.config_databoard as config_databoard
# to
# from databoard import config

# root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
root_path = '.'

tag_len_limit = 40

# temporary trick to detect if whether
# this is debug mode
#local_deployment = 'onevm' not in socket.gethostname()
#n_processes = 3 if local_deployment else cpu_count()

# paths
repos_path = os.path.join(root_path, 'teams_repos')
ground_truth_path = os.path.join(root_path, 'ground_truth')
models_path = os.path.join(root_path, 'models')
submissions_path = os.path.join(root_path, 'teams_submissions')
data_path = os.path.join(root_path, 'data')
raw_data_path = os.path.join(data_path, 'raw')
# TODO: create them
# TODO: use sklearn fetch 
# TODO: use jaberg's fetcher, MLData
# TODO: everything local should be _
public_data_path = os.path.join(data_path, 'public')
private_data_path = os.path.join(data_path, 'private')

cachedir = '.'

is_parallelize = False  # make it False if parallel training is not working
# make it True to use parallelism across machines
is_parallelize_across_machines = False
# maximum number of seconds per model training for parallelize across machines
timeout_parallelize_across_machines = 10800
# often doesn't work and takes a lot of disk space
is_pickle_trained_model = False

# Open ports in Stratuslab
# 22, 80, 389, 443, 636, 2135, 2170, 2171, 2172, 2811, 3147, 5001, 5010, 5015,
# 8080, 8081, 8095, 8188, 8443, 8444, 9002, 10339, 10636, 15000, 15001, 15002,
# 15003, 15004, 20000-25000.

# amadeus
#server_port = '8443'
#dest_path = '/mnt/datacamp/databoard_06_8443_test'

# pollenating insects
#server_port = '8444'
#dest_path = '/mnt/datacamp/databoard_07_8444_test'

# el nino
#server_port = '8188'
#dest_path = '/mnt/datacamp/databoard_05_8188_test'

# kaggle otto with skf_test_size = 0.5
#server_port = '8081'
#dest_path = '/mnt/datacamp/databoard_04_8081_test'

# kaggle otto with skf_test_size = 0.2
#server_port = '8095'
#dest_path = '/mnt/datacamp/databoard_04_8095_test'

# variable star
#server_port = '8080'
#dest_path = '/mnt/datacamp/databoard_03_8080_test'

#debug_server = 'http://' + "localhost:{}".format(server_port)
#train_server = 'http://' + socket.gethostname() + ".lal.in2p3.fr:{}".format(server_port)
#server_name = debug_server if local_deployment else train_server

vd_server = 'onevm-85.lal.in2p3.fr'
reims_server = 'romeo1.univ-reims.fr'
vd_root = '/mnt/datacamp'
local_root = '/tmp/databoard_local'  # for local publishing / testing

ramp_df_columns = [
    'ramp_name',  # for naming the library where the data and specific.py is
    'train_server',  # the server for training
    'train_user',  # the username on the train_server
    'train_root',  # the root dir of databoard on the train_server
    'n_cpus',  # number of cpus on the train_server
    'web_server',  # the server for the web site (and possibly leaderboard)
    'web_user',  # the username on the web_server
    'web_root',  # the root dir of databoard on the web_server
    'server_port',  # the server port on the web_server
    'cv_test_size',
    'random_state',
]
# ignore web* variables if train and web servers, users, roots are the same

ramp_df = pd.DataFrame(columns=ramp_df_columns)

ramp_df = ramp_df.append(pd.Series({
    'ramp_name': 'mortality_prediction',
    'train_server': 'localhost',
    'train_user': '',
    'train_root': local_root,
    'n_cpus': 10,
    'web_server': 'localhost',
    'web_user': '',
    'web_root': local_root,
    'server_port': '8080',
    'cv_test_size': 0.2,
    'random_state': 57,
}, name='mortality_prediction_local_test'))

ramp_df = ramp_df.append(pd.Series({
    'ramp_name': 'mortality_prediction',
    'train_server': vd_server,
    'train_user': 'root',
    'train_root': vd_root,
    'n_cpus': 10,
    'web_server': vd_server,
    'web_user': 'root',
    'web_root': vd_root,
    'server_port': '2171',
    'cv_test_size': 0.2,
    'random_state': 57,
}, name='mortality_prediction_remote_test'))

ramp_df = ramp_df.append(pd.Series({
    'ramp_name': 'iris',
    'train_server': 'localhost',
    'train_user': '',
    'train_root': local_root,
    'n_cpus': 10,
    'web_server': 'localhost',
    'web_user': '',
    'web_root': local_root,
    'server_port': '8080',
    'cv_test_size': 0.2,
    'random_state': 57,
}, name='iris_local_test'))

ramp_df = ramp_df.append(pd.Series({
    'ramp_name': 'boston_housing',
    'train_server': 'localhost',
    'train_user': '',
    'train_root': local_root,
    'n_cpus': 10,
    'web_server': 'localhost',
    'web_user': '',
    'web_root': local_root,
    'server_port': '8080',
    'cv_test_size': 0.2,
    'random_state': 57,
}, name='boston_housing_local_test'))

ramp_df = ramp_df.append(pd.Series({
    'ramp_name': 'iris',
    'train_server': vd_server,
    'train_user': 'root',
    'train_root': vd_root,
    'n_cpus': 10,
    'web_server': vd_server,
    'web_user': 'root',
    'web_root': vd_root,
    'server_port': '2171',
    'cv_test_size': 0.2,
    'random_state': 57,
}, name='iris_remote_test'))

ramp_df = ramp_df.append(pd.Series({
    'ramp_name': 'pollenating_insects',
    'train_server': reims_server,
    'train_user': 'mcherti',
    'train_root': '/home/mcherti/ramp_pollenating_insects',
    'n_cpus': 10,
    'web_server': vd_server,
    'web_user': 'root',
    'web_root': vd_root,
    'server_port': '2170',
    'cv_test_size': 0.2,
    'random_state': 57,
}, name='pollenating_insects_1'))

ramp_df = ramp_df.append(pd.Series({
    'ramp_name': 'pollenating_insects',
    'train_server': 'localhost',
    'train_user': '',
    'train_root': local_root,
    'n_cpus': 2,
    'web_server': 'localhost',
    'web_user': '',
    'web_root': local_root,
    'server_port': '8080',
    'cv_test_size': 0.2,
    'random_state': 57,
}, name='pollenating_insects_local_test'))

ramp_df = ramp_df.append(pd.Series({
    'ramp_name': 'kaggle_otto',
    'train_server': 'localhost',
    'train_user': '',
    'train_root': local_root,
    'n_cpus': 2,
    'web_server': 'localhost',
    'web_user': '',
    'web_root': local_root,
    'server_port': '8080',
    'cv_test_size': 0.2,
    'random_state': 57,
}, name='kaggle_otto_local_test'))


# TODO after insect ramp: clean up the old ramps
ramp_df = ramp_df.append(pd.Series({
    'ramp_name': 'el_nino',
    'train_server': vd_server,
    'train_user': 'root',
    'train_root': '/mnt/datacamp',
    'n_cpus': 32,
    'server_port': '9002',
    'cv_test_size': 0.5,
    'random_state': 57,
}, name='el_nino_1'))

ramp_df = ramp_df.append(pd.Series({
    'ramp_name': 'el_nino',
    'train_server': vd_server,
    'train_user': 'root',
    'server_port': '10339',
    'train_root': '/mnt/datacamp',
    'n_cpus': 15,
    'cv_test_size': 0.5,
    'random_state': 57,
}, name='el_nino_colorado'))

ramp_df = ramp_df.append(pd.Series({
    'ramp_name': 'el_nino_block_cv',
    'train_server': vd_server,
    'train_user': 'root',
    'server_port': '5015',
    'train_root': '/mnt/datacamp',
    'n_cpus': 15,
    'cv_test_size': 0.5,
    'random_state': 57,
}, name='el_nino_colorado_block_cv'))

ramp_df = ramp_df.append(pd.Series({
    'ramp_name': 'el_nino_bagged_cv_future',
    'train_server': 'localhost',
    'train_user': '',
    'train_root': local_root,
    'n_cpus': 2,
    'web_server': 'localhost',
    'web_user': '',
    'web_root': local_root,
    'server_port': '8080',
    'cv_test_size': 0.2,
    'cv_bag_size': 0.5,
    'random_state': 57,
}, name='el_nino_bagged_cv_future_local_test'))

ramp_df = ramp_df.append(pd.Series({
    'ramp_name': 'el_nino_block_cv',
    'train_server': 'localhost',
    'train_user': '',
    'train_root': local_root,
    'n_cpus': 2,
    'web_server': 'localhost',
    'web_user': '',
    'web_root': local_root,
    'server_port': '8080',
    'cv_test_size': 0.2,
    'cv_bag_size': 0.5,
    'random_state': 57,
}, name='el_nino_block_cv_local_test'))

ramp_df = ramp_df.append(pd.Series({
    'ramp_name': 'amadeus',
    'train_server': 'localhost',
    'train_user': '',
    'train_root': local_root,
    'n_cpus': 2,
    'web_server': 'localhost',
    'web_user': '',
    'web_root': local_root,
    'server_port': '8080',
    'cv_test_size': 0.2,
    'random_state': 57,
}, name='amadeus_local_test'))

ramp_df = ramp_df.append(pd.Series({
    'ramp_name': 'variable_stars',
    'train_server': 'localhost',
    'train_user': '',
    'train_root': local_root,
    'n_cpus': 2,
    'web_server': 'localhost',
    'web_user': '',
    'web_root': local_root,
    'server_port': '8080',
    'cv_test_size': 0.2,
    'random_state': 57,
}, name='variable_stars_local_test'))

# otherwise integers will have float type, weird
ramp_df[['n_cpus', 'random_state']] = ramp_df[
    ['n_cpus', 'random_state']].astype(int)

notification_recipients = []
notification_recipients.append("balazs.kegl@gmail.com")
notification_recipients.append("alexandre.gramfort@gmail.com")

assert repos_path != 'models'


def get_ramp_field(field, ramp_index=None):
    """Normally only 'fab publish' will call it with the ramp_index
    specified, otherwise it's coming from ramp_index.txt"""

    if ramp_index is None:
        with open("ramp_index.txt") as f:
            ramp_index = f.readline()
    ramp = ramp_df.loc[ramp_index]
    return ramp[field]


def get_destination_path(root, ramp_index=None):
    destination_root = get_ramp_field(root, ramp_index)
    ramp_name = get_ramp_field('ramp_name', ramp_index)
    server_port = get_ramp_field('server_port', ramp_index)
    destination_path = os.path.join(
        destination_root, "databoard_" + ramp_name + "_" + server_port)
    return destination_path


def get_train_destination_path(ramp_index=None):
    return get_destination_path('train_root', ramp_index)


def get_web_destination_path(ramp_index=None):
    return get_destination_path('web_root', ramp_index)


def is_same_web_and_train_servers(ramp_index):
    return (get_ramp_field('web_server', ramp_index) ==
            get_ramp_field('train_server', ramp_index)
            and get_ramp_field('web_user', ramp_index) ==
            get_ramp_field('train_user', ramp_index)
            and get_ramp_field('web_root', ramp_index) ==
            get_ramp_field('train_root', ramp_index))
