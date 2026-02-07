# Created by: ALISHA ATIF
# Date: 10/4/2024

# This is the BOB module for our file-sharing system.
# Bob is the receiver of the file. He:
#    1. Contacts the tracker to get a list of active peers.
#    2. Requests the list of chunks available from each peer.
#    3. Downloads the required chunks from the peers.
#    4. Reconstructs the original file from the downloaded chunks.

# Import necessary libraries
import socket
import json
import os
import shutil

# Tracker's IP and Port Number 
TRACKER_IP = '127.0.0.1'
TRACKER_PORT = 9090

# Setting up the directory for the downloaded chnuks
DOWNLOAD_DIR = 'bob_downloads'
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

# Reconstructed File Path
OUTPUT_FILE = os.path.join(DOWNLOAD_DIR, 'reconstructed_file')

# ----------------------------------------------------------------------------------
# This function (get_peer_list) asks the tracker for list of available peers
def get_peer_list():
    # Creating TCP socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            # Connect to the tracker
            s.connect((TRACKER_IP, TRACKER_PORT))
            # Send a request to get the peer list
            s.sendall(b'GET_PEERS')
            # Receive the peer list data from the tracker
            peer_data = s.recv(4096).decode()
            # Parse the received JSON data and return the peer list
            print(f"Received peer data: {peer_data}")
            return json.loads(peer_data)
        except Exception as e:
            print(f"Error getting peer list: {e}")
            # Return an empty list if an error occurs
            return []

