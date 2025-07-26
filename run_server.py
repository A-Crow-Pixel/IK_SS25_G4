"""
Server startup script
Directly run server.py in the server directory
"""

import sys
import os
import subprocess

def main():
    """Start server application"""
    # Get the path of server.py
    current_dir = os.path.dirname(os.path.abspath(__file__))
    server_path = os.path.join(current_dir, 'server', 'server.py')
    
    # Check if file exists
    if not os.path.exists(server_path):
        print(f"Error: Server file not found {server_path}")
        return 1
    
    # Run server.py, pass all command line arguments
    try:
        print("Starting server...")
        print(f"Running: python {server_path}")
        result = subprocess.run([sys.executable, server_path] + sys.argv[1:], cwd=current_dir)
        return result.returncode
    except KeyboardInterrupt:
        print("\nServer stopped")
        return 0
    except Exception as e:
        print(f"Startup failed: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main()) 