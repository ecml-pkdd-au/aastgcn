import os
import numpy as np
import torch
import torch.utils.data
from sklearn.metrics import mean_absolute_error
from sklearn.metrics import mean_squared_error
from lib.metrics import masked_mape_np
from scipy.sparse.linalg import eigs
from sklearn.metrics import r2_score
from p_value_test import p_test
def re_normalization(x, mean, std):
    x = x * std + mean
    return x


def max_min_normalization(x, _max, _min):
    x = 1. * (x - _min)/(_max - _min)
    x = x * 2. - 1.
    return x


def re_max_min_normalization(x, _max, _min):
    x = (x + 1.) / 2.
    x = 1. * x * (_max - _min) + _min
    return x


def get_adjacency_matrix(distance_df_filename, num_of_vertices, id_filename=None):
    '''
    Parameters
    ----------
    distance_df_filename: str, path of the csv file contains edges information

    num_of_vertices: int, the number of vertices

    Returns
    ----------
    A: np.ndarray, adjacency matrix

    '''
    if 'npy' in distance_df_filename:

        adj_mx = np.load(distance_df_filename)

        return adj_mx, None

    else:

        import csv

        A = np.zeros((int(num_of_vertices), int(num_of_vertices)),
                     dtype=np.float32)

        distaneA = np.zeros((int(num_of_vertices), int(num_of_vertices)),
                            dtype=np.float32)

        if id_filename:

            with open(id_filename, 'r') as f:
                id_dict = {int(i): idx for idx, i in enumerate(f.read().strip().split('\n'))}  # 把节点id（idx）映射成从0开始的索引

            with open(distance_df_filename, 'r') as f:
                f.readline()
                reader = csv.reader(f)
                for row in reader:
                    if len(row) != 3:
                        continue
                    i, j, distance = int(row[0]), int(row[1]), float(row[2])
                    A[id_dict[i], id_dict[j]] = 1
                    distaneA[id_dict[i], id_dict[j]] = distance
            return A, distaneA

        else:

            with open(distance_df_filename, 'r') as f:
                f.readline()
                reader = csv.reader(f)
                for row in reader:
                    if len(row) != 3:
                        continue
                    i, j, distance = int(row[0]), int(row[1]), float(row[2])
                    A[i, j] = 1
                    distaneA[i, j] = distance
            return A, distaneA


#
# def scaled_Laplacian(W):
#     '''
#     compute \tilde{L}
#
#     Parameters
#     ----------
#     W: np.ndarray, shape is (N, N), N is the num of vertices
#
#     Returns
#     ----------
#     scaled_Laplacian: np.ndarray, shape (N, N)
#
#     '''
#
#     assert W.shape[0] == W.shape[1]
#
#     D = np.diag(np.sum(W, axis=1))
#
#     L = D - W
#
#     lambda_max = eigs(L, k=1, which='LR')[0].real
#
#     return (2 * L) / lambda_max - np.identity(W.shape[0])


# def cheb_polynomial(L_tilde, K):
#     '''
#     compute a list of chebyshev polynomials from T_0 to T_{K-1}
#
#     Parameters
#     ----------
#     L_tilde: scaled Laplacian, np.ndarray, shape (N, N)
#
#     K: the maximum order of chebyshev polynomials
#
#     Returns
#     ----------
#     cheb_polynomials: list(np.ndarray), length: K, from T_0 to T_{K-1}
#
#     '''
#
#     N = L_tilde.shape[0]
#
#     cheb_polynomials = [np.identity(N), L_tilde.copy()]
#
#     for i in range(2, K):
#         cheb_polynomials.append(2 * L_tilde * cheb_polynomials[i - 1] - cheb_polynomials[i - 2])
#
#     return cheb_polynomials


