import json
import os
import socket
import threading
import time

# Ensure the 'metadata.json' file exists
if not os.path.exists("metadata.json"):
    with open("metadata.json", "w") as file:
        json.dump({}, file)

# Function to read JSON data from a file
def read_json(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data

# Function to update client status in the JSON data
def update_status(data, ip, status):
    data[ip]['Status'] = status

# Function to retrieve and store file metadata
def retrieve_and_store_metadata(ip, data):
    metadata = request_file_metadata(ip)
    if metadata:
        data[ip]['Metadata'] = metadata
        print(f"Metadata updated for {ip}")

# Function to attempt connection to a device
def attempt_connection(ip, data):
    while True:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)  # Set a timeout for the connection attempt
            sock.connect((ip, 12345))  # Assume port 12345 for connection
            update_status(data, ip, 1)  # Update status to connected (1)
            print(f"Successfully connected to {ip}")
            retrieve_and_store_metadata(ip, data)  # Retrieve and store metadata
            # We can add additional functionality here if needed
        except Exception as e:
            print(f"Failed to connect to {ip}: {e}")
            update_status(data, ip, 0)  # Update status to disconnected (0)
        time.sleep(15)  # Wait for 15 seconds before trying again

# Function to request file chunks from the server
def request_file_chunks(ip, filename):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((ip, 12345))  # Assume server listens on port 12345
        request_data = json.dumps({"command": "GET_FILE_CHUNKS", "filename": filename})
        sock.sendall(request_data.encode())
        response = sock.recv(1024)
        chunks = json.loads(response.decode())
        return chunks
    except Exception as e:
        print(f"Error requesting file chunks from {ip}: {e}")
        return []

# Function to start connection attempts to devices
def start_connection_attempts(data):
    for ip, status_info in data.items():
        if status_info['Status'] == 1:
            thread = threading.Thread(target=attempt_connection, args=(ip, data))
            thread.start()

# Function to request file metadata from the server
def request_file_metadata(ip):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((ip, 12345))  # Assume server listens on port 12345
        sock.sendall(b"GET_METADATA")
        response = sock.recv(1024)
        metadata = json.loads(response.decode())
        return metadata
    except Exception as e:
        print(f"Error requesting file metadata from {ip}: {e}")
        return {}

def handle_user_input(data):
    while True:
        filename = input("Enter filename: ")
        online_devices = get_online_devices(data)
        found = False
        if not online_devices:
            print("No devices online")
        else:    
            for ip in online_devices:
                metadata = data[ip].get('Metadata', None)
                if metadata and filename in metadata:
                    found = True
                    print(f"Fetching file '{filename}' from {ip}...")
                    chunks = request_file_chunks(ip, filename)
                    for chunk in chunks:
                        print(f"Received chunk {chunk} for {filename}")
                        # Code to process the received chunk
                    break
            if not found:
                print(f"File '{filename}' not found in directory.")

# Function to save JSON data to a file
def save_json(file_path, data):
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)

def get_online_devices(data):
    online_devices = []
    for ip, status_info in data.items():
        if status_info['Status'] == 1:
            online_devices.append(ip)
    return online_devices

# Function to periodically update metadata
def update_metadata_periodically(data):
    while True:
        for ip in get_online_devices(data):
            retrieve_and_store_metadata(ip, data)
        time.sleep(30)  # Wait for 30 seconds before the next update

# Main function
def main(file_path):
    data = read_json(file_path)
    
    connection_thread = threading.Thread(target=start_connection_attempts, args=(data,))
    metadata_thread = threading.Thread(target=update_metadata_periodically, args=(data,))
    
    connection_thread.start()
    metadata_thread.start()

    handle_user_input(data)

    connection_thread.join()
    metadata_thread.join()

if __name__ == "__main__":
    main('metadata.json')
