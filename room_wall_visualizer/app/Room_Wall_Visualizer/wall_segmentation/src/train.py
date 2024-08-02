import os
import torch
import torch.nn as nn
from utils.constants import TOTAL_NUM_ITER, NUM_ITER_PER_EPOCH, OPTIMIZER_PARAMETERS, DEVICE
from utils.utils import pixel_acc
from tqdm import tqdm


def train_one_epoch(segmentation_module, iterator, optimizers, epoch, crit, writer):
    """
    Train the segmentation module for one epoch.

    Parameters:
    segmentation_module (nn.Module): The segmentation model.
    iterator (iter): Iterator for the dataset.
    optimizers (tuple): Tuple of encoder and decoder optimizers.
    epoch (int): Current epoch number.
    crit (nn.Module): Loss function.
    writer (SummaryWriter): Tensorboard summary writer.
    """

    segmentation_module.train()

    # Processing each batch of the data, assume that NUM_ITER_PER_EPOCH is set the 5000, the number of data in the dataset is 20000, then the number of batches is 20000/5000 = 4
    for i in tqdm(range(NUM_ITER_PER_EPOCH)):
        # load a batch of data
        batch_data = next(iterator)[0]  # Because the batch size in the dataloader is 1, but the batch is created in TrainDataset
        segmentation_module.zero_grad() 
        
        # adjust learning rate (learning rate "poly") 
        curr_iter = i + (epoch - 1) * NUM_ITER_PER_EPOCH
        lr_encoder, _ = adjust_learning_rate(optimizers, curr_iter)
                
        # forward pass
        pred = segmentation_module(batch_data)

        # Calculate loss and accuracy
        loss = crit(pred, batch_data['seg_label'].to(DEVICE))
        acc = pixel_acc(pred, batch_data['seg_label'].to(DEVICE))
               
        loss = loss.mean()
        acc = acc.mean()

        # Backward pass
        loss.backward()
        for optimizer in optimizers:
            optimizer.step()

        # update average loss and acc
        writer.add_scalar('Learning rate', lr_encoder, curr_iter)
        writer.add_scalar('Training loss', loss.data.item(), curr_iter)
        writer.add_scalar('Training accuracy', acc.data.item(), curr_iter)


def checkpoint(nets, epoch, checkpoint_dir_path, is_best_epoch): 
    """
        Function for saving encoder and decoder weights into a file
        
        Parameters:
        nets (tuple): Tuple of encoder, decoder, and criteria networks.
        epoch (int): Current epoch number.
        checkpoint_dir_path (str): Directory path to save checkpoints.
        is_best_epoch (bool): Whether the current epoch is the best one.
    """
    print('Saving checkpoints...')
    net_encoder, net_decoder, _ = nets

    dict_encoder = net_encoder.state_dict()
    dict_decoder = net_decoder.state_dict()
    
    torch.save(dict_encoder, os.path.join(checkpoint_dir_path, f'encoder_epoch_{epoch}.pth'))
    torch.save(dict_decoder, os.path.join(checkpoint_dir_path, f'decoder_epoch_{epoch}.pth'))
    
    previous_encoder_epoch = os.path.join(checkpoint_dir_path, f'encoder_epoch_{epoch - 1}.pth')
    if os.path.exists(previous_encoder_epoch):
        os.remove(previous_encoder_epoch)
        
    previous_decoder_epoch = os.path.join(checkpoint_dir_path, f'decoder_epoch_{epoch - 1}.pth')
    if os.path.exists(previous_decoder_epoch):
        os.remove(previous_decoder_epoch)
    
    if is_best_epoch:
        prev_best_models = [os.path.join(checkpoint_dir_path, x) for x in os.listdir(checkpoint_dir_path) if x.startswith('best_')]
        for model_path in prev_best_models:
            os.remove(model_path)
        torch.save(dict_encoder, os.path.join(checkpoint_dir_path, f'best_encoder_epoch_{epoch}.pth'))
        torch.save(dict_decoder, os.path.join(checkpoint_dir_path, f'best_decoder_epoch_{epoch}.pth'))


def group_weight(module):
    """
    Group weights and biases of a network into individual groups for training.

    Parameters:
    module (nn.Module): The network module.

    Returns:
    list: List of dictionaries with grouped parameters.
    """
    group_decay = []
    group_no_decay = []

    for m in module.modules():
        if isinstance(m, (nn.Linear, nn.modules.conv._ConvNd)):
            group_decay.append(m.weight)
            if m.bias is not None:
                group_no_decay.append(m.bias)

        elif isinstance(m, nn.modules.batchnorm._BatchNorm):
            if m.weight is not None:
                group_no_decay.append(m.weight)
            if m.bias is not None:
                group_no_decay.append(m.bias)

    return [
        dict(params=group_decay),
        dict(params=group_no_decay, weight_decay=0),
    ]


def create_optimizers(nets, optim_parameters):
    """
    Create individual optimizers for encoder and decoder.

    Parameters:
    nets (tuple): Tuple of encoder, decoder, and criteria networks.
    optim_parameters (dict): Dictionary of optimizer parameters.

    Returns:
    tuple: Encoder and decoder optimizers.
    """
    (net_encoder, net_decoder, crit) = nets
    
    optimizer_encoder = torch.optim.SGD(group_weight(net_encoder),
                                        lr=optim_parameters["LEARNING_RATE"],
                                        momentum=optim_parameters["MOMENTUM"],
                                        weight_decay=optim_parameters["WEIGHT_DECAY"])
    
    optimizer_decoder = torch.optim.SGD(group_weight(net_decoder),
                                        lr=optim_parameters["LEARNING_RATE"],
                                        momentum=optim_parameters["MOMENTUM"],
                                        weight_decay=optim_parameters["WEIGHT_DECAY"])
        
    return optimizer_encoder, optimizer_decoder


def adjust_learning_rate(optimizers, curr_iter):
    """
    Adjust the learning rate for each iteration.

    Parameters:
    optimizers (tuple): Tuple of encoder and decoder optimizers.
    curr_iter (int): Current iteration number.
    total_num_iter (int): Total number of iterations.
    start_lr (float): Initial learning rate.

    Returns:
    tuple: Updated learning rates for encoder and decoder.
    """
    scale_running_lr = ((1 - curr_iter/TOTAL_NUM_ITER) ** 0.9)
    start_lr = OPTIMIZER_PARAMETERS["LEARNING_RATE"]

    lr_encoder = start_lr * scale_running_lr
    lr_decoder = start_lr * scale_running_lr

    (optimizer_encoder, optimizer_decoder) = optimizers
    for param_group in optimizer_encoder.param_groups:
        param_group['lr'] = lr_encoder
    for param_group in optimizer_decoder.param_groups:
        param_group['lr'] = lr_decoder

    return lr_encoder, lr_decoder