"""
This module implements the bank commands using the Command Pattern and provides a proxy mechanism
to forward commands (AD, AW, AB) to a remote node if the specified bank code (IP) does not match
the local bank code. It also defines the BankServer class which handles client connections.
"""

import concurrent.futures
import ipaddress
import socket


# --- Exception and validation functions ---
class CommandError(Exception):
    """
    Exception raised for errors in command execution.
    """
    pass


def validate_ip(ip_str):
    """
    Validates an IP address string.

    Args:
        ip_str (str): The IP address to validate.

    Returns:
        bool: True if the IP is valid, otherwise False.
    """
    try:
        ipaddress.ip_address(ip_str)
        return True
    except ValueError:
        return False


def validate_account_number(account_num):
    """
    Checks if the account number is within the allowed range.

    Args:
        account_num (int): The account number to validate.

    Returns:
        bool: True if valid, otherwise False.
    """
    return 10000 <= account_num <= 99999


def validate_number(number):
    """
    Checks if a number is within the allowed range.

    Args:
        number (int): The number to validate.

    Returns:
        bool: True if valid, otherwise False.
    """
    return 0 <= number <= 9223372036854775807


# --- Proxy functionality ---
def proxy_command(remote_ip, command, port):
    """
    Attempts to connect to a remote IP on the specified port to forward a command.

    Args:
        remote_ip (str): The remote IP address.
        command (str): The command string to forward.
        port (int): The port to use for the connection.

    Returns:
        str: The response from the remote server (trimmed), or an error message if the connection fails.
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(3)  # Set a timeout of 3 seconds
        s.connect((remote_ip, port))
        s.sendall((command + "\r\n").encode("utf-8"))
        response = ""
        while not response.endswith("\r\n"):
            data = s.recv(1024).decode("utf-8")
            if not data:
                break
            response += data
        s.close()
        return response.strip()
    except Exception as e:
        return f"ER PROXY ERROR: {str(e)}"


# --- Bank command implementations ---
class BaseCommand:
    """
    Base class for all bank commands.
    """
    command_code = ""

    def execute(self, args, client_ip, bank, logger, proxy_port):
        """
        Executes the command.

        Args:
            args (list): List of command arguments.
            client_ip (str): IP address of the client issuing the command.
            bank (Bank): The Bank instance.
            logger (Logger): The Logger instance.
            proxy_port (int): Port to use for proxying commands.

        Returns:
            str: The result of executing the command.

        Raises:
            NotImplementedError: Must be overridden by subclasses.
        """
        raise NotImplementedError()


class HELPCommand(BaseCommand):
    """
    Provides a help message listing available commands.
    """
    command_code = "HELP"

    def execute(self, args, client_ip, bank, logger, proxy_port):
        """
        Returns a help message with available commands.

        Returns:
            str: A help message.
        """
        help_message = (
            "Available Commands:\r\n"
            "BC - returns bank code\r\n"
            "AC - creates an account and returns its number\r\n"
            "AD - adds money to account\r\n"
            "AW - withdraws money from account\r\n"
            "AB - returns account balance\r\n"
            "AR - deletes account if empty\r\n"
            "BA - returns bank value\r\n"
            "BN - returns number of clients in bank\r\n"
        )
        return help_message


class BCCommand(BaseCommand):
    """
    Returns the bank code.
    """
    command_code = "BC"

    def execute(self, args, client_ip, bank, logger, proxy_port):
        """
        Executes the BC command.

        Returns:
            str: Bank code in the format "BC <bank_code>".
        """
        if len(args) != 1:
            raise CommandError("INVALID NUMBER OF ARGUMENTS FOR BC")
        logger.log("INFO", client_ip, " ".join(args))
        return f"BC {bank.bank_code}"


class ACCommand(BaseCommand):
    """
    Creates a new account and returns its number.
    """
    command_code = "AC"

    def execute(self, args, client_ip, bank, logger, proxy_port):
        """
        Executes the AC command.

        Returns:
            str: The new account number and bank code in the format "AC <account_number>/<bank_code>".
        """
        if len(args) != 1:
            raise CommandError("INVALID NUMBER OF ARGUMENTS FOR AC")
        try:
            account_number = bank.create_account()
        except Exception:
            raise CommandError("OUR BANK DOES NOT ALLOW NEW ACCOUNT CREATION.")
        logger.log("INFO", client_ip, " ".join(args))
        return f"AC {account_number}/{bank.bank_code}"


class ADCommand(BaseCommand):
    """
    Adds money to an account.
    """
    command_code = "AD"

    def execute(self, args, client_ip, bank, logger, proxy_port):
        """
        Executes the AD command. If the bank code in the account info does not match the local bank,
        the command is proxied to the remote node.

        Returns:
            str: "AD" if successful or the proxied response.
        """
        if len(args) != 3:
            raise CommandError("ACCOUNT NUMBER AND AMOUNT ARE NOT IN THE CORRECT FORMAT.")
        account_info = args[1]
        amount_str = args[2]
        if "/" not in account_info:
            raise CommandError("ACCOUNT NUMBER AND AMOUNT ARE NOT IN THE CORRECT FORMAT.")
        account_num_str, account_bank = account_info.split("/")
        if account_bank != bank.bank_code:
            command_str = " ".join(args)
            return proxy_command(account_bank, command_str, proxy_port)
        try:
            account_number = int(account_num_str)
        except ValueError:
            raise CommandError("ACCOUNT NUMBER AND AMOUNT ARE NOT IN THE CORRECT FORMAT.")
        if not validate_account_number(account_number):
            raise CommandError("ACCOUNT NUMBER AND AMOUNT ARE NOT IN THE CORRECT FORMAT.")
        try:
            amount = int(amount_str)
        except ValueError:
            raise CommandError("ACCOUNT NUMBER AND AMOUNT ARE NOT IN THE CORRECT FORMAT.")
        if not validate_number(amount):
            raise CommandError("ACCOUNT NUMBER AND AMOUNT ARE NOT IN THE CORRECT FORMAT.")
        bank.deposit(account_number, amount)
        logger.log("INFO", client_ip, " ".join(args))
        return "AD"


class AWCommand(BaseCommand):
    """
    Withdraws money from an account.
    """
    command_code = "AW"

    def execute(self, args, client_ip, bank, logger, proxy_port):
        """
        Executes the AW command. If the bank code does not match the local bank,
        the command is proxied.

        Returns:
            str: "AW" if successful or the proxied response.
        """
        if len(args) != 3:
            raise CommandError("ACCOUNT NUMBER AND AMOUNT ARE NOT IN THE CORRECT FORMAT.")
        account_info = args[1]
        amount_str = args[2]
        if "/" not in account_info:
            raise CommandError("ACCOUNT NUMBER AND AMOUNT ARE NOT IN THE CORRECT FORMAT.")
        account_num_str, account_bank = account_info.split("/")
        if account_bank != bank.bank_code:
            command_str = " ".join(args)
            return proxy_command(account_bank, command_str, proxy_port)
        try:
            account_number = int(account_num_str)
        except ValueError:
            raise CommandError("ACCOUNT NUMBER AND AMOUNT ARE NOT IN THE CORRECT FORMAT.")
        if not validate_account_number(account_number):
            raise CommandError("ACCOUNT NUMBER AND AMOUNT ARE NOT IN THE CORRECT FORMAT.")
        try:
            amount = int(amount_str)
        except ValueError:
            raise CommandError("ACCOUNT NUMBER AND AMOUNT ARE NOT IN THE CORRECT FORMAT.")
        if not validate_number(amount):
            raise CommandError("ACCOUNT NUMBER AND AMOUNT ARE NOT IN THE CORRECT FORMAT.")
        try:
            bank.withdraw(account_number, amount)
        except Exception as e:
            if str(e).upper() == "INSUFFICIENT FUNDS":
                raise CommandError("INSUFFICIENT FUNDS.")
            else:
                raise CommandError("ACCOUNT NUMBER AND AMOUNT ARE NOT IN THE CORRECT FORMAT.")
        logger.log("INFO", client_ip, " ".join(args))
        return "AW"


class ABCommand(BaseCommand):
    """
    Returns the balance of an account.
    """
    command_code = "AB"

    def execute(self, args, client_ip, bank, logger, proxy_port):
        """
        Executes the AB command. If the bank code does not match, proxies the command.

        Returns:
            str: The account balance in the format "AB <balance>" or the proxied response.
        """
        if len(args) != 2:
            raise CommandError("THE ACCOUNT NUMBER FORMAT IS NOT CORRECT.")
        account_info = args[1]
        if "/" not in account_info:
            raise CommandError("THE ACCOUNT NUMBER FORMAT IS NOT CORRECT.")
        account_num_str, account_bank = account_info.split("/")
        if account_bank != bank.bank_code:
            command_str = " ".join(args)
            return proxy_command(account_bank, command_str, proxy_port)
        try:
            account_number = int(account_num_str)
        except ValueError:
            raise CommandError("THE ACCOUNT NUMBER FORMAT IS NOT CORRECT.")
        if not validate_account_number(account_number):
            raise CommandError("THE ACCOUNT NUMBER FORMAT IS NOT CORRECT.")
        balance = bank.get_balance(account_number)
        logger.log("INFO", client_ip, " ".join(args))
        return f"AB {balance}"


class ARCommand(BaseCommand):
    """
    Deletes an account if its balance is zero.
    """
    command_code = "AR"

    def execute(self, args, client_ip, bank, logger, proxy_port):
        """
        Executes the AR command. Deletion is only allowed locally.

        Returns:
            str: "AR" if successful.
        """
        if len(args) != 2:
            raise CommandError("THE ACCOUNT NUMBER FORMAT IS NOT CORRECT.")
        account_info = args[1]
        if "/" not in account_info:
            raise CommandError("THE ACCOUNT NUMBER FORMAT IS NOT CORRECT.")
        account_num_str, account_bank = account_info.split("/")
        if account_bank != bank.bank_code:
            raise CommandError("THE ACCOUNT NUMBER FORMAT IS NOT CORRECT.")
        try:
            account_number = int(account_num_str)
        except ValueError:
            raise CommandError("THE ACCOUNT NUMBER FORMAT IS NOT CORRECT.")
        if not validate_account_number(account_number):
            raise CommandError("THE ACCOUNT NUMBER FORMAT IS NOT CORRECT.")
        try:
            bank.remove_account(account_number)
        except Exception:
            raise CommandError("CANNOT DELETE AN ACCOUNT THAT HAS FUNDS.")
        logger.log("INFO", client_ip, " ".join(args))
        return "AR"


class BACommand(BaseCommand):
    """
    Returns the total funds in the bank.
    """
    command_code = "BA"

    def execute(self, args, client_ip, bank, logger, proxy_port):
        """
        Executes the BA command.

        Returns:
            str: The bank value in the format "BA <total>".
        """
        if len(args) != 1:
            raise CommandError("INVALID NUMBER OF ARGUMENTS FOR BA")
        total = bank.get_total_amount()
        logger.log("INFO", client_ip, " ".join(args))
        return f"BA {total}"


class BNCommand(BaseCommand):
    """
    Returns the number of active accounts in the bank.
    """
    command_code = "BN"

    def execute(self, args, client_ip, bank, logger, proxy_port):
        """
        Executes the BN command.

        Returns:
            str: The number of clients in the format "BN <count>".
        """
        if len(args) != 1:
            raise CommandError("INVALID NUMBER OF ARGUMENTS FOR BN")
        count = bank.get_client_count()
        logger.log("INFO", client_ip, " ".join(args))
        return f"BN {count}"


# --- Command registry ---
COMMANDS = {
    "HELP": HELPCommand(),
    "BC": BCCommand(),
    "AC": ACCommand(),
    "AD": ADCommand(),
    "AW": AWCommand(),
    "AB": ABCommand(),
    "AR": ARCommand(),
    "BA": BACommand(),
    "BN": BNCommand(),
}


def handle_bank_command(command, client_ip, bank, logger, proxy_port):
    """
    Parses and handles a bank command.

    Args:
        command (str): The raw command string.
        client_ip (str): The IP address of the client issuing the command.
        bank (Bank): The Bank instance.
        logger (Logger): The Logger instance.
        proxy_port (int): The port to use for proxying commands.

    Returns:
        str: The response from executing the command.
    """
    parts = command.split()
    if not parts:
        logger.log("ER", client_ip, command, "INVALID COMMAND")
        return "ER INVALID COMMAND"
    cmd_key = parts[0]
    cmd_instance = COMMANDS.get(cmd_key)
    if not cmd_instance:
        logger.log("ER", client_ip, command, "UNKNOWN COMMAND")
        return "ER UNKNOWN COMMAND"
    try:
        result = cmd_instance.execute(parts, client_ip, bank, logger, proxy_port)
        return result
    except CommandError as ce:
        error_message = str(ce)
        logger.log("ER", client_ip, command, error_message)
        return f"ER {error_message}"


def process_bank_command(command, client_ip, bank, logger, response_timeout, proxy_port):
    """
    Processes a bank command using a separate thread and applies a timeout.

    Args:
        command (str): The command string.
        client_ip (str): The IP address of the client.
        bank (Bank): The Bank instance.
        logger (Logger): The Logger instance.
        response_timeout (int): Timeout in seconds for command processing.
        proxy_port (int): The port to use for proxying commands.

    Returns:
        str: The result of command execution, or an error message if a timeout occurs.
    """
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(handle_bank_command, command, client_ip, bank, logger, proxy_port)
        try:
            result = future.result(timeout=response_timeout)
            bank.save_data()  # Save data after each operation.
            return result
        except concurrent.futures.TimeoutError:
            logger.log("ER", client_ip, command, "TIMEOUT PROCESSING COMMAND")
            return "ER TIMEOUT PROCESSING COMMAND"


class BankServer:
    """
    Handles client connections and processes bank commands.
    """

    def __init__(self, bank, logger, response_timeout, port):
        """
        Initializes the BankServer.

        Args:
            bank (Bank): The Bank instance.
            logger (Logger): The Logger instance.
            response_timeout (int): Timeout in seconds for command processing.
            port (int): The default port used for proxying commands (must be consistent across nodes).
        """
        self.bank = bank
        self.logger = logger
        self.response_timeout = response_timeout
        self.port = port
        self.clients = []

    def process_command(self, command, client_socket):
        """
        Processes a command received from a client.

        Args:
            command (str): The raw command string.
            client_socket (socket.socket): The client's socket.

        Returns:
            str: The response to be sent back to the client.
        """
        try:
            client_ip = client_socket.getpeername()[0]
        except Exception:
            client_ip = "0.0.0.0"
        return process_bank_command(command, client_ip, self.bank, self.logger, self.response_timeout, self.port)

    def handle_client(self, client_socket):
        """
        Handles communication with a connected client. Receives data, processes commands,
        and sends back responses.

        Args:
            client_socket (socket.socket): The socket for the connected client.
        """
        self.clients.append(client_socket)
        buffer = ""
        while True:
            try:
                data = client_socket.recv(1024).decode("utf-8")
                if not data:
                    break
                buffer += data
                while "\r\n" in buffer:
                    command, buffer = buffer.split("\r\n", 1)
                    command = command.strip().upper()  # Convert input to uppercase.
                    print(f"RECEIVED COMMAND: {command}")
                    response = self.process_command(command, client_socket)
                    if response:
                        client_socket.send((response + "\r\n").encode("utf-8"))
            except ConnectionResetError:
                break
            except Exception as e:
                self.logger.log("ER", "UNKNOWN", command if 'command' in locals() else "", str(e))
                break
        if client_socket in self.clients:
            self.clients.remove(client_socket)
        client_socket.close()