# def load_graphdata_channel1(graph_signal_matrix_filename, num_of_hours, num_of_days, num_of_weeks, DEVICE, batch_size, shuffle=True):
#     '''
#     :param graph_signal_matrix_filename: str
#     :param num_of_hours: int
#     :param num_of_days: int
#     :param num_of_weeks: int
#     :param DEVICE:
#     :param batch_size: int
#     :return:
#     three DataLoaders, each dataloader contains:
#     test_x_tensor: (B, N_n odes, in_feature, T_input)
#     test_decoder_input_tensor: (B, N_nodes, T_output)
#     test_target_tensor: (B, N_nodes, T_output)
#
#     '''
#
#     file = os.path.basename(graph_signal_matrix_filename).split('.')[0]
#
#     dirpath = os.path.dirname(graph_signal_matrix_filename)
#
#     filename = os.path.join(dirpath,
#                             file + '_r' + str(num_of_hours) + '_d' + str(num_of_days) + '_w' + str(num_of_weeks)) +'_astcgn'
#
#
#     file_data = np.load(filename + '.npz')
#     train_x = file_data['train_x']  # (10181, 307, 3, 12)
#     train_x = train_x[:, :, 0:1, :]
#     train_target = file_data['train_target']  # (10181, 307, 12)
#
#     val_x = file_data['val_x']
#     val_x = val_x[:, :, 0:1, :]
#     val_target = file_data['val_target']
#
#     test_x = file_data['test_x']
#     test_x = test_x[:, :, 0:1, :]
#     test_target = file_data['test_target']
#
#     mean = file_data['mean'][:, :, 0:1, :]  # (1, 1, 3, 1)
#     std = file_data['std'][:, :, 0:1, :]  # (1, 1, 3, 1)
#
#     # ------- train_loader -------
#     train_x_tensor = torch.from_numpy(train_x).type(torch.FloatTensor).to(DEVICE)  # (B, N, F, T)
#     train_target_tensor = torch.from_numpy(train_target).type(torch.FloatTensor).to(DEVICE)  # (B, N, T)
#
#     train_dataset = torch.utils.data.TensorDataset(train_x_tensor, train_target_tensor)
#
#     train_loader = torch.utils.data.DataLoader(train_dataset, batch_size=batch_size, shuffle=shuffle)
#
#     # ------- val_loader -------
#     val_x_tensor = torch.from_numpy(val_x).type(torch.FloatTensor).to(DEVICE)  # (B, N, F, T)
#     val_target_tensor = torch.from_numpy(val_target).type(torch.FloatTensor).to(DEVICE)  # (B, N, T)
#
#     val_dataset = torch.utils.data.TensorDataset(val_x_tensor, val_target_tensor)
#
#     val_loader = torch.utils.data.DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
#
#     # ------- test_loader -------
#     test_x_tensor = torch.from_numpy(test_x).type(torch.FloatTensor).to(DEVICE)  # (B, N, F, T)
#     test_target_tensor = torch.from_numpy(test_target).type(torch.FloatTensor).to(DEVICE)  # (B, N, T)
#
#     test_dataset = torch.utils.data.TensorDataset(test_x_tensor, test_target_tensor)
#
#     test_loader = torch.utils.data.DataLoader(test_dataset, batch_size=batch_size, shuffle=False)
#
#     # print
#     print('train:', train_x_tensor.size(), train_target_tensor.size())
#     print('val:', val_x_tensor.size(), val_target_tensor.size())
#     print('test:', test_x_tensor.size(), test_target_tensor.size())
#
#     return train_loader, train_target_tensor, val_loader, val_target_tensor, test_loader, test_target_tensor, mean, std


def compute_val_loss_mstgcn(net, val_loader, criterion, sw, epoch, limit=None):
    '''
    for rnn, compute mean loss on validation set
    :param net: model
    :param val_loader: torch.utils.data.utils.DataLoader
    :param criterion: torch.nn.MSELoss
    :param sw: tensorboardX.SummaryWriter
    :param global_step: int, current global_step
    :param limit: int,
    :return: val_loss
    '''

    net.train(False)  # ensure dropout layers are in evaluation mode

    with torch.no_grad():

        val_loader_length = len(val_loader)  # nb of batch

        tmp = []  # 记录了所有batch的loss

        for batch_index, batch_data in enumerate(val_loader):
            # print(batch_index)
            encoder_inputs, labels = batch_data
            outputs = net(encoder_inputs)
            # print('val_outputs:')
            # print(outputs)
            # print('val_labels:')
            # print(labels)
            loss = criterion(outputs, labels)  # 计算误差
            tmp.append(loss.item())
            # if batch_index % 100 == 0:
            #     print('validation batch %s / %s, loss: %.2f' % (batch_index + 1, val_loader_length, loss.item()))
            if (limit is not None) and batch_index >= limit:
                break

        validation_loss = sum(tmp) / len(tmp)
        sw.add_scalar('validation_loss', validation_loss, epoch)
    return validation_loss


