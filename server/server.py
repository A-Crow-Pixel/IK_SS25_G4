"""
Chat application server startup module

This module is responsible for starting the server side of the chat application, including UI interface and network services.
Supports command line parameter configuration for server ID, UDP port and TCP port.
"""

import sys
import os
from PySide6.QtWidgets import QApplication

# Add project root directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

from server.modern_server_ui import Stats, global_ms
from server.server_network import ServerSocket
import argparse

def parse_args():
    """
    Parse command line arguments
    
    Returns:
        argparse.Namespace: Namespace object containing the following parameters:
            - serverid (str): Server ID, default is 'Server_4'
            - udpport (int): UDP listening port, default is 9999
            - tcpport (int): TCP listening port, default is 65433
    """
    parser = argparse.ArgumentParser(description='IK Server startup parameters')
    parser.add_argument('--serverid', type=str, default='Server_4', help='This group serverId')
    parser.add_argument('--udpport', type=int, default=9999, help='UDP listening port')
    parser.add_argument('--tcpport', type=int, default=65433, help='TCP listening port')
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()
    app = QApplication([])
    main = Stats()
    server_socket = ServerSocket(server_id=args.serverid, udp_port=args.udpport, tcp_port=args.tcpport)
    main.server_socket = server_socket  # Inject server_socket to UI
    server_socket.ui = main.ui  # Compatibility retention
    main.ui.show()
    app.exec()
