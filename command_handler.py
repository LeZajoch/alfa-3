import concurrent.futures
import ipaddress


# --- Exception and validation functions ---
class CommandError(Exception):
    pass


def validate_ip(ip_str):
    try:
        ipaddress.ip_address(ip_str)
        return True
    except ValueError:
        return False


def validate_account_number(account_num):
    return 10000 <= account_num <= 99999


def validate_number(number):
    return 0 <= number <= 9223372036854775807


# --- Bank command implementations (Command Pattern) ---
class BaseCommand:
    command_code = ""

    def execute(self, args, client_ip, bank, logger):
        raise NotImplementedError()

class HELPCommand(BaseCommand):
    command_code = "HELP"

    def execute(self, args, client_ip, bank, logger):
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
    command_code = "BC"

    def execute(self, args, client_ip, bank, logger):
        if len(args) != 1:
            raise CommandError("INVALID NUMBER OF ARGUMENTS FOR BC")
        logger.log("INFO", client_ip, " ".join(args))
        return f"BC {bank.bank_code}"


class ACCommand(BaseCommand):
    command_code = "AC"

    def execute(self, args, client_ip, bank, logger):
        if len(args) != 1:
            raise CommandError("INVALID NUMBER OF ARGUMENTS FOR AC")
        try:
            account_number = bank.create_account()
        except Exception:
            raise CommandError("OUR BANK DOES NOT ALLOW NEW ACCOUNT CREATION.")
        logger.log("INFO", client_ip, " ".join(args))
        return f"AC {account_number}/{bank.bank_code}"


class ADCommand(BaseCommand):
    command_code = "AD"

    def execute(self, args, client_ip, bank, logger):
        if len(args) != 3:
            raise CommandError("ACCOUNT NUMBER AND AMOUNT ARE NOT IN THE CORRECT FORMAT.")
        account_info = args[1]
        amount_str = args[2]
        if "/" not in account_info:
            raise CommandError("ACCOUNT NUMBER AND AMOUNT ARE NOT IN THE CORRECT FORMAT.")
        account_num_str, account_bank = account_info.split("/")
        try:
            account_number = int(account_num_str)
        except ValueError:
            raise CommandError("ACCOUNT NUMBER AND AMOUNT ARE NOT IN THE CORRECT FORMAT.")
        if not validate_account_number(account_number):
            raise CommandError("ACCOUNT NUMBER AND AMOUNT ARE NOT IN THE CORRECT FORMAT.")
        if account_bank != bank.bank_code:
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
    command_code = "AW"

    def execute(self, args, client_ip, bank, logger):
        if len(args) != 3:
            raise CommandError("ACCOUNT NUMBER AND AMOUNT ARE NOT IN THE CORRECT FORMAT.")
        account_info = args[1]
        amount_str = args[2]
        if "/" not in account_info:
            raise CommandError("ACCOUNT NUMBER AND AMOUNT ARE NOT IN THE CORRECT FORMAT.")
        account_num_str, account_bank = account_info.split("/")
        try:
            account_number = int(account_num_str)
        except ValueError:
            raise CommandError("ACCOUNT NUMBER AND AMOUNT ARE NOT IN THE CORRECT FORMAT.")
        if not validate_account_number(account_number):
            raise CommandError("ACCOUNT NUMBER AND AMOUNT ARE NOT IN THE CORRECT FORMAT.")
        if account_bank != bank.bank_code:
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
            if str(e) == "INSUFFICIENT FUNDS":
                raise CommandError("INSUFFICIENT FUNDS.")
            else:
                raise CommandError("ACCOUNT NUMBER AND AMOUNT ARE NOT IN THE CORRECT FORMAT.")
        logger.log("INFO", client_ip, " ".join(args))
        return "AW"


