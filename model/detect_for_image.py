import argparse
import time
from pathlib import Path

import cv2
import torch
import torch.backends.cudnn as cudnn
from numpy import random
import numpy as np

from models.experimental import attempt_load
from utils.datasets import LoadStreams, LoadImages, letterbox
from utils.general import check_img_size, check_requirements, check_imshow, non_max_suppression, apply_classifier, \
    scale_coords, xyxy2xywh, strip_optimizer, set_logging, increment_path
from utils.plots import plot_one_box
from utils.torch_utils import select_device, load_classifier, time_synchronized, TracedModel

class Detector:
    def __init__(self, path_weights, device, img_size, conf_thres, iou_thres):
        self.conf_thres = conf_thres
        self.iou_thres = iou_thres
        self.device = select_device(device)
        self.half = self.device.type != 'cpu'  #half precision only supported on CUDA
        self.model = attempt_load(path_weights, map_location=self.device) # load FP32 model
        self.stride = int(self.model.stride.max())  #model stride
        self.img_size = check_img_size(img_size, s=self.stride)
        if self.half:
            self.model.half()  # to FP16

        if self.device.type != 'cpu':
            self.model(torch.zeros(1, 3, img_size, img_size).to(self.device).type_as(next(self.model.parameters())))  #run once
    
    def detect(self, img_arr):
        img_arr_resized = letterbox(img_arr, self.img_size, stride=self.stride)[0]

        # Convert
        img_arr_resized = img_arr_resized[:, :, ::-1].transpose(2, 0, 1)  # BGR to RGB, to 3x416x416
        img_arr_resized = np.ascontiguousarray(img_arr_resized)

        img_arr_resized = torch.from_numpy(img_arr_resized).to(self.device)
        img_arr_resized = img_arr_resized.half() if self.half else img_arr_resized.float()  # uint8 to fp16/32
        img_arr_resized /= 255.0  # 0 - 255 to 0.0 - 1.0
        if img_arr_resized.ndimension() == 3:
            img_arr_resized = img_arr_resized.unsqueeze(0)

        # Inference
        with torch.no_grad():   # Calculating gradients would cause a GPU memory leak
            pred = self.model(img_arr_resized, augment=True)[0]

        # Apply NMS
        pred = non_max_suppression(pred, self.conf_thres, self.iou_thres, agnostic=True)
        
        result = []
        for det in pred:
            det[:, :4] = scale_coords(img_arr_resized.shape[2:], det[:, :4], img_arr.shape).round()
            result.append(det.cpu().detach().numpy())

        return result

if __name__ == '__main__':
    img_arr = cv2.imread("../../input/tmp-one-image/tmp_run2.png")
    detector = Detector("/kaggle/working/yolov7/runs/train/exp/weights/best.pt", "0", 1024, 0.25, 0.45)
    print(detector.detect(img_arr))