def evaluate_on_test_mstgcn(net, test_loader, test_target_tensor, sw, epoch, _mean, _std):
    '''
    for rnn, compute MAE, RMSE, MAPE scores of the prediction for every time step on testing set.

    :param net: model
    :param test_loader: torch.utils.data.utils.DataLoader
    :param test_target_tensor: torch.tensor (B, N_nodes, T_output, out_feature)=(B, N_nodes, T_output, 1)
    :param sw:
    :param epoch: int, current epoch
    :param _mean: (1, 1, 3(features), 1)
    :param _std: (1, 1, 3(features), 1)
    '''

    net.train(False)  # ensure dropout layers are in test mode

    with torch.no_grad():

        test_loader_length = len(test_loader)

        test_target_tensor = test_target_tensor.cpu().numpy()

        prediction = []  # 存储所有batch的output

        for batch_index, batch_data in enumerate(test_loader):

            encoder_inputs, labels = batch_data

            outputs = net(encoder_inputs)

            prediction.append(outputs.detach().cpu().numpy())

            if batch_index % 100 == 0:
                print('predicting testing set batch %s / %s' % (batch_index + 1, test_loader_length))

        prediction = np.concatenate(prediction, 0)  # (batch, T', 1)
        prediction_length = prediction.shape[2]

        for i in range(prediction_length):
            assert test_target_tensor.shape[0] == prediction.shape[0]
            print('current epoch: %s, predict %s points' % (epoch, i))
            mae = mean_absolute_error(test_target_tensor[:, :, i], prediction[:, :, i])
            rmse = mean_squared_error(test_target_tensor[:, :, i], prediction[:, :, i]) ** 0.5
            mape = masked_mape_np(test_target_tensor[:, :, i], prediction[:, :, i], 0)
            print('MAE: %.2f' % (mae))
            print('RMSE: %.2f' % (rmse))
            print('MAPE: %.2f' % (mape))
            print()
            if sw:
                sw.add_scalar('MAE_%s_points' % (i), mae, epoch)
                sw.add_scalar('RMSE_%s_points' % (i), rmse, epoch)
                sw.add_scalar('MAPE_%s_points' % (i), mape, epoch)


