import json
import socket
import threading
import time

# Ensure the 'devices.json' file exists
if not os.path.exists("devices.json"):
    with open("devices.json", "w") as file:
        json.dump({}, file)

# Function to read JSON data from a file
def read_json(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data

# Function to save JSON data to a file
def save_json(file_path, data):
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)

# Function to update client status in the JSON data
def update_status(data, ip, status):
    if ip in data:
        data[ip]['Status'] = status
    else:
        data[ip] = {'Status': status}
    save_json('devices.json', data)

# Function to attempt connection to a device
def attempt_connection(ip, data):
    while True:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)  # Set a timeout for the connection attempt
            sock.connect((ip, 12345))  # Assume port 12345 for connection
            update_status(data, ip, 1)  # Update status to connected (1)
            print(f"Successfully connected to {ip}")

            # Request file metadata
            metadata = request_file_metadata(sock)
            if metadata:
                print(f"Received metadata from {ip}: {metadata}")

                # Request file chunks
                filename = input("Enter filename to request chunks: ")
                chunks = request_file_chunks(sock, filename)
                if chunks:
                    print(f"Received chunks from {ip}: {chunks}")

            sock.close()
            # Exit the loop once connection is successful
            break
        except Exception as e:
            print(f"Failed to connect to {ip}: {e}")
            update_status(data, ip, 0)  # Update status to disconnected (0)
        time.sleep(15)  # Wait for 15 seconds before trying again

# Function to request file metadata from the server
def request_file_metadata(sock):
    try:
        sock.sendall(b"GET_METADATA")
        response = sock.recv(1024)
        metadata = json.loads(response.decode())
        return metadata
    except Exception as e:
        print(f"Error requesting file metadata: {e}")
        return None

# Function to request file chunks from the server
def request_file_chunks(sock, filename):
    try:
        request_data = json.dumps({"command": "GET_FILE_CHUNKS", "filename": filename})
        sock.sendall(request_data.encode())
        response = sock.recv(1024)
        chunks = json.loads(response.decode())
        return chunks
    except Exception as e:
        print(f"Error requesting file chunks: {e}")
        return None

# Function to start connection attempts to devices
def start_connection_attempts(data):
    for ip in data.keys():
        thread = threading.Thread(target=attempt_connection, args=(ip, data))
        thread.start()

# Function to periodically update metadata
def update_metadata_periodically(data):
    while True:
        for ip in data.keys():
            if data[ip]['Status'] == 1:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(5)
                    sock.connect((ip, 12345))  # Assume server listens on port 12345
                    metadata = request_file_metadata(sock)
                    if metadata:
                        data[ip]['Metadata'] = metadata
                        print(f"Metadata updated for {ip}: {metadata}")
                except Exception as e:
                    print(f"Error updating metadata for {ip}: {e}")
                finally:
                    sock.close()
        time.sleep(30)  # Wait for 30 seconds before the next update

# Main function
def main():
    data = read_json('devices.json')
    start_connection_attempts(data)

    metadata_thread = threading.Thread(target=update_metadata_periodically, args=(data,))
    metadata_thread.start()

if __name__ == "__main__":
    main()
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

import json
import os
import socket
import threading
import time
from FindIPs import FindIPs

# Add to a file

Config = {
    "AllInfo" : "devices.json"
}

# Ensure the 'metadata.json' file exists
if not os.path.exists("metadata.json"):
    with open("metadata.json", "w") as file:
        json.dump({}, file)


# Integrate in file_request
def encode_and_join(name, chunks):
    encoded_name = json.dumps(name)
    encoded_chunks = json.dumps(chunks)

    joined_data = encoded_name + '\n' + encoded_chunks

    return joined_data

def split_and_decode(joined_data):
    encoded_name, encoded_chunks = joined_data.split('\n')

    name = json.loads(encoded_name)
    chunks = json.loads(encoded_chunks)

    return name, chunks


def file_request(device_socket, device_ip, filename, chunks):

    # Add integration of encode_and_join
    # Write response code    
    try:
        device_socket.sendall(message.encode())

        # Receive response from the device (if needed)
        # response = sock.recv(1024)
        # print("Response from device:", response.decode())

    except Exception as e:
        print(f"Error sending message to device {device_ip}: {e}")


def TransferFile():
        print("Executing command 1")

def Metadata():
        print("Executing command 2")

def command3():
        print("Executing command 3")


def HandleInput(toDo, fileDetails ):

    

    if(toDo==""):
        TransferFile()

    elif(toDo==""):
        Metadata()

    elif(toDo==""):
        command3()


# Function to read JSON data from a file
def read_json(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data

# Function to update client status in the JSON data
def update_status(data, ip, status):
    data[ip]['status'] = status
    save_json("devices.json", data)

def attempt_connection(ip, data, success_counter):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)  # Set a timeout for the connection attempt
        sock.connect((ip, 12345))  # Assume port 12345 for connection
        update_status(data, ip, 1)  # Update status to connected (1)
        print(f"Successfully connected to {ip}")
        success_counter.append(ip)  # Increment the counter for successful connections
    except Exception as e:
        print(f"Failed to connect to {ip}: {e}")
        update_status(data, ip, 0)  # Update status to disconnected (0)

def start_connection_attempts(data):
    success_counter = []  # List to store successful connections
    threads = []
    for device in data:
        ip = device['ip']
        if device['status'] == 0:
            thread = threading.Thread(target=attempt_connection, args=(ip, data, success_counter))
            thread.start()
            threads.append(thread)
    for thread in threads:
        thread.join()
    return len(success_counter)  # Return the number of successful connections

def save_json(file_path, data):
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)

def main(file_path):
    data = read_json(file_path)
    success_count = start_connection_attempts(data)
    if success_count > 0:
        print(f"Successfully connected to {success_count} devices.")
    else:
        print("No connections made.")

if __name__ == "__main__":
    FindIPs()
    main(Config['AllInfo'])

