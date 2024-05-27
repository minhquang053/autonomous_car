import RPi.GPIO as GPIO
import pickle
from car import Car
from ultrasonic import Ultrasonic
from utils import get_ip_addr, TcpConnThread
from obstacle_avoiding import greedy_policy, get_sensor_values
from video_streamer import stream_webcam

def manual(data):
    global CONTROL_MODE
    if 'manual-left' in data:
        car.left()
    elif 'manual-right' in data:
        car.right()
    elif 'manual-forward' in data:
        car.forward()
    elif 'manual-stop' in data:
        car.stop()
    else:
        CONTROL_MODE = 2

def auto(data): 
    # action to avoid obstacle
    distances = ultrasonic.measure_distances()
    state = get_sensor_values(distances, data)
    oa_action = greedy_policy(Qtable_rlcar, state)
    print(tcp_conn_thread.data)
    print(state, oa_action)
    if all(d < 10 for d in distances):
        car.stop()
    elif oa_action == 0: 
        car.forward()
    elif oa_action == 1:
        car.left()
    elif oa_action == 2:
        car.right()
    else:
        car.stop()	
    
    # send sensor data
    tcp_conn_thread.send_data(f"{distances};")

car = Car()
HOST = get_ip_addr() 
PORT = 65432
rtsp_stream = stream_webcam(HOST)

ultrasonic = Ultrasonic(car)

# Mode for controlling the boat
CONTROL_MODE = 2 # 0: shutdown, 1: manual, 2: auto

with open('config/q_table.pkl', 'rb') as f:
    Qtable_rlcar = pickle.load(f)

try:
    tcp_conn_thread = TcpConnThread(HOST, PORT)
    
    while tcp_conn_thread.running:
        if rtsp_stream.poll():
            print("RTSP stream stopped")
            tcp_conn_thread.running = False
            break
        if tcp_conn_thread.connected:
            # check for current control mode
            if 'manual' in tcp_conn_thread.data:
                CONTROL_MODE = 1
            elif 'auto' or 'tracking' or 'detecting' in tcp_conn_thread.data:
                CONTROL_MODE = 2
            elif 'shutdown' in tcp_conn_thread.data:
                print("Shutting down") 
                break

            # take action based on control mode
            if CONTROL_MODE == 1:
                manual(tcp_conn_thread.data)
            elif CONTROL_MODE == 2: 
                auto(tcp_conn_thread.data)
        else:
            auto('')
finally:
    tcp_conn_thread.connected = False
    tcp_conn_thread.running = False
    tcp_conn_thread.join()
    car.shutdown()
    rtsp_stream.terminate()
