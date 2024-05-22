import json
import os
import socket
import threading
import re
import time

# Function to get the IP address of the machine
def get_ip_address():
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    return ip_address

def handle_client(connection, address, data):
    print(f"Connected to {address}")
    try:
        while True:
            data_received = connection.recv(1024)
            if not data_received:
                break
            print(f"Received from {address}: {data_received.decode()}")
            if data_received == b"GET_METADATA":
                metadata = file_metadata("/Files")  # Change this to your directory path
                connection.sendall(json.dumps(metadata).encode())
            else:
                connection.sendall(data_received)
    except Exception as e:
        print(f"Error with {address}: {e}")
    finally:
        print(f"Disconnected from {address}")

# Function to read JSON data from a file
def read_json(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data

def start_server(ip, port, data):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((ip, port))
    server_socket.listen(5)
    print(f"Server started on {ip}:{port}")

    try:
        while True:
            client_socket, address = server_socket.accept()
            client_thread = threading.Thread(target=handle_client, args=(client_socket, address, data))
            client_thread.start()
    except KeyboardInterrupt:
        print("Server terminated.")

def file_metadata(directory):
    metadata = {}
    for root, _, files in os.walk(directory):
        for filename in files:
            if "chunk" in filename:
                chunks = set()
                max_chunk_number = 0
                pattern = re.compile(r'chunk(\d+)_of_(\d+)')
                match = pattern.search(filename)
                if match:
                    chunk_number = int(match.group(1))
                    total_chunks = int(match.group(2))
                    chunks.add(chunk_number)
                    max_chunk_number = max(max_chunk_number, chunk_number)
                metadata[filename] = {
                    "chunks": sorted(chunks),
                    "max_chunk_number": max_chunk_number,
                    "total_chunks": total_chunks
                }
    return metadata

def get_online_devices(data):
    online_devices = []
    for ip, status_info in data.items():
        if status_info['Status'] == 1:
            online_devices.append(ip)
    return online_devices

def get_local_files(directory):
    local_files = {}
    for root, _, files in os.walk(directory):
        for filename in files:
            local_files[filename] = set()
            with open(os.path.join(root, filename), 'r') as file:
                lines = file.readlines()
                for line in lines:
                    chunk_index = int(line.strip())  # Assuming each line contains a chunk index
                    local_files[filename].add(chunk_index)
    return local_files

# Function to send chunks to a client
def send_chunks(connection, filename, chunks):
    try:
        with open(os.path.join("/Files", filename), 'rb') as file:  # Change this to your directory path
            for chunk_index in chunks:
                # Assuming each chunk is read as 1024 bytes
                file.seek(chunk_index * 1024)
                chunk_data = file.read(1024)
                connection.sendall(chunk_data)
        print(f"Sent chunks of {filename} to {connection.getpeername()[0]}")
    except Exception as e:
        print(f"Error sending chunks to {connection.getpeername()[0]}: {e}")
    finally:
        connection.close()

def backup_chunks(data):
    while True:
        time.sleep(37)
        online_devices = get_online_devices(data)
        local_files = get_local_files("/Files")  # Change this to your directory path
        for filename, chunks in local_files.items():
            for ip in online_devices:
                if filename in data[ip]:
                    remote_chunks = set(data[ip][filename]["chunks"])
                    missing_chunks = chunks - remote_chunks
                    if len(missing_chunks) > 0:
                        try:
                            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            sock.settimeout(5)
                            sock.connect((ip, 12345))  # Assume server listens on port 12345
                            request_data = json.dumps({"filename": filename, "chunks": list(missing_chunks)})
                            sock.sendall(request_data.encode())
                            response = sock.recv(1024)
                            if response == b"RECEIVED":
                                print(f"Sent missing chunks of {filename} to {ip}")
                            sock.close()
                        except Exception as e:
                            print(f"Error sending chunks to {ip}: {e}")

# Main function
def main():
    data = read_json('metadata.json')
    server_ip = get_ip_address()
    server_thread = threading.Thread(target=start_server, args=(server_ip, 12345, data))
    backup_thread = threading.Thread(target=backup_chunks, args=(data,))

    server_thread.start()
    backup_thread.start()

    server_thread.join()
    backup_thread.join()

if __name__ == "__main__":
    main()
