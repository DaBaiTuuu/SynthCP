import os.path
import os.path as osp
import sys
from collections import deque
from tqdm import *

import click
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision
from PIL import Image
from options.fcn_options import BaseOptions

from models.fcn8 import VGG16_FCN8s
import data
import json
import pdb

def to_tensor_raw(im):
    return torch.from_numpy(np.array(im, np.int64, copy=False))


def fmt_array(arr, fmt=','):
    strs = ['{:.3f}'.format(x) for x in arr]
    return fmt.join(strs)

def fast_hist(a, b, n):
    k = (a >= 0) & (a < n)
    return np.bincount(n * a[k].astype(int) + b[k], minlength=n**2).reshape(n, n)

def result_stats(hist):
    acc_overall = np.diag(hist).sum() / hist.sum() * 100
    acc_percls = np.diag(hist) / (hist.sum(1) + 1e-8) * 100
    iu = np.diag(hist) / (hist.sum(1) + hist.sum(0) - np.diag(hist) + 1e-8) * 100
    freq = hist.sum(1) / hist.sum()
    fwIU = (freq[freq > 0] * iu[freq > 0]).sum()
    pix_percls = hist.sum(1)
    return acc_overall, acc_percls, iu, fwIU, pix_percls

ignore_label = 255
id2label = {-1: ignore_label, 0: ignore_label, 1: ignore_label, 2: ignore_label,
            3: ignore_label, 4: ignore_label, 5: ignore_label, 6: ignore_label,
            7: 0, 8: 1, 9: ignore_label, 10: ignore_label, 11: 2, 12: 3, 13: 4,
            14: ignore_label, 15: ignore_label, 16: ignore_label, 17: 5,
            18: ignore_label, 19: 6, 20: 7, 21: 8, 22: 9, 23: 10, 24: 11, 25: 12, 26: 13, 27: 14,
            28: 15, 29: ignore_label, 30: ignore_label, 31: 16, 32: 17, 33: 18}

#id2label_gta2cs = {}
#for k,v in id2label:
#    if v != ignore_label:
#        id2label_gta2cs[v] = k

# parse options
opt = BaseOptions().parse()
# print options to help debugging
print(' '.join(sys.argv))

# load the dataset
dataloader = data.create_dataloader(opt)

net = VGG16_FCN8s(num_cls=opt.label_nc, pretrained=False)
net.load_state_dict(torch.load(opt.model_path))
net.cuda()
net.eval()

hist = np.zeros((19, 19))
metrics = []
iterations = tqdm(enumerate(dataloader))
for i, data_i in iterations:
    # Clear out gradients

    # forward pass and compute loss
    im = data_i['image_seg'].cuda()
    label = data_i['label'].squeeze(1)
    preds = net(im)
    score = net(im).data
    _, preds = torch.max(score, 1)
    #pdb.set_trace()
    pred_path = data_i['label_path'][0].replace('gtFine', 'gtFinePred')
    os.makedirs(os.path.dirname(pred_path), exist_ok=True)
    Image.fromarray(np.uint8(preds.cpu().numpy()[0])).save(pred_path)

    hist = fast_hist(label.numpy().flatten(),
            preds.cpu().numpy().flatten(),
            19)
    acc_overall, acc_percls, iu, fwIU, pix_percls = result_stats(hist)
    iterations.set_postfix({'mIoU':' {:0.2f}  fwIoU: {:0.2f} pixel acc: {:0.2f} per cls acc: {:0.2f}'.format(
        np.nanmean(iu), fwIU, acc_overall, np.nanmean(acc_percls))})
    metrics.append([iu.tolist(), pix_percls.tolist(), fwIU, acc_overall, acc_percls.tolist()])
print()
with open(os.path.join('.', 'metrics.json'), 'w') as f:
    json.dump(metrics, f)
#print(','.join(classes))
#print(fmt_array(iu))
#print(np.nanmean(iu), fwIU, acc_overall, np.nanmean(acc_percls))
#print(np.mean(iu))
#print('Errors:', errs)
