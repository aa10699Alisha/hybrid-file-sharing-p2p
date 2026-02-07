# Created by: MUHAMMAD ABYAN AHMED
# Date Created: 6/4/2024

# This is the TRACKER module for our file-sharing system.
# The tracker acts like a directory server. It will:
#   1. Keep track of all active peers that are ready to receive chunks,
#   2. Share the list of those peers when asked (e.g., by Alice),
#   3. Allow new peers to register themselves so others can discover them.

import socket
import json

# List to store the registered peers
peers = []

# ---------------------------------------------------------------------------------------------
# This function (start_tracker) handles incoming peer requests.
def start_tracker(host='0.0.0.0', port=9090):
    # Create a socket for the tracker to listen for connections
    tracker_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tracker_socket.bind((host, port))
    # Start listening for incoming connections (we can queue upto 5 connections)
    tracker_socket.listen(5)

    # Let our user know the tracker is running.
    print(f"Tracker is up and running on {host}:{port}")

    while True:
        connection, address = tracker_socket.accept()
         # Inform the user when we get a connection.
        print(f"Got a connection from {address}")
        #  Receive data from the peer (up to 1024 bytes) and decode it.
        request = connection.recv(1024).decode()
        print(f"Request received: {request}")

        if request == 'GET_PEERS':
            # If the peer wants the list of peers, send it the 'peers' list.
            connection.sendall(json.dumps(peers).encode())
        elif request.startswith('REGISTER_PEER'):
            # If the peer wants to register itself, extract the peer's information.
            # We split the request into two parts: 'REGISTER_PEER' and the peer's info.
            _, peer_info = request.strip().split(' ', 1)
            # If the peer isn't already in the list, add it. This will help us optimise and
            # avoid duplicates
            if peer_info not in peers:
                peers.append(peer_info)
                print(f"New peer registered: {peer_info}")
        # Close the connection with the peer when we're done with this request
        connection.close()
# ---------------------------------------------------------------------------------------------

# Main program
if __name__ == "__main__":
    start_tracker()


    
    
        
