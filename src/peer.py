# Created by: MUHAMMAD ABYAN AHMED
# Date: 7/4/2024

# This is the PEER module for our file-sharing system. It:
#    1. Registers itself with the tracker.
#    2. Listens for incoming chunk data (from Alice).
#    3. Serves chunks to downloaders like Bob.

# Import necessary libraries
import socket  
import os  
import threading  
import shutil  
import json 

# First, we remove any existing received_chunks directory contents
shutil.rmtree("received_chunks", ignore_errors=True)

# Peer's IP address
PEER_IP = '127.0.0.1'
# Tracker's IP address
TRACKER_IP = '127.0.0.1'
# Tracker's port
TRACKER_PORT = 9090

# ---------------------------------------------------------------------------------------
# This function (get_free_port) finds and returns an available port number for the peer to 
# communicate. 
def get_free_port():
    # Create a temporary socket
    temp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Bind to any available address and port 0 
    temp_sock.bind(('', 0))
    # Get the assigned port number
    _, free_port = temp_sock.getsockname()
    # Close the temporary socket
    temp_sock.close()
    # Return the free port
    return free_port

# Get and set the peer's port
PEER_PORT = get_free_port()

# ----------------------------------------------------------------------------------
# This function (register_with_tracker) helps to register the peer with the tracker.
def register_with_tracker():
    # Create a socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            # Connect to the tracker
            s.connect((TRACKER_IP, TRACKER_PORT))
            # Create the registration message
            register_msg = f"REGISTER_PEER {PEER_IP}:{PEER_PORT}"
            # Send it
            s.sendall(register_msg.encode())
            # Print it for the user 
            print(f"Tracker registration complete: {register_msg}")
        except Exception as e:
            # If we fail to register, print it and exit
            print(f"Failed to register with tracker: {e}")
            exit(1)

# ----------------------------------------------------------------------------------
# This function (start_peer) is used to start the peer server to listen for incoming connections
def start_peer():
    # Call the register function we made to register with tracker first
    register_with_tracker()
    # Now, we create the server socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # Bind to the peer's IP and port
    server_socket.bind((PEER_IP, PEER_PORT))
    # Listen for incoming connections
    server_socket.listen(5)
    # Print peer running message so the user is aware that the peer is up
    print(f"Peer is now running at {PEER_IP}:{PEER_PORT} and waiting for chunks...")
    # Next, we ensure that the received_chunks directory exists
    os.makedirs('received_chunks', exist_ok=True)
    while True:
        try:
            # Accept a connection
            connection, addr = server_socket.accept()
            # Print new connection info 
            print(f"New connection from {addr}")
            # Start thread for client
            threading.Thread(target=handle_client, args=(connection,)).start()
        except Exception as e:
            # In case of a connection error, we print it
            print(f"Error accepting connection: {e}")

# ----------------------------------------------------------------------------------
# This function (handle_client) is used to handle communication with a connected client
def handle_client(connection):
    try:
        # Get request type
        request = connection.recv(1024)
        # Print the received request
        print(f"Received request: {request}")
        # Handle chunk request
        if request == b'REQUEST_CHUNKS':
            # Call handler function
            handle_request_chunks(connection)
        # Handle specific chunk request
        elif request == b'REQUEST_CHUNK': 
            handle_request_specific_chunk(connection)
        # Handle incoming chunk
        elif request == b'READY_TO_SEND':
            # Call appropriate function
            handle_incoming_chunk(connection)
        else:
            # Handle unknown requests
            print(f"Unknown request: {request}")
    except Exception as e:
        # Print if error.
        print(f"Error while handling client request: {e}")
    finally:
        # Close the connection
        connection.close()

# ----------------------------------------------------------------------------------
# This function (handle_incoming_chunk) is used to handle the logic for receiving
# a chunk of data from another peer.
def handle_incoming_chunk(connection):
    try:
        # Send acknowledgment
        connection.sendall(b'READY_ACK')
        # Get chunk filename
        chunk_file_name = connection.recv(1024).decode()
        # Print incoming chunk name
        print(f"Incoming chunk name: {chunk_file_name}")
        # Set the save directory
        save_dir = 'received_chunks'
        os.makedirs(save_dir, exist_ok=True)
        # Construct the full save path
        save_path = os.path.join(save_dir, chunk_file_name)
        # Open the file for writing 
        with open(save_path, 'wb') as f:
            while True:
                try:
                    # Receive data
                    data = connection.recv(1024)
                    # If no more data, break
                    if not data:
                        break
                    # Write data to the file
                    f.write(data)
                except ConnectionResetError:
                    print("Connection reset during chunk receive – assuming file end.")
                    break
        # Verify file received
        if os.path.exists(save_path) and os.path.getsize(save_path) > 0:
            # Print success message to infrom user
            print(f"Saved chunk: {chunk_file_name} ({os.path.getsize(save_path)} bytes)")
        else:
            # Print warning in case of an error
            print(f"Warning: Chunk {chunk_file_name} is empty or wasn't saved properly")
    except Exception as e:
        # Print chunk receiving error
        print(f"Error while receiving chunk: {e}")

# ---------------------------------------------------------------------------------- 
# This function is relevant for the Part 2 of the Assignment, when we retrieve the file
# This function (handle_request_chunks) is used to send the list of available chunks to Bob
# It handles requests from other peers for a list of available chunks
def handle_request_chunks(connection):
    try:
        if not os.path.exists('received_chunks'):
            os.makedirs('received_chunks')
            connection.sendall(json.dumps([]).encode())
            print("Sent empty chunk list (no folder yet)")
            return
        # Get the chunk list
        available_chunks = [f for f in os.listdir('received_chunks') if os.path.isfile(os.path.join('received_chunks', f))]
        # Convert list to JSON
        response = json.dumps(available_chunks)
        # Send the JSON-encoded list
        connection.sendall(response.encode())
        # Print sent list
        print(f"Sent available chunks list: {available_chunks}")
    except Exception as e:
        # Print error
        print(f"Error sending chunk list: {e}")
        try:
            connection.sendall(json.dumps([]).encode())
        except:
            pass

# ----------------------------------------------------------------------------------
# This function (handle_request_specific_chunk) is used to send a specific chunk to Bob
def handle_request_specific_chunk(connection):
    try:
        # Send acknowledgment
        connection.sendall(b'REQUEST_ACK')
        # Get requested chunk name
        chunk_name = connection.recv(1024).decode()
        # Print request
        print(f"Received request for chunk: {chunk_name}")
        # Construct path
        chunk_path = os.path.join('received_chunks', chunk_name)
        # Check if chunk exists
        if not os.path.exists(chunk_path) or os.path.getsize(chunk_path) == 0:
            # Send not found
            connection.sendall(b'NOT_FOUND')
            # Print not found
            print(f"{chunk_name} not found or empty")
            return
        # Open the chunk file
        with open(chunk_path, 'rb') as f:
            # Read the chunk data
            data = f.read()
            # Send the data
            connection.sendall(data)
            # Print when it is sent
            print(f"Sent chunk {chunk_name} ({len(data)} bytes)")
    except Exception as e:
        # Print error
        print(f"Error sending chunk: {e}")
        try:
            connection.sendall(b'NOT_FOUND')
        except:
            pass

# ----------------------------------------------------------------------------------
# Call the star_peer function in the main loop 
if __name__ == "__main__":
    start_peer()
