"""
Client startup script
Directly run client.py in the client directory
"""

import sys
import os
import subprocess

def main():
    """Start client application"""
    # Get the path of client.py
    current_dir = os.path.dirname(os.path.abspath(__file__))
    client_path = os.path.join(current_dir, 'client', 'client_1.py')
    
    # Check if file exists
    if not os.path.exists(client_path):
        print(f"Error: Client file not found {client_path}")
        return 1
    
    # Run client.py, pass all command line arguments
    try:
        print("Starting client...")
        print(f"Running: python {client_path}")
        result = subprocess.run([sys.executable, client_path] + sys.argv[1:], cwd=current_dir)
        return result.returncode
    except KeyboardInterrupt:
        print("\nClient stopped")
        return 0
    except Exception as e:
        print(f"Startup failed: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main()) 