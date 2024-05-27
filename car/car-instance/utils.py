import socket
import subprocess
import sys
import re
import threading
import traceback

def get_ip_addr():
    # Run ifconfig command to get network interface information
    result = subprocess.run(['ifconfig', 'wlan0'], capture_output=True, text=True)

    # Check if ifconfig command was successful
    if result.returncode == 0:
        # Use regular expression to find the IP address
        ip_match = re.search(r'inet (\d+\.\d+\.\d+\.\d+)', result.stdout)
        if ip_match:
            return ip_match.group(1)
        else:
            sys.exit("IP address not found")
    else:
        sys.exit("Failed to run ifconfig command")
        
class TcpConnThread(threading.Thread):
    def __init__(self, host, port, name='tcp-conn-thread'):
        self.host = host 
        self.port = port
        self.data = 'None'
        self.connected = False
        self.running = True
        self.conn = None
        super(TcpConnThread, self).__init__(name=name)
        self.start()
    
    def send_data(self, data):
        if self.connected and self.conn:
            try:
                self.conn.sendall(data.encode())
            except Exception as e:
                print(f"Error sending data: {e}")

    def run(self):	
        # Create a socket object
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            # Bind the socket to the address and port
            server_socket.bind((self.host, self.port))
            
            # Listen for incoming connections
            server_socket.listen()
            print("Server is listening...")
            
            while self.running:
                # Accept connection
                self.conn, addr = server_socket.accept()
                with self.conn:
                    self.connected = True
                    print('Connected by', addr)
                        
                    while self.connected:
                        # Receive data from the client
                        d = self.conn.recv(1024)
                        if not d:
                            break
                            
                        self.data = d.decode()

                        if "which" in self.data:
                            self.send_data("vehicle-car")

                        if "disconnect" in self.data:
                            self.connected = False
                        elif "shutdown" in self.data:
                            self.running = False
                            break

                self.conn = None
                self.connected = False
