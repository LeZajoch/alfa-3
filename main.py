"""
This module loads the configuration, initializes the bank server,
and listens for client connections. On shutdown (KeyboardInterrupt), it saves
the current account data.
"""

import socket
import threading
import sys
import json
import os
from bank import Bank
from logger import Logger
from command_handler import BankServer


def load_config():
    """
    Loads configuration parameters from 'config.json'.

    Returns:
        dict: A dictionary containing configuration parameters.
              If the file is missing or cannot be parsed, default configuration is returned.
    """
    config_file = "config.json"
    default_config = {"port": 65525}
    if os.path.exists(config_file):
        with open(config_file, "r", encoding="utf-8") as f:
            try:
                config = json.load(f)
            except Exception:
                config = default_config
    else:
        config = default_config
    return config


def main():
    """
    Main entry point for the bank server application.

    Loads the configuration, initializes the bank, logger, and bank server,
    sets up the server socket, and accepts incoming client connections.
    On KeyboardInterrupt, account data is saved and the server shuts down.
    """
    config = load_config()
    port = config.get("port", 65525)

    if port < 65525 or port > 65535:
        print("PORT MUST BE IN THE RANGE 65525 - 65535")
        sys.exit(1)

    # Server listens on all interfaces.
    bind_ip = "0.0.0.0"
    # Automatically obtain local IP address as bank code.
    bank_code = socket.gethostbyname(socket.gethostname())

    # For purposes of manual IP setup (e.g. ZeroTier), you could override bank_code:
    # bank_code = config.get("ip", bank_code)

    bank = Bank(bank_code)
    # Load saved account data if available.
    bank.load_data()
    logger = Logger()
    bank_server = BankServer(bank, logger, response_timeout=5, port=port)

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((bind_ip, port))
    server_socket.listen(5)
    print(f"Server listening on {bind_ip}:{port} with bank code {bank_code}")

    try:
        while True:
            client_socket, client_address = server_socket.accept()
            threading.Thread(target=bank_server.handle_client, args=(client_socket,), daemon=True).start()
    except KeyboardInterrupt:
        print("\nShutting down server. Saving account data...")
        bank.save_data()
        server_socket.close()
        sys.exit(0)


if __name__ == '__main__':
    main()
