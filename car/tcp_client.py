import socket
import time
import cv2
import numpy as np
import threading
import argparse
import ipaddress
import sys

(major_ver, minor_ver, subminor_ver) = (cv2.__version__).split('.')
print(cv2.__version__)

tracker_types = ['BOOSTING', 'MIL','KCF', 'TLD', 'MEDIANFLOW', 'CSRT', 'MOSSE']
tracker_type = tracker_types[5]

parser = argparse.ArgumentParser(description='Connect to raspberry pi using IP address')
parser.add_argument('host', metavar='h', type=str, help='ip address of pi')
args = parser.parse_args()

def init_tracker(frame, bbox):
    if int(major_ver) < 4 and int(minor_ver) < 3:
        tracker = cv2.cv2.Tracker_create(tracker_type)
    else:
        if tracker_type == 'BOOSTING':
            tracker = cv2.TrackerBoosting_create()
        if tracker_type == 'MIL':
            tracker = cv2.TrackerMIL_create()
        if tracker_type == 'KCF':
            tracker = cv2.TrackerKCF_create()
        if tracker_type == 'TLD':
            tracker = cv2.TrackerTLD_create()
        if tracker_type == 'MEDIANFLOW':
            tracker = cv2.TrackerMedianFlow_create()
        if tracker_type == 'CSRT':
            tracker = cv2.TrackerCSRT_create()
        if tracker_type == 'MOSSE':
            tracker = cv2.legacy.TrackerMOSSE_create()
    tracker.init(frame, bbox)
    return tracker

class CameraBufferCleanerThread(threading.Thread):
    def __init__(self, camera, name='camera-buffer-cleaner-thread'):
        self.camera = camera
        self.last_frame = None
        super(CameraBufferCleanerThread, self).__init__(name=name)
        self.start()

    def run(self):
        while True:
            ret, self.last_frame = self.camera.read()
            
def get_decision(bbox):
    x, w = int(bbox[0]), int(bbox[2])
    cx = int(x + w // 2)

    # Calculate slope
    if cx < width // 2 - 50: 
        return "Turn left"
    elif cx > width // 2 + 50: 
        return "Turn right"
    else:  
        return "Go straight"

# Define host and port
try:
    HOST = str(ipaddress.ip_address(args.host))
    print(f"Valid IP address: {HOST}")
except ValueError:
    sys.exit(f"Invalid IP address: {args.host}")
PORT = 65432

cap = cv2.VideoCapture(f"rtsp://{HOST}:8554/video_stream")
cam_cleaner = CameraBufferCleanerThread(cap)

net = cv2.dnn.readNetFromONNX("best.onnx")
classes = ['obstacle']

bbox = None
tracking = False
obj_label = ""

decision = ""

# Create a socket object
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
    # Connect to server
    client_socket.connect((HOST, PORT))
    
    # Main loop
    while True:
        # Read frame from webcam
        if cam_cleaner.last_frame is None:
            continue

        frame = cam_cleaner.last_frame

        # Start timer
        timer = cv2.getTickCount()

        if tracking:
            ok, bbox = tracker.update(frame)
            # Draw bounding box
            if ok:
                x, y, w, h = int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])
                cx = int(x + w // 2)
                cy = int(y + h // 2)
                cv2.line(frame, (int(cx), int(cy)), (width // 2, height), (255,255,255), 2)

                decision = get_decision(bbox) 
                
                client_socket.sendall(decision.encode())
                text = obj_label + "{:.2f}".format(conf)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (255,0,0), 2)
                cv2.putText(frame, text, (x,y-2),cv2.FONT_HERSHEY_COMPLEX, 0.7,(255,0,255),2)
                cv2.putText(frame, decision, (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 2) 
            else :
                tracking = False
        else: 
            # Detect objects using YOLOv5
            height, width, _ = frame.shape
            blob = cv2.dnn.blobFromImage(frame, 1/255, (640, 640), (0, 0, 0), True, crop=False)
            net.setInput(blob)
            detections = net.forward()[0]
            
            classes_ids = []
            confidences = []
            boxes = []
            rows = detections.shape[0]

            x_scale = width/640
            y_scale = height/640

            for i in range(rows):
                row = detections[i]
                confidence = row[4]
                if confidence > 0.4:
                    classes_score = row[5:]
                    ind = np.argmax(classes_score)
                    if classes_score[ind] > 0.2:
                        classes_ids.append(ind)
                        confidences.append(confidence)
                        cx, cy, w, h = row[:4]
                        x1 = int((cx- w/2)*x_scale)
                        y1 = int((cy-h/2)*y_scale)
                        wv= int(w * x_scale)
                        hv = int(h * y_scale)
                        box = np.array([x1,y1,wv,hv])
                        boxes.append(box)

            if len(boxes) > 0:
                num_retained_boxes = cv2.dnn.NMSBoxes(boxes,confidences,0.5,0.5)
                for i in num_retained_boxes:
                    if classes[classes_ids[i]] == 'obstacle':
                        bbox = boxes[i]
                        x1,y1,w,h = bbox
                        label = classes[classes_ids[i]]
                        conf = confidences[i]
                        text = label + "{:.2f}".format(conf)
                        cv2.rectangle(frame,(x1,y1),(x1+w,y1+h),(255,0,0),2)
                        cv2.putText(frame, text, (x1,y1-2),cv2.FONT_HERSHEY_COMPLEX, 0.7,(255,0,255),2)
                        cv2.putText(frame, decision, (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 2)
                        tracker = init_tracker(frame, bbox)
                        tracking = True
                        client_socket.sendall(get_decision(bbox).encode())
                        break
            
            if not tracking:
                client_socket.sendall("None".encode())
        
        # Calculate Frames per second (FPS)
        fps = cv2.getTickFrequency() / (cv2.getTickCount() - timer)
        # Display FPS on frame
        cv2.putText(frame, "FPS : " + str(int(fps)), (100,50), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (50,170,50), 2)
        
        # Display frame with bounding box
        cv2.imshow("Frame", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'): 
            client_socket.close()
            break

    # Release the camera and close serial connection
    cap.release()
        