# ----------------------------------------------------------------------------------
# This function (request_chunks_from_peer) asks a peer for the chunks it has
def request_chunks_from_peer(peer_ip, peer_port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
             # Connect to the peer
            s.connect((peer_ip, peer_port))
            # Send a request to get the chunk list
            s.sendall(b'REQUEST_CHUNKS')  
            # Receive it
            response = s.recv(4096).decode()
            # Print the received chunk list
            print(f"Received chunk list from {peer_ip}:{peer_port}: {response}")
            chunk_list = json.loads(response) 
            # Return the chunk list.
            return chunk_list
        except Exception as e:
            # Print an error message if an exception occurs.
            print(f"Failed to connect to {peer_ip}:{peer_port} – {e}")
            return []

# ----------------------------------------------------------------------------------
# This function (download_chunk) is used to download a specific chunk from the peer
def download_chunk(peer_ip, peer_port, chunk_name):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((peer_ip, peer_port))

            # Send a request to download a chunk
            s.sendall(b'REQUEST_CHUNK')
            # Receive acknowledgement from the peer
            ack = s.recv(1024)
            # Check if the acknowledgement is correct, if not we display error
            if ack != b'REQUEST_ACK':
                print(f"{peer_ip}:{peer_port} didn't acknowledge chunk request. Got: {ack}")
                return False

            # Send the chunk name to the peer
            s.sendall(chunk_name.encode())
            # Define the path to save the chunk
            save_path = os.path.join(DOWNLOAD_DIR, chunk_name)
            # Open the file in write mode
            with open(save_path, 'wb') as f:
                # Receive the first part of the chunk data
                first_data = s.recv(1024)
                # Check if the chunk was not found on the peer
                if first_data == b'NOT_FOUND':
                    # Print error in that case
                    print(f"{chunk_name} not found on {peer_ip}:{peer_port}")
                    # Remove the empty file
                    os.remove(save_path)  
                    return False


                # Otherwise, it is the first chunk of data and we write it
                f.write(first_data)
                
                # Continue receiving data until not data when we break
                while True:
                    try:
                        data = s.recv(1024)
                        if not data:
                            break
                        f.write(data)
                    except:
                        break

            # Verify the chunk is not empty and if it empty, we return false
            if os.path.getsize(save_path) == 0:
                print(f"Downloaded empty chunk: {chunk_name}")
                os.remove(save_path)
                return False

            # Return True if the chunk was downloaded successfully.
            print(f"Downloaded: {chunk_name} from {peer_ip}:{peer_port} ({os.path.getsize(save_path)} bytes)")
            return True

    except Exception as e:
        # Return False if the chunk was downloaded successfully.
        print(f"Error downloading {chunk_name} from {peer_ip}:{peer_port} – {e}")
        return False

# ---------------------------------------------------------------------------------------
# This helper function (get_file_metadata) is used to read metadata file to get
# original filename and extension
def get_file_metadata():
    # Reads the file metadata from 'file_metadata.json' we created
    metadata_path = os.path.join(DOWNLOAD_DIR, "file_metadata.json")
    # If it does not exist, we display error
    if not os.path.exists(metadata_path):
        print("No metadata file found. Cannot determine original file extension.")
        return None
    
    try:
         # Open the metadata file in read mode
         with open(metadata_path, 'r') as f:
             # Load the JSON data
            metadata = json.load(f)
            # Print it and return the metadata
            print(f"Read metadata: {metadata}")
            return metadata
    except Exception as e:
        # Print an error message if an exception occurs
        print(f"Error reading metadata: {e}")
        return None

# -------------------------------------------------------------------------------------
# This function (reconstruct_file) reconstructs the file from chunks using metadata
def reconstruct_file():
    # Get metadata for original filename and extension
    metadata = get_file_metadata()
    
    # We check if metadata exists and display error in case it doesnt 
    if not metadata:
        print("Missing metadata - attempting to reconstruct without file extension")
        output_path = OUTPUT_FILE
    else:
        # Use original extension from metadata
        extension = metadata.get('extension', '')
        # Get the original filename from the metadata
        original_filename = metadata.get('original_filename', 'reconstructed_file')
         # Get output file path using the original filename
        output_path = os.path.join(DOWNLOAD_DIR, original_filename)
        print(f"Using original filename: {original_filename}")
    
    # Find all chunk files and sort them (excluding the metadata file)
    chunk_files = sorted([f for f in os.listdir(DOWNLOAD_DIR) 
                         if f.startswith("chunk_") and f.endswith(".part")])
    
    if not chunk_files:
        print("No chunks found for reconstruction!")
        return False
    
    # Print the number of chunk files found.
    print(f"Found {len(chunk_files)} chunk files for reconstruction: {chunk_files}")
    
    # Reconstructing the file
    # Open the output file in write mode
    with open(output_path, "wb") as output:
        # Iterate over each chunk file
        for chunk_name in chunk_files:
            # Define the path to the chunk file
            chunk_path = os.path.join(DOWNLOAD_DIR, chunk_name)
            print(f"Adding {chunk_name} to reconstructed file ({os.path.getsize(chunk_path)} bytes)")
            # Open the chunk file in read
            with open(chunk_path, "rb") as chunk_file:
                # Write the chunk data to the output file
                output.write(chunk_file.read())
    
    # Check if the reconstructed file is empty and display error if it is
    if os.path.getsize(output_path) == 0:
        print("Warning: Reconstructed file is empty!")
        return False
    
    # Print a success message
    print(f"\nReconstructed file saved as: {output_path} ({os.path.getsize(output_path)} bytes)")
    return True

# ----------------------------------------------------------------------------------
# Main Logic
def main():
    print("Starting Bob's file retrieval process...")
    
    # Clean download directory from previous work
    # Iterate over each file in the download directory and define path
    for filename in os.listdir(DOWNLOAD_DIR):
        file_path = os.path.join(DOWNLOAD_DIR, filename)
        try:
            # Check if the file is a regular file, then remove it 
            if os.path.isfile(file_path):
                os.remove(file_path)
        except Exception as e:
            # Else error
            print(f"Error cleaning up {filename}: {e}")
    
    # Get all available peers from tracker
    all_peers = get_peer_list()
    # Check if the peer list is empty, then display error and return
    if not all_peers:
        print("No peers available. Make sure the tracker is running and peers are registered.")
        return

     # Print the number of peers found
    print(f"Found {len(all_peers)} peers: {all_peers}")
    
    # Keep track of downloaded chunks by making a set
    downloaded_chunks = set()
    
    # Process each peer
    for peer in all_peers:
        # Split the peer address into IP and port
        ip, port = peer.split(":")
         # Convert the port to integer
        port = int(port)
        # Print a message indicating which peer is being contacted.
        print(f"\nContacting peer at {ip}:{port}...")
        
        # Get available chunks from this peer
        available_chunks = request_chunks_from_peer(ip, port)
        
        # If no available chunks, print that
        if not available_chunks:
            print(f"No chunks available from {ip}:{port}")
            # Continue to the next peer.
            continue
            
        # Print the number of chunks available from the peer.
        print(f"Peer has {len(available_chunks)} chunks: {available_chunks}")
        
        # Download each chunk
        for chunk in available_chunks:
            # Check if the chunk has not been downloaded yet.
            if chunk not in downloaded_chunks:
                # Print a message indicating which chunk is being downloaded.
                print(f"Attempting to download {chunk}...")
                # Download the chunk.
                success = download_chunk(ip, port, chunk)
                # Check if the chunk was downloaded successfully.
                if success:
                    # Add the chunk to the set of downloaded chunks.
                    downloaded_chunks.add(chunk)
                    # Success msg.
                    print(f"Successfully downloaded {chunk}")
                else:
                    # Failure msg
                    print(f"Failed to download {chunk}")

    # If no chunks were downloaded, display
    if not downloaded_chunks:
        print("No chunks were downloaded. Cannot reconstruct the file.")
        return
    
    # Print the number of unique chunks downloaded.
    print(f"\nDownloaded {len(downloaded_chunks)} unique chunks: {downloaded_chunks}")
    
    # Print if reconstructing was a success or nto
    if reconstruct_file():
        print("\nFile reconstruction completed successfully!")
    else:
        print("\nFile reconstruction failed!")

# ----------------------------------------------------------------------------------
if __name__ == "__main__":
    # Call main function 
    main()

