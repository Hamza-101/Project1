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
