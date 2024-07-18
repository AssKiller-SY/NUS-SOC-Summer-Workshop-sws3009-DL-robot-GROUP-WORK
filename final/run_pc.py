#!/usr/bin/python3

from onnx_tf.backend import prepare
import cv2
import numpy as np
import onnx
import onnxruntime as ort
from urllib import request
from simple_pid import PID
import socket
import time

def area_of(left_top, right_bottom):
    hw = np.clip(right_bottom - left_top, 0.0, None)
    return hw[..., 0] * hw[..., 1]

def iou_of(boxes0, boxes1, eps=1e-5):
    overlap_left_top = np.maximum(boxes0[..., :2], boxes1[..., :2])
    overlap_right_bottom = np.minimum(boxes0[..., 2:], boxes1[..., 2:])
    overlap_area = area_of(overlap_left_top, overlap_right_bottom)
    area0 = area_of(boxes0[..., :2], boxes0[..., 2:])
    area1 = area_of(boxes1[..., :2], boxes1[..., 2:])
    return overlap_area / (area0 + area1 - overlap_area + eps)

def hard_nms(box_scores, iou_threshold, top_k=-1, candidate_size=200):
    scores = box_scores[:, -1]
    boxes = box_scores[:, :-1]
    picked = []
    indexes = np.argsort(scores)
    indexes = indexes[-candidate_size:]
    while len(indexes) > 0:
        current = indexes[-1]
        picked.append(current)
        if 0 < top_k == len(picked) or len(indexes) == 1:
            break
        current_box = boxes[current, :]
        indexes = indexes[:-1]
        rest_boxes = boxes[indexes, :]
        iou = iou_of(rest_boxes, np.expand_dims(current_box, axis=0),)
        indexes = indexes[iou <= iou_threshold]
    return box_scores[picked, :]

def predict(width, height, confidences, boxes, prob_threshold, iou_threshold=0.5, top_k=-1):
    boxes = boxes[0]
    confidences = confidences[0]
    picked_box_probs = []
    picked_labels = []
    for class_index in range(1, confidences.shape[1]):
        probs = confidences[:, class_index]
        mask = probs > prob_threshold
        probs = probs[mask]
        if probs.shape[0] == 0:
            continue
        subset_boxes = boxes[mask, :]
        box_probs = np.concatenate([subset_boxes, probs.reshape(-1, 1)], axis=1)
        box_probs = hard_nms(box_probs, iou_threshold=iou_threshold, top_k=top_k,)
        picked_box_probs.append(box_probs)
        picked_labels.extend([class_index] * box_probs.shape[0])
    if not picked_box_probs:
        return np.array([]), np.array([]), np.array([])
    picked_box_probs = np.concatenate(picked_box_probs)
    picked_box_probs[:, 0] *= width
    picked_box_probs[:, 1] *= height
    picked_box_probs[:, 2] *= width
    picked_box_probs[:, 3] *= height
    return picked_box_probs[:, :4].astype(np.int32), np.array(picked_labels), picked_box_probs[:, 4]

onnx_path = r"D:\SOC3\ultra_light_320.onnx"
onnx_model = onnx.load(onnx_path)
predictor = prepare(onnx_model, device="GPU")
ort_session = ort.InferenceSession(onnx_path)
input_name = ort_session.get_inputs()[0].name

def detect_first_face(frame):
    h, w, _ = frame.shape
    img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img = cv2.resize(img, (320, 240))
    img_mean = np.array([127, 127, 127])
    img = (img - img_mean) / 128
    img = np.transpose(img, [2, 0, 1])
    img = np.expand_dims(img, axis=0)
    img = img.astype(np.float32)
    confidences, boxes = ort_session.run(None, {input_name: img})
    boxes, _, _ = predict(w, h, confidences, boxes, 0.7)
    for i in range(boxes.shape[0]):
        box = boxes[i, :]
        x1, y1, x2, y2 = box
        cv2.rectangle(frame, (x1, y1), (x2, y2), (80, 18, 236), 2)
        cv2.rectangle(frame, (x1, y2 - 20), (x2, y2), (80, 18, 236), cv2.FILLED)
        cv2.putText(frame, "PERSON", (x1 + 6, y2 - 6), cv2.FONT_HERSHEY_DUPLEX, 0.5, (255, 255, 255), 1)
        return ((x1 + x2) * 0.5 / w - 0.5) * 2.0, x2-x1
    return None

def read_from_mjpg_stream(url):
    try:
        stream = request.urlopen(url)
    except Exception as e:
        print(f"Error opening URL: {e}")
        return
    bytes = b""
    while True:
        try:
            bytes += stream.read(1024)
            a = bytes.find(b"\xff\xd8")
            b = bytes.find(b"\xff\xd9")
            if a != -1 and b != -1:
                jpg = bytes[a:b+2]
                bytes = bytes[b+2:]
                frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                yield frame
        except Exception as e:
            print(f"Error reading from stream: {e}")
            break

if __name__ == "__main__":
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('172.25.109.5', 12346)) #本机地址
    server_socket.listen(5)
    robot_socket = None
    print(">>>等待连接")
    while True:
        robot_socket, robot_address = server_socket.accept()
        print(f"机器人连接来自: {robot_address}")
        break
    print(">>>连接成功")
    time.sleep(5)

    # pid = PID(0.5, 0.2, 0.0, setpoint=0)
    url = "http://172.25.96.245:8000/stream.mjpg" #树莓派地址

    cnt = 0
    face_len = 0
    sum1 = 0
    sum2 = 0
    flag = 0
    fre1 = 60
    fre2 = 40
    cnt_find = fre1
    for frame in read_from_mjpg_stream(url=url):
        face_center_ndc = detect_first_face(frame)
        cv2.imshow("Face Detection", frame)
        if face_center_ndc is None:
            if cnt_find == fre1:
                robot_socket.send('q'.encode())
                print('>>>find no face send q')
                cnt_find = 0
            cnt_find += 1
        else:
            cnt_find = 0
            face_mid , face_len = face_center_ndc
            sum1 += face_mid
            sum2 += face_len
            cnt += 1
            if(cnt == fre2):
                bias = sum1/fre2
                face = sum2/fre2
                sum1 = 0
                sum2 = 0
                cnt = 0
                flag = 1
        
        if cnt == 0:
            print("-"*100)
            if bias <= 0.45 and bias >= -0.45 and face > 60:
                robot_socket.send('stop'.encode())
                print('>>>stop')
                break
            elif bias <= 0.35 and bias >= -0.35 and face <= 60:
                robot_socket.send('f'.encode())
                print('>>>f')
            else:
                if bias > 0.1:
                    robot_socket.send('d'.encode())
                    print('>>>d')
                    
                elif bias < -0.1:
                    robot_socket.send('a'.encode())
                    print('>>>a')
                    
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cv2.destroyAllWindows()

