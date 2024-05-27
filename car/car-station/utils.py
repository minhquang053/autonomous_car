import socket
import threading

def tcp_client(server_address, port, sys_info):
    # Create a TCP client socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        # Connect to the server
        client_socket.connect((server_address, port))
        print(f"Connected to server at {server_address}:{port}")

        # Function to handle receiving messages
        def receive_messages():
            while True:
                try:
                    data = client_socket.recv(1024)
                    if not data:
                        break
                    message = data.decode('utf-8')
                    if "vehicle-car" in message:
                        sys_info.vehicle_type = "Car"

                    msgs = message.split(';')
                    sys_info.recv_msg = msgs[1] if len(msgs) > 2 else msgs[0] 
                        
                    # print(f"Received message from server: {message}")
                except ConnectionResetError:
                    print("Connection reset by peer")
                    break

        # Start a separate thread to receive messages
        receive_thread = threading.Thread(target=receive_messages)
        receive_thread.start()

        # Function to send messages
        def send_message(message):
            client_socket.sendall(message.encode('utf-8'))
            sys_info.sent_msg = message
            # print(f"Sent message: {message}")
          
        send_message("which")

        # Function to close the client socket
        def close_socket():
            client_socket.close()
            print("Socket closed")

        # Return the send_message and close_socket functions for external use
        return send_message, close_socket

    except ConnectionRefusedError:
        print(f"Connection to server at {server_address}:{port} refused")
        # Close the socket if connection attempt fails
        client_socket.close()
