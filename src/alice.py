# Created by: ALISHA ATIF 
# Date: 6/4/2024

# This is the ALICE module for our file-sharing system.
# Alice is the original sender of the file. She:
#   1. Splits a large file into smaller chunks
#   2. Contacts the tracker to get a list of active peers
#   3. Sends those chunks to a few selected peers over the network

# Import necessary libraries
import socket
import json
import os
import time

# Allocated IP address and port number of the tracker
TRACKER_IP = '127.0.0.1'
TRACKER_PORT = 9090

# -------------------------------------------------------------------------------------------
# This function (get_peers) asks the tracker for a list of peers
def get_peers():
    try:
        # Create a socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            # Connect to the tracker
            s.connect((TRACKER_IP, TRACKER_PORT))
            # Send the request for peers
            s.sendall(b'GET_PEERS')
            # Receive and decode the peer list as JSON
            response = s.recv(4096).decode()
            print(f"Received peer list: {response}")
            peers = json.loads(response)
            # Return the list of peers
            return peers
    except Exception as e:
    	# In case of error, display
        print(f"Error getting peers: {e}")
        return []

# -------------------------------------------------------------------------------------------
# This function (split_file) splits a big file into smaller chunks and saves them 
# in a "chunks" folder.
# Here, we have chosen the default chunk size to be 1 MB
def split_file(file_path, chunk_size=1024 * 1024):  
    # Directory where we save the chunks
    chunks_dir = "chunks"
    # Clear existing chunks from previous runs
    if os.path.exists(chunks_dir):
        for filename in os.listdir(chunks_dir):
            file_path_to_delete = os.path.join(chunks_dir, filename)
            if os.path.isfile(file_path_to_delete):
                os.remove(file_path_to_delete)
    # Create the chunks folder if it doesn't exist
    else:
        os.makedirs(chunks_dir)

    # Verify that the file exists. If not, we display an error
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} not found")
        return []

    # Check file size (this is an additional chekc, where if it is 0, we return that file is empty)
    file_size = os.path.getsize(file_path)
    if file_size == 0:
        print(f"Warning: File {file_path} is empty")

    # To make our program functionable for several data types (like txt and jpeg), we implemented
    # the following. We used the following method, to retrieve the extension of the files 
    # that Alice gets as input
    # Get original file extension 
    _, file_extension = os.path.splitext(file_path)
    
    # Create a metadata file which will store filename and extension of original file
    file_metadata = {
        "original_filename": os.path.basename(file_path),
        "extension": file_extension,
        "size": file_size,
        "chunk_count": 0  
    }

    # Print message to infrom user we are splitting the files
    print(f"Splitting file: {file_path} ({file_size} bytes) with extension: {file_extension}")

    # List to store chunk file names 
    chunks = []
    
    # Open the file in read mode
    with open(file_path, "rb") as f:
        # Chunk counter
        i = 0
        while True:
            # Read a chunk from the file
            chunk = f.read(chunk_size)
            # If no more data, we're done
            if not chunk:
                break
                
            # Create the chunk file name
            chunk_name = f"chunk_{i}.part"
            chunk_path = os.path.join(chunks_dir, chunk_name)
            
            # Open the chunk file in write mode
            with open(chunk_path, "wb") as chunk_file:
                # Write the chunk data to the file
                chunk_file.write(chunk)
                
            # Add just the chunk name to the list 
            chunks.append(chunk_name)
            
            # Display a message for user to stay updated
            print(f"Chunk created: {chunk_name} ({len(chunk)} bytes)")
            i += 1

    # Update metadata with chunk count and save it
    file_metadata["chunk_count"] = i
    metadata_path = os.path.join(chunks_dir, "file_metadata.json")
    with open(metadata_path, "w") as metadata_file:
        json.dump(file_metadata, metadata_file)
    
    # Add metadata file to chunks list
    chunks.append("file_metadata.json")
    
    # Notify the user
    print(f"Finished splitting file – total chunks: {i}")
    print(f"Metadata saved with original filename: {file_metadata['original_filename']} and extension: {file_metadata['extension']}")
    
    # Return the list of chunk names
    return chunks

