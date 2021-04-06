#!/usr/bin/env python
# coding: utf-8
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import os
from time import time
import shutil
import argparse
import configparser
from model.ASTGCN_r import make_model
from lib.utils import compute_val_loss_mstgcn, predict_and_save_results_mstgcn, get_normalized_adj
from tensorboardX import SummaryWriter

from method_replay import load_graphdata_channel_stp

#-------------------------------------------Experimental Settings with parser--------------------------------------------#
parser = argparse.ArgumentParser()                                                                                       #
# for ISFD21                                                                                                             #
# parser.add_argument("--config", default='configurations/ISFD21_aastgcn.conf',                                          #
#                     type=str,help="configuration file path")                                                           #                                                                                          #
# for SSFD21                                                                                                             #
parser.add_argument("--config", default='configurations/SSFD21_aastgcn.conf', type=str,                                  #
                    help="configuration file path")                                                                      #

args = parser.parse_args()
config = configparser.ConfigParser()
print('Read configuration file: %s' % (args.config))
config.read(args.config)

data_config = config['Data']
training_config = config['Training']

# aastgcn do not need adj matrix, just for astagcn
# adj_filename = data_config['adj_filename']
# graph_signal_matrix_filename = data_config['graph_signal_matrix_filename']

if config.has_option('Data', 'id_filename'):
    id_filename = data_config['id_filename']
else:
    id_filename = None

# from ISFD21/SSFD21_astgcn.conf [Data]
num_of_vertices = int(data_config['num_of_vertices'])
num_for_predict = int(data_config['num_for_predict'])
len_input = int(data_config['len_input'])
dataset_name = data_config['dataset_name']

# from ISFD21/SSFD21_aastgcn.conf [Training]
model_name = training_config['model_name']
ctx = training_config['ctx']
os.environ["CUDA_VISIBLE_DEVICES"] = ctx
USE_CUDA = torch.cuda.is_available()
DEVICE = torch.device('cuda:0')
print("CUDA:", USE_CUDA, DEVICE)

learning_rate = float(training_config['learning_rate'])
epochs = int(training_config['epochs'])
start_epoch = int(training_config['start_epoch'])
batch_size = int(training_config['batch_size'])

# astgcn's time level is 3 (week+day+hour), while time-level for aastgcn is 1 (day)
# expanding the data may further improve model performance
num_of_hours = int(training_config['time_level'])
time_strides = num_of_hours #

nb_chev_filter = int(training_config['nb_chev_filter'])
nb_time_filter = int(training_config['nb_time_filter'])
in_channels = int(training_config['in_channels'])
nb_block = int(training_config['nb_block'])
K = int(training_config['K'])

folder_dir = '%s_h%d_%e' % (model_name, in_channels, learning_rate)
print('folder_dir:', folder_dir)
params_path = os.path.join('experiments', dataset_name, folder_dir)
print('params_path:', params_path)

#-------------------------------------------Load data for AASTGCN--------------------------------------------#

## load ISFD21 adj just for astgcn
## adj_mx = np.load('./data/ISFD21/distance.npy') # static_adj_matrix with history price data
# adj normalized just for astgcn
# adj_mx = get_normalized_adj(adj_mx)


# load ISFD21/SSFD21 data
train_loader, train_target_tensor, val_loader, val_target_tensor, test_loader, test_target_tensor, \
_mean, _std = load_graphdata_channel_stp(dataset_name, num_timesteps_input=len_input,
                                                       num_timesteps_output=num_for_predict,
                                                       DEVICE=DEVICE, batch_size=32)



#-------------------------------------------Make AASTGCN--------------------------------------------#

# make model
net = make_model(DEVICE, nb_block, in_channels, K, nb_chev_filter, nb_time_filter, time_strides,
                 num_for_predict, len_input, num_of_vertices)


#-------------------------------------------train + valid + test--------------------------------------------#

