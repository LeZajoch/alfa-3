import os
import json
from datetime import datetime
import socket
import random
import threading
from datetime import datetime
import state

class Logger:
    def __init__(self, log_dir="logs"):
        self.log_dir = log_dir
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

    def log(self, level, client_ip, command, error_message=None):
        now = datetime.now()
        timestamp = now.strftime("%Y-%m-%dT%H:%M")
        date_str = now.strftime("%d,%m,%Y")
        log_file = os.path.join(self.log_dir, f"{date_str}.json")
        log_entry = {
            "timestamp": timestamp,
            "level": level,
            "client_ip": client_ip,
            "command": command,
        }
        if error_message:
            log_entry["error"] = error_message

        if os.path.exists(log_file):
            try:
                with open(log_file, "r", encoding="utf-8") as f:
                    logs = json.load(f)
                    if not isinstance(logs, list):
                        logs = []
            except Exception:
                logs = []
        else:
            logs = []

        logs.append(log_entry)
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(logs, f, indent=2)

class Server:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.running = True
        self.clients = []
        self.shutdown_votes = {}
        self.state = state.StateKnowNothing()
        self.logger = Logger()

    def start(self):
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print(f"Server běží na {self.host}:{self.port}")
        while self.running:
            client_socket, client_address = self.server_socket.accept()
            self.clients.append(client_socket)
            print(f"Připojen klient: {client_address}")
            self.logger.log("INFO", client_address[0], "Client Connected")
            threading.Thread(target=self.handle_client, args=(client_socket, client_address)).start()

    def handle_client(self, client_socket, client_address):
        client_socket.send("Vítejte na serveru! Napište 'help' pro dostupné příkazy.\r\n".encode('utf-8'))
        buffer = ""
        while True:
            try:
                data = client_socket.recv(1024).decode('utf-8')
                if not data:
                    break
                buffer += data
                while '\r\n' in buffer:
                    command, buffer = buffer.split('\r\n', 1)
                    command = command.strip()
                    print(f"Přijatý příkaz: {command}")
                    self.logger.log("INFO", client_address[0], command)
                    response = self.process_command(command, client_socket, client_address)
                    if response:
                        client_socket.send((response + "\r\n").encode('utf-8'))
            except Exception as e:
                self.logger.log("ERROR", client_address[0], "Unknown", str(e))
                break

        self.clients.remove(client_socket)
        client_socket.close()

    def process_command(self, command, client_socket, client_address):
        commands = {
            "help": self.show_help,
            "cit": self.send_quote,
            "dat": self.send_date,
            "cli": self.show_client_count,
            "bro": self.broadcast_message,
            "ss": self.request_shutdown,
            "ex": self.disconnect_client,
        }
        func = commands.get(command.split()[0].lower(), self.unknown_command)
        return func(client_socket, command)

    def show_help(self, client_socket, command):
        return "Dostupné příkazy:\r\ncit - vypíše citát\r\ndat - vrátí aktuální datum\r\ncli - zobrazí počet aktuálně připojených klientů\r\nbro [zpráva] - pošle zprávu všem připojeným klientům\r\nss - zahájí hlasování o vypnutí serveru\r\nex - odpojí vás ze serveru\r\n"

    def send_quote(self, client_socket, command):
        quotes = [
            "Nejlepší čas zasadit strom byl před 20 lety. Druhý nejlepší čas je teď.",
            "Buď změnou, kterou chceš vidět ve světě.",
            "Nikdy se nevzdávej. Velké věci potřebují čas.",
        ]
        return random.choice(quotes)

    def send_date(self, client_socket, command):
        return f"Dnešní datum je: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    def show_client_count(self, client_socket, command):
        return f"Aktuálně připojených klientů: {len(self.clients)}"

    def broadcast_message(self, client_socket, command):
        message = command[len("broadcast "):].strip()
        if not message:
            return "Zpráva je prázdná. Použijte: broadcast [zpráva]"

        for client in self.clients:
            if client != client_socket:
                try:
                    client.send(f"BROADCAST: {message}\r\n".encode('utf-8'))
                except:
                    pass
        return "Broadcast zpráva byla odeslána."

    def request_shutdown(self, client_socket, command):
        self.logger.log("INFO", "Server", "Shutdown vote initiated")
        return "Hlasování o vypnutí serveru zahájeno. Čeká se na odpovědi všech klientů."

    def disconnect_client(self, client_socket, command):
        self.logger.log("INFO", "Server", "Client Disconnected")
        client_socket.send("Byli jste odpojeni.\r\n".encode('utf-8'))
        self.clients.remove(client_socket)
        client_socket.close()
        return None

    def unknown_command(self, client_socket, command):
        self.logger.log("WARNING", "Server", command, "Unknown Command")
        return "Neznámý příkaz. Napište 'help' pro seznam dostupných příkazů."

if __name__ == "__main__":
    host = "127.0.0.1"
    port = 65532
    server = Server(host, port)
    server.start()