# -------------------------------------------------------------------------------------------
# This function (send_chunks_to_peer) sends all the chunks from the "chunks" folder to 
# the specified peer.
def send_chunks_to_peer(peer_ip, peer_port):
    # Get and sort the chunk file names
    chunks_dir = "chunks"
    if not os.path.exists(chunks_dir):
        print(f"Error: Chunks directory {chunks_dir} not found")
        return False
    chunks = sorted(os.listdir(chunks_dir))
    
    # Move metadata file to the end to ensure it's processed last
    if "file_metadata.json" in chunks:
        chunks.remove("file_metadata.json")
        chunks.append("file_metadata.json")
    
    # Check if there are any chunks to send.
    if not chunks:
        print("No chunks found to send")
        return False

    print(f"Preparing to send {len(chunks)} chunks to {peer_ip}:{peer_port}")
    
    # Counter for the successfully sent chunks
    success_count = 0
    for chunk_file in chunks:
    	# Initiliaze the path to the chunk file.
        chunk_path = os.path.join(chunks_dir, chunk_file)
        
        # Skip if not a file or empty
        if not os.path.isfile(chunk_path) or os.path.getsize(chunk_path) == 0:
            print(f"Skipping {chunk_file} - not a valid file")
            continue
            
        # Create a socket for each chunk
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                # Connect to the peer
                s.connect((peer_ip, int(peer_port)))
                # Send a handshake message
                s.sendall(b'READY_TO_SEND')
                # Wait for acknowledgement
                ack = s.recv(1024)
                # If acknowledgement is incorrect
                if ack != b'READY_ACK':
                    print(f"{peer_ip}:{peer_port} isn't ready. Got: {ack}. Skipping...")
                    continue

                # Send the chunk file name
                s.sendall(os.path.basename(chunk_file).encode())
                # Small delay to ensure the peer is ready
                time.sleep(0.1)
                # Send the chunk data
                with open(chunk_path, "rb") as f:
                    data = f.read()
                    s.sendall(data)
                
                # Close the connection when we are done
                s.shutdown(socket.SHUT_WR)
                
                # Output message and incrementing the success counter for chunks
                print(f"Sent {chunk_file} to {peer_ip}:{peer_port} ({os.path.getsize(chunk_path)} bytes)")
                success_count += 1
                
            except Exception as e:
                print(f"Couldn't send {chunk_file} to {peer_ip}:{peer_port} – Error: {e}")

    # Output user for the user if all chunks sent succesfully
    print(f"Successfully sent {success_count} of {len(chunks)} chunks to {peer_ip}:{peer_port}")
    # Return True if at least one chunk was sent successfully.
    return success_count > 0

# -----------------------------------------------------------------------------------------
# Main program
if __name__ == "__main__":
    # Get the file path from the user
    file_path = input("Enter file path to share: ").strip()
    # Check if file exists
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} does not exist!")
        exit(1)
     
    # Split the file into chunks
    chunks = split_file(file_path)
    if not chunks:
        print("No chunks were created. Check if the file is valid.")
        exit(1)

    # Wait for peers to register
    print("Waiting for peers to register with tracker...")
    time.sleep(2)
    # Get the list of peers from the tracker
    peers = get_peers()
    # If no peers are available
    if not peers:
        print("No peers available. Make sure peers are running before starting Alice.")
        exit(1)

    # Send to the 2 peers
    peer_count = min(2, len(peers))
    print(f"Sending chunks to {peer_count} peers: {peers[:peer_count]}")
    
    for peer in peers[:peer_count]:  
        print(f"Sending chunks to {peer}...")
        # Extract IP and port from the peer info
        ip, port = peer.split(":")
        # Send chunks to the peer
        send_chunks_to_peer(ip, port)

    # Final message if a success for all required in PART 1
    print("File sharing complete!")