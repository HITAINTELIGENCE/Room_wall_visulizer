"""
Chuẩn bị cho quá trình training

    Lựa chọn device: PyTorch yêu cầu lựa chọn cụ thể device sẽ train và yêu cầu người dùng tự move dữ liệu, mô hình vào device đã lựa chọn. Device có thể là "cuda" - tức là GPU NVIDIA hoặc "cpu".
    Định nghĩa DataLoader, khác với Dataset là cách đọc dữ liệu từ ổ cứng, DataLoader ghép nhiều điểm dữ liệu vào cùng nhau tạo thành 1 batch để đưa vào train mô hình. Lưu ý thêm: batch_size nên đặt là 4, 8, 16, 32, ... và nên để lớn nhất có thể
    Khởi tạo mô hình
    Khởi tạo hàm loss
    Khởi tạo thuật toán tối ưu (optimizer)
    Khởi tạo các độ đo sẽ sử dụng để đánh giá hiệu năng của mô hình. Phần này sẽ sử dụng các hàm độ đo Dice và IoU được lập trình sẵn trong thư viện torchmetrics
    Khởi tạo từng AverageMeter để lưu lại giá trị của từng độ đo, giá trị hàm loss, thời gian train, ... trong suốt quá trình train
"""
import json
import os
import shutil
import pickle
import torch
import torch.nn as nn
from torch.utils.tensorboard import SummaryWriter

from models.pspnet import PSPNet, build_encoder, build_decoder
from models.dataset import TrainDataset, ValDataset
from utils.constants import NUM_EPOCHS, OPTIMIZER_PARAMETERS, DEVICE, NUM_WORKERS, ODGT_TRAINING, BATCH_PER_GPU, ODGT_EVALUTATION
from src.train import create_optimizers, train_one_epoch, checkpoint
from src.eval import validation_step
from utils.utils import not_None_collate


def main_train(ckpt_dir_path,
               data_root_path,
               continue_training=False,
               encoder_model="resnet50-dilated",
               path_encoder_weights="",
               path_decoder_weights=""):
    """
        Main function for training original encoder/decoder architecture
    """
    # Encoder/Decoder weights
    if continue_training:
        last_epoch = [int(x.split('.')[0].split('_')[-1]) for x in os.listdir(ckpt_dir_path) if x.startswith('encoder_epoch_')][0]
        path_encoder_weights = os.path.join(ckpt_dir_path, f'encoder_epoch_{last_epoch}.pth')
        path_decoder_weights = os.path.join(ckpt_dir_path, f'decoder_epoch_{last_epoch}.pth')
        print(f"The training will continue from {last_epoch + 1} epoch...")
    else:
        last_epoch = 0
        if os.path.exists(ckpt_dir_path):
            shutil.rmtree(ckpt_dir_path)
        os.mkdir(ckpt_dir_path)

    net_encoder = build_encoder(path_encoder_weights, encoder_model)
    net_decoder = build_decoder(path_decoder_weights)

    # Loại bỏ các nhãn có giá trị -1 khỏi quá trình train
    crit = nn.NLLLoss(ignore_index=-1)

    # Segmentation Module
    segmentation_module = PSPNet(net_encoder, net_decoder).to(DEVICE)

    # Dataset and Loader
    dataset_train = TrainDataset(data_root_path, ODGT_TRAINING, batch_per_gpu=BATCH_PER_GPU)

    loader_train = torch.utils.data.DataLoader(dataset_train,
                                               batch_size=1,  # batch is created in TrainDataset
                                               shuffle=False,
                                               collate_fn=not_None_collate,
                                               num_workers=NUM_WORKERS,
                                               drop_last=True,
                                               pin_memory=True)
    
    # Create training loader iterator
    iterator_train = iter(loader_train)
    
    dataset_val = ValDataset(data_root_path, ODGT_EVALUTATION)
    loader_val = torch.utils.data.DataLoader(dataset_val,
                                             batch_size=1,  # it has to be 1, because images are not the same size
                                             shuffle=False,
                                             collate_fn=lambda x: x,
                                             drop_last=True)

    # Set up optimizers
    nets = (net_encoder, net_decoder, crit)
    optimizers = create_optimizers(nets, OPTIMIZER_PARAMETERS)

    # Tensorboard initialization
    writer = SummaryWriter(os.path.join(ckpt_dir_path, 'tensorboard'))

    print('Starting training')
    # Main loop of certain number of epochs
    path_train_metadata = os.path.join(ckpt_dir_path, 'training_metadata.pkl')
    if os.path.exists(path_train_metadata):
        with open(path_train_metadata, 'rb') as f:
            train_metadata = pickle.load(f)
    else:
        train_metadata = {'best_acc': 0, 'best_IOU': 0}

    for epoch in range(last_epoch, NUM_EPOCHS):
        print(f'Training epoch {epoch + 1}/{NUM_EPOCHS}...')
        train_one_epoch(segmentation_module, iterator_train, optimizers, epoch + 1, crit, writer)
        
        print(f'Starting evaluation after epoch {epoch + 1}')
        acc, IOU = validation_step(segmentation_module, loader_val, writer, epoch + 1)
        print(f'Epoch {epoch + 1} - Accuracy: {acc:.2f}, IoU: {IOU:.2f}')
        print('Evaluation Done!')
                
        if acc > train_metadata['best_acc']:
            train_metadata['best_acc'] = acc
            train_metadata['best_IOU'] = IOU
            save_best = True
            with open(path_train_metadata, 'wb') as f:
                pickle.dump(train_metadata, f)
            print(f'Epoch {epoch + 1} is the new best epoch!')
        else:
            save_best = False
        checkpoint(nets, epoch + 1, ckpt_dir_path, save_best)

    writer.close()
    print('Training Done!')
    print(f'best epoch {epoch + 1} - best_acc: {acc:.2f}, best_IOU: {IOU:.2f}')
    

if __name__ == '__main__':

    with open('configs/config.json', 'r') as f:
        config = json.load(f)

    ckpt_dir = os.path.join('ckpt', config["CHECKPOINT_DIR_PATH"])
    data_root_path = config["ROOT_DATASET"]
    continue_training = config["CONTINUE_TRAINING"]
    path_encoder_weights = config.get("MODEL_ENCODER_WEIGHTS_PATH", "")
    path_decoder_weights = config.get("MODEL_DECODER_WEIGHTS_PATH", "")

    encoder_model = config.get("ENCODER_MODEL", "resnet50-dilated")
    main_train(ckpt_dir, data_root_path, continue_training, encoder_model, path_encoder_weights, path_decoder_weights)