class ABCommand(BaseCommand):
    command_code = "AB"

    def execute(self, args, client_ip, bank, logger):
        if len(args) != 2:
            raise CommandError("THE ACCOUNT NUMBER FORMAT IS NOT CORRECT.")
        account_info = args[1]
        if "/" not in account_info:
            raise CommandError("THE ACCOUNT NUMBER FORMAT IS NOT CORRECT.")
        account_num_str, account_bank = account_info.split("/")
        try:
            account_number = int(account_num_str)
        except ValueError:
            raise CommandError("THE ACCOUNT NUMBER FORMAT IS NOT CORRECT.")
        if not validate_account_number(account_number):
            raise CommandError("THE ACCOUNT NUMBER FORMAT IS NOT CORRECT.")
        if account_bank != bank.bank_code:
            raise CommandError("THE ACCOUNT NUMBER FORMAT IS NOT CORRECT.")
        balance = bank.get_balance(account_number)
        logger.log("INFO", client_ip, " ".join(args))
        return f"AB {balance}"


class ARCommand(BaseCommand):
    command_code = "AR"

    def execute(self, args, client_ip, bank, logger):
        if len(args) != 2:
            raise CommandError("THE ACCOUNT NUMBER FORMAT IS NOT CORRECT.")
        account_info = args[1]
        if "/" not in account_info:
            raise CommandError("THE ACCOUNT NUMBER FORMAT IS NOT CORRECT.")
        account_num_str, account_bank = account_info.split("/")
        try:
            account_number = int(account_num_str)
        except ValueError:
            raise CommandError("THE ACCOUNT NUMBER FORMAT IS NOT CORRECT.")
        if not validate_account_number(account_number):
            raise CommandError("THE ACCOUNT NUMBER FORMAT IS NOT CORRECT.")
        if account_bank != bank.bank_code:
            raise CommandError("THE ACCOUNT NUMBER FORMAT IS NOT CORRECT.")
        try:
            bank.remove_account(account_number)
        except Exception:
            raise CommandError("CANNOT DELETE AN ACCOUNT THAT HAS FUNDS.")
        logger.log("INFO", client_ip, " ".join(args))
        return "AR"


class BACommand(BaseCommand):
    command_code = "BA"

    def execute(self, args, client_ip, bank, logger):
        if len(args) != 1:
            raise CommandError("INVALID NUMBER OF ARGUMENTS FOR BA")
        total = bank.get_total_amount()
        logger.log("INFO", client_ip, " ".join(args))
        return f"BA {total}"


class BNCommand(BaseCommand):
    command_code = "BN"

    def execute(self, args, client_ip, bank, logger):
        if len(args) != 1:
            raise CommandError("INVALID NUMBER OF ARGUMENTS FOR BN")
        count = bank.get_client_count()
        logger.log("INFO", client_ip, " ".join(args))
        return f"BN {count}"


# Register bank commands.
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


def handle_bank_command(command, client_ip, bank, logger):
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
        result = cmd_instance.execute(parts, client_ip, bank, logger)
        return result
    except CommandError as ce:
        error_message = str(ce)
        logger.log("ER", client_ip, command, error_message)
        return f"ER {error_message}"


def process_bank_command(command, client_ip, bank, logger, response_timeout):
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(handle_bank_command, command, client_ip, bank, logger)
        try:
            result = future.result(timeout=response_timeout)
            # Save data after each operation.
            bank.save_data()
            return result
        except concurrent.futures.TimeoutError:
            logger.log("ER", client_ip, command, "TIMEOUT PROCESSING COMMAND")
            return "ER TIMEOUT PROCESSING COMMAND"


# --- BankServer class – handles client connections using bank commands only ---
class BankServer:
    def __init__(self, bank, logger, response_timeout=5):
        self.bank = bank
        self.logger = logger
        self.response_timeout = response_timeout
        self.clients = []

    def process_command(self, command, client_socket):
        try:
            client_ip = client_socket.getpeername()[0]
        except Exception:
            client_ip = "0.0.0.0"
        return process_bank_command(command, client_ip, self.bank, self.logger, self.response_timeout)

    def handle_client(self, client_socket):
        self.clients.append(client_socket)
        try:
            client_socket.send("WELCOME TO THE BANK SERVER!\r\n".encode("utf-8"))
        except Exception:
            pass
        buffer = ""
        while True:
            try:
                data = client_socket.recv(1024).decode("utf-8")
                if not data:
                    break
                buffer += data
                while "\r\n" in buffer:
                    command, buffer = buffer.split("\r\n", 1)
                    # Convert input to uppercase.
                    command = command.strip().upper()
                    print(f"Received command: {command}")
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