def predict_and_save_results_mstgcn(net, data_loader, data_target_tensor, global_step, _mean, _std, params_path, type):
    '''

    :param net: nn.Module
    :param data_loader: torch.utils.data.utils.DataLoader
    :param data_target_tensor: tensor
    :param epoch: int
    :param _mean: (1, 1, 3, 1)
    :param _std: (1, 1, 3, 1)
    :param params_path: the path for saving the results
    :return:
    '''
    net.train(False)  # ensure dropout layers are in test mode

    with torch.no_grad():

        data_target_tensor = data_target_tensor.cpu().numpy()

        loader_length = len(data_loader)  # nb of batch

        prediction = []  # 存储所有batch的output

        input = []  # 存储所有batch的input

        for batch_index, batch_data in enumerate(data_loader):

            encoder_inputs, labels = batch_data

            input.append(encoder_inputs[:, :, 0:1].cpu().numpy())  # (batch, T', 1)

            outputs = net(encoder_inputs)
            # outputs = outputs.detach().cpu().numpy()
            # outputs = re_normalization(outputs, _mean, _std)
            # print('outputs.shape:{}'.format(outputs.shape))
            # prediction.append(outputs)

            prediction.append(outputs.detach().cpu().numpy())

            if batch_index % 100 == 0:
                print('predicting data set batch %s / %s' % (batch_index + 1, loader_length))
        # print('input.shape:{}'.format(input.shape))
        input = np.concatenate(input, 0)
        input = re_normalization(input, _mean, _std)

        # 这里实际上就是把每次的output拼接成 target格式的output，首先需要了解prediction内部格式，然后再拼接
        # print('prediction[0]:{}'.format(prediction[0]))
        # print('prediction[0].shape:{}'.format(prediction[0].shape)) # prediction[0].shape:(1, 32, 105, 12)

        # 在batch的维度对数组进行纵向拼接 (1, 32, 105, 12) (1, 32, 105, 12) (1, 32, 105, 12)...   =  (1, 481, 105, 12)
        prediction = np.concatenate(prediction, 0)  # (batch, T', 1)  prediction: ( 481, 105, 12)
        # print('prediction:', prediction.shape)

        # # 新增输出数据还原操作 # DONE
        prediction = re_normalization(prediction, _mean, _std)
        # print('prediction_unnormalization.shape:{}'.format(prediction.shape))  # prediction: (1, 481, 105, 12)
        # 去掉prediction还原过程中增加的第一个维度
        prediction = prediction.squeeze()
        # print('prediction_recover.shape:', prediction.shape) # (481,105,12)

        # 新增target数据还原操作 # DONE
        data_target_tensor = re_normalization(data_target_tensor,_mean,_std)
        # print('data_target_tensor_unnormalization.shape:{}'.format(data_target_tensor.shape))
        data_target_tensor = np.array(data_target_tensor).squeeze()
        # print('data_target_tensor_recover.shape:{}'.format(data_target_tensor.shape))


        # print('input:', input.shape) # (481, 105, 1, 12)
        # print('prediction:', prediction.shape) # (481, 105, 12)
        # print('data_target_tensor:', data_target_tensor.shape) # (481,105,12)
        output_filename = os.path.join(params_path, 'output_epoch_%s_%s' % (global_step, type))
        np.savez(output_filename, input=input, prediction=prediction, data_target_tensor=data_target_tensor)

        # 计算误差
        excel_list = []
        prediction_length = prediction.shape[2]

        for i in range(prediction_length):
            assert data_target_tensor.shape[0] == prediction.shape[0] # assert error for ISFD21 which the prediction shape is different from prediction
            print('current epoch: %s, predict %s points' % (global_step, i))

            # 结果检查
            # print('data_target_tensor:')
            # print(data_target_tensor[:, :, i])
            # print('prediction_tensor:')
            # print(prediction[:, :, i])

            # 原始ASTGCN评估方式
            mae = mean_absolute_error(data_target_tensor[:, :, i], prediction[:, :, i])
            rmse = mean_squared_error(data_target_tensor[:, :, i], prediction[:, :, i]) ** 0.5
            mape = masked_mape_np(data_target_tensor[:, :, i], prediction[:, :, i], 0)

            # 对齐STGCN的评估函数
            mae = np.mean(np.absolute(prediction[:, :, i] - data_target_tensor[:, :, i]))
            rmse = np.sqrt(np.mean(np.square(prediction[:, :, i] - data_target_tensor[:, :, i])))
            def cal_mape(y_true, y_pred): return np.mean(np.abs((y_pred - y_true) / y_true)) * 100
            mape = cal_mape(prediction[:, :, i], data_target_tensor[:, :, i])
            r2score = r2_score(data_target_tensor[:, :, i],prediction[:, :, i])
            # print('MAE: %.2f' % (mae))
            # print('RMSE: %.2f' % (rmse))
            # print('MAPE: %.2f' % (mape))
            print("MAE:{:.4f}".format(mae))
            print("RMSE:{:.4f}".format(rmse))
            print("MAE:{:.4f}".format(mape))
            print('R2_Score:{:.4f}'.format(r2score))
            excel_list.extend([mae, rmse, mape,r2score])

        # print overall results
        mae = mean_absolute_error(data_target_tensor.reshape(-1, 1), prediction.reshape(-1, 1))
        rmse = mean_squared_error(data_target_tensor.reshape(-1, 1), prediction.reshape(-1, 1)) ** 0.5
        mape = masked_mape_np(data_target_tensor.reshape(-1, 1), prediction.reshape(-1, 1), 0)
        r2score = r2_score(data_target_tensor.reshape(-1, 1), prediction.reshape(-1, 1))

        # print('all_target.shape:{}'.format(data_target_tensor.reshape(-1, 1).shape))
        # print('all_pred.shape:{}'.format(prediction.reshape(-1, 1).shape))
        # print('all MAE: %.4f' % (mae))
        # print('all RMSE: %.4f' % (rmse))
        # print('all MAPE: %.4f' % (mape))
        # print('all R2_Score: %.4f' %(r2score))
        # excel_list.extend([mae, rmse, mape,r2score])

        p_value = p_test(np.reshape(data_target_tensor, -1), np.reshape(prediction, -1))
        print('final result:')
        print('all RMSE: %.4f' % (rmse))
        print('all MAE: %.4f' % (mae))
        print('all MAPE: %.4f' % (mape))
        print('all P_value: %.4f' % (p_value))
        excel_list.extend([mae, rmse, mape, p_value])
        print(excel_list)


