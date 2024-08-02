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