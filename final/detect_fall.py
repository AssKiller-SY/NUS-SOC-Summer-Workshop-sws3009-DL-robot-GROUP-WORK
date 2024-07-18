# -*-coding: utf-8 -*-
"""Run inference with a YOLOv5 model on images, videos, directories, streams

Usage:
    $ python path/to/detect.py --source path/to/img.jpg --weights yolov5s.pt --img 640
"""
import sys
import os
import socket
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import cv2
import argparse
import numpy as np
from typing import List
from utils.datasets import LoadImages
from pybaseutils import file_utils, image_utils
from engine.inference import yolov5
count_down = 0
flag = 0
class Yolov5Detector(yolov5.YOLOv5):
    def __init__(self,
                 weights='yolov5s.pt',  # model.pt path(s)
                 imgsz=640,  # inference size (pixels)
                 conf_thres=0.5,  # confidence threshold
                 iou_thres=0.5,  # NMS IOU threshold
                 max_det=1000,  # maximum detections per image
                 class_name=None,  # filter by class: --class 0, or --class 0 2 3
                 classes=None,  # filter by class: --class 0, or --class 0 2 3
                 agnostic_nms=False,  # class-agnostic NMS
                 augment=False,  # augmented inference
                 half=False,  # use FP16 half-precision inference
                 visualize=False,  # visualize features
                 batch_size=4,
                 device='cuda:0',  # cuda device, i.e. 0 or 0,1,2,3 or cpu
                 fix_inputs=False,
                 ):
        super(Yolov5Detector, self).__init__(weights=weights,  # model.pt path(s)
                                             imgsz=imgsz,  # inference size (pixels)
                                             conf_thres=conf_thres,  # confidence threshold
                                             iou_thres=iou_thres,  # NMS IOU threshold
                                             max_det=max_det,  # maximum detections per image
                                             class_name=class_name,  # filter by class: --class 0, or --class 0 2 3
                                             classes=classes,  # filter by class: --class 0, or --class 0 2 3
                                             agnostic_nms=agnostic_nms,  # class-agnostic NMS
                                             augment=augment,  # augmented inference
                                             half=half,  # use FP16 half-precision inference
                                             visualize=visualize,  # visualize features
                                             batch_size=batch_size,
                                             device=device,  # cuda device, i.e. 0 or 0,1,2,3 or cpu
                                             fix_inputs=fix_inputs)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect(('172.25.96.245', 12345))  # 替换为树莓派IP和端口

    def start_capture(self, video_file, save_video=None, detect_freq=1, vis=True):
        video_cap = image_utils.get_video_capture(video_file)
        width, height, numFrames, fps = image_utils.get_video_info(video_cap)
        if save_video:
            self.video_writer = image_utils.get_video_writer(save_video, width, height, fps)
        count = 0
        while True:
            if count % detect_freq == 0:
                if isinstance(video_file, str): video_cap.set(cv2.CAP_PROP_POS_FRAMES, count)
                isSuccess, frame = video_cap.read()
                if not isSuccess:
                    break
                dets = self.detect(frame, vis=False)
                frame = self.draw_result([frame], dets, thickness=2, fontScale=1.0, delay=10, vis=vis)[0]
            if save_video:
                self.video_writer.write(frame)
            count += 1
        video_cap.release()

    def detect(self, image: List[np.ndarray] or np.ndarray, vis: bool = False) -> List[List]:
        if isinstance(image, np.ndarray): image = [image]
        dets = super().inference(image)
        if vis:
            self.draw_result(image, dets)
        return dets

    def detect_image_dir(self, image_dir, out_dir=None, vis=True):
        # Dataloader
        dataset = file_utils.get_files_lists(image_dir)
        # Run inference
        for path in dataset:
            print(path)
            image = cv2.imread(path)  # BGR
            # rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            dets = self.detect(image, vis=False)
            image = self.draw_result([image], dets, vis=vis)[0]
            if out_dir:
                out_file = file_utils.create_dir(out_dir, None, os.path.basename(path))
                print("save result:{}".format(out_file))
                cv2.imwrite(out_file, image)

    def draw_result(self, image: List[np.ndarray] or np.ndarray, dets, thickness=2, fontScale=1.0, delay=0, vis=True):
        vis_image = []
        for i in range(len(dets)):
            image = self.draw_image(image[i], dets[i], thickness=thickness, fontScale=fontScale, delay=delay, vis=vis)
            vis_image.append(image)
        return vis_image

    def draw_image(self, image, dets, thickness=1, fontScale=1.0, delay=0, vis=True):
        # image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        # (xmin,ymin,xmax,ymax,conf, cls)
        boxes = dets[:, 0:4]
        conf = dets[:, 4:5]
        cls = dets[:, 5]
        labels = [int(c) for c in cls]
        image_utils.draw_image_detection_boxes(image, boxes, conf, labels, class_name=self.names,
                                               thickness=thickness, fontScale=fontScale)
        global flag
        global count_down
        if len(labels) > 0:
            if flag==0 and 2 in labels:
                count_down += 1
                if count_down >= 10:
                    print("DETECT SOMEONE IS FALLING DOWN!!!")
                    self.sock.send(b'start1')
                    flag = 1
                    
            else:
                count_down = 0
        # for *box, conf, cls in reversed(dets):
        #     c = int(cls)  # integer class
        #     label = "{}{:.2f}".format(self.names[c], conf)
        #     plot_one_box(box, image, label=label, color=colors(c, True), line_thickness=2)
        if vis: image_utils.cv_show_image("image", image, use_rgb=False, delay=delay)
        return image


def parse_opt():
    image_dir = r'D:\Desktop\sws3009\yolov5\data\test_image'  # 测试图片的目录
    out_dir = r"D:\Desktop\sws3009\yolov5\runs\test-result"  # 保存检测结果
    # weights = r"D:\Desktop\sws3009\yolov5\data\model\yolov5s_640\weights\best.pt"  # 模型文件
    # weights = r"D:\Desktop\sws3009\yolov5\data\model\yolov5s05_320\weights\best.pt"
    weights = r"D:\Desktop\sws3009\yolov5\data\model\yolov5s05_416\weights\best.pt"  # 模型文件
    imgsz = 640
    video_file = None  # video_file is None表示进行图片测试
    video_file = r"D:\Desktop\sws3009\yolov5\data\test-video.mp4"  # 视频文件测试
    video_file = "0"  # 摄像头测试
    parser = argparse.ArgumentParser()
    parser.add_argument('--weights', nargs='+', type=str, default=weights, help='model.pt')
    parser.add_argument('--image_dir', type=str, default=image_dir, help='file/dir/URL/glob, 0 for webcam')
    parser.add_argument('--video_file', type=str, default=video_file, help='camera id or video file')
    parser.add_argument('--out_dir', type=str, default=out_dir, help='save det result image')
    parser.add_argument('--imgsz', '--img', '--img-size', type=int, default=imgsz, help='inference size (pixels)')
    parser.add_argument('--conf-thres', type=float, default=0.5, help='confidence threshold')
    parser.add_argument('--iou-thres', type=float, default=0.5, help='NMS IoU threshold')
    parser.add_argument('--max-det', type=int, default=1000, help='maximum detections per image')
    parser.add_argument('--device', default='cpu', help='cuda device, i.e. 0 or 0,1,2,3 or cpu')
    parser.add_argument('--classes', nargs='+', type=int, help='filter by class: --class 0, or --class 0 2 3')
    parser.add_argument('--class_name', nargs='+', type=list, default=None)
    parser.add_argument('--agnostic-nms', action='store_true', help='class-agnostic NMS')
    parser.add_argument('--augment', action='store_true', help='augmented inference')
    opt = parser.parse_args()
    return opt


if __name__ == "__main__":
    opt = parse_opt()
    d = Yolov5Detector(weights=opt.weights,  # model.pt path(s)
                       imgsz=opt.imgsz,  # inference size (pixels)
                       conf_thres=opt.conf_thres,  # confidence threshold
                       iou_thres=opt.iou_thres,  # NMS IOU threshold
                       max_det=opt.max_det,  # maximum detections per image
                       class_name=opt.class_name,  # filter by class: --class 0, or --class 0 2 3
                       classes=opt.classes,  # filter by class: --class 0, or --class 0 2 3
                       agnostic_nms=opt.agnostic_nms,  # class-agnostic NMS
                       augment=opt.augment,  # augmented inference
                       device=opt.device,  # cuda device, i.e. 0 or 0,1,2,3 or cpu
                       )
    if isinstance(opt.video_file, str) or isinstance(opt.video_file, int):
        opt.video_file = str(opt.video_file)
        if len(opt.video_file) == 1: opt.video_file = int(opt.video_file)
        # save_video = os.path.join(opt.out_dir, "result.avi") if opt.out_dir else None
        d.start_capture(opt.video_file, save_video=None, detect_freq=1, vis=True)
    else:
        d.detect_image_dir(opt.image_dir, opt.out_dir, vis=True)