def train_main():
    if (start_epoch == 0) and (not os.path.exists(params_path)):
        os.makedirs(params_path)
        print('create params directory %s' % (params_path))
    elif (start_epoch == 0) and (os.path.exists(params_path)):
        shutil.rmtree(params_path)
        os.makedirs(params_path)
        print('delete the old one and create params directory %s' % (params_path))
    elif (start_epoch > 0) and (os.path.exists(params_path)):
        print('train from params directory %s' % (params_path))
    else:
        raise SystemExit('Wrong type of model!')

    print('param list:')
    print('CUDA\t', DEVICE)
    print('in_channels\t', in_channels)
    print('nb_block\t', nb_block)
    print('nb_chev_filter\t', nb_chev_filter)
    print('nb_time_filter\t', nb_time_filter)
    print('time_strides\t', time_strides)
    print('batch_size\t', batch_size)
    # print('graph_signal_matrix_filename\t', graph_signal_matrix_filename)
    print('start_epoch\t', start_epoch)
    print('epochs\t', epochs)

    criterion = nn.MSELoss().to(DEVICE)
    optimizer = optim.Adam(net.parameters(), lr=learning_rate)
    sw = SummaryWriter(logdir=params_path, flush_secs=5)
    print(net)

    print('Net\'s state_dict:')
    total_param = 0
    for param_tensor in net.state_dict():
        print(param_tensor, '\t', net.state_dict()[param_tensor].size())
        total_param += np.prod(net.state_dict()[param_tensor].size())
    print('Net\'s total params:', total_param)

    print('Optimizer\'s state_dict:')
    for var_name in optimizer.state_dict():
        print(var_name, '\t', optimizer.state_dict()[var_name])

    global_step = 0
    best_epoch = 0
    best_val_loss = np.inf
    start_time = time()
    if start_epoch > 0:
        params_filename = os.path.join(params_path, 'epoch_%s.params' % start_epoch)
        print('params_filename:{}'.format(params_filename))
        # params_filename = params_path + 'epoch_%s.params' % start_epoch
        # print('params_filename:{}'.format(params_filename))
        net.load_state_dict(torch.load(params_filename))
        print('start epoch:', start_epoch)
        print('load weight from: ', params_filename)

    # train model
    for epoch in range(start_epoch, epochs):

        params_filename = os.path.join(params_path, 'epoch_%s.params' % epoch)

        val_loss = compute_val_loss_mstgcn(net, val_loader, criterion, sw, epoch)

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_epoch = epoch
            torch.save(net.state_dict(), params_filename)
            print('save parameters to file: %s' % params_filename)

        net.train()  # ensure dropout layers are in train mode

        for batch_index, batch_data in enumerate(train_loader):

            encoder_inputs, labels = batch_data

            optimizer.zero_grad()

            outputs = net(encoder_inputs)

            loss = criterion(outputs, labels)

            loss.backward()

            optimizer.step()

            training_loss = loss.item()

            global_step += 1

            sw.add_scalar('training_loss', training_loss, global_step)

            if global_step % 1000 == 0:

                print('global step: %s, training loss: %.2f, time: %.2fs' % (global_step, training_loss, time() - start_time))

    print('best epoch:', best_epoch)

    # apply the best model on the test set
    predict_main(best_epoch, test_loader, test_target_tensor, _mean, _std, 'test')


def predict_main(global_step, data_loader, data_target_tensor, _mean, _std, type):
    '''

    :param global_step: int
    :param data_loader: torch.utils.data.utils.DataLoader
    :param data_target_tensor: tensor
    :param mean: (1, 1, 1, 1)
    :param std: (1, 1, 1, 1)
    :param type: string
    :return:
    '''

    params_filename = os.path.join(params_path, 'epoch_%s.params' % global_step)
    # params_filename = params_path + 'epoch_%s.params' % global_step
    print('load weight from:', params_filename)

    net.load_state_dict(torch.load(params_filename))

    predict_and_save_results_mstgcn(net, data_loader, data_target_tensor, global_step, _mean, _std, params_path, type)


if __name__ == "__main__":

    train_main()

    # predict_main(7, test_loader, test_target_tensor, _mean, _std, 'test')














