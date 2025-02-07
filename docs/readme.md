# Bank Server Application

## Documentation

This project implements a bank server according to the specified requirements. The server functions as a node in a peer-to-peer (p2p) network, where each node represents a bank. Communication is performed via TCP/IP using standardized commands. The application employs an object-oriented approach using the Command Pattern, recycles account numbers, saves account states to a JSON file after every operation (and on shutdown), and logs events to daily log files (valid JSON documents).

### Main Features

- **Network Communication:**  
  The server listens on ports in the range 65525–65535 (configurable via the `config.json` file) and automatically obtains its local IP address, which is used as the bank code.

- **Standardized Commands:**  
  The supported commands are:
  - `HELP` – displays a list of available commands.
  - `BC` – returns the bank code (IP address).
  - `AC` – creates a new bank account and returns its number (with recycled account numbers).
  - `AD <account>/<bank_code> <amount>` – deposits money into an account.
  - `AW <account>/<bank_code> <amount>` – withdraws money from an account.
  - `AB <account>/<bank_code>` – returns the account balance.
  - `AR <account>/<bank_code>` – deletes an account if its balance is zero.
  - `BA` – returns the total value of the bank (sum of all accounts).
  - `BN` – returns the number of clients (active accounts).

- **Proxy Functionality:**  
  The commands `AD`, `AW`, and `AB` check the bank code (IP) specified in the account field. If this code does not match the local bank code, the command is forwarded (proxied) to the remote server on the same standardized port. Commands must be terminated with `\r\n`.

- **Data Saving and Loading:**  
  The account state is saved to the file `accounts.json` after each operation and also upon server shutdown (for example, via Ctrl+C). When the server starts, it loads these data if they exist.

- **Logging:**  
  Log files are created daily and are named by date in the format `DD,MM,YYYY.json`. Each log entry includes a timestamp (with minute precision), the client's IP address, the command, and an optional error message.

- **Account Number Recycling:**  
  If an account is deleted (when its balance is zero), its number is recycled for future account creation.

- **Input Conversion to Uppercase:**  
  All input data is converted to uppercase to ensure uniformity of commands.

## How to Run the Application

1. **Configuration:**
   - Edit the `config.json` file (located in the src directory) to set the port (default: 65525). For example, the file should contain:
     ```json
     {
       "port": 65525
     }
     ```

2. **Starting the Server:**
   - Ensure that Python 3 is installed.
   - Ensure you are in src folder
   - Run the application from the command line:
     ```
     python main.py
     ```
   - The server will start listening on all interfaces (`0.0.0.0`) and automatically obtain its local IP address, which is used as the bank code.

3. **Controlling the Application:**
   - Commands are sent via TCP/IP and must be terminated with the sequence `\r\n`.
   - For example, to deposit money into an account, you can send:
     ```
     AD 11111/10.147.18.244 1000
     ```
     The command is processed locally if the bank code `10.147.18.244` matches your server's IP; otherwise, it is forwarded as a proxy to that remote server.
   - To view a list of all available commands, send:
     ```
     HELP
     ```

## Used Resources

1. **Source Information and Inspiration:**
   - Information and inspiration were gathered from a [ChatGPT conversation](https://chatgpt.com/share/67a65db9-1dc4-800a-98c9-aebea12a8a92) (including prompts and responses).
   - Python Socket API Documentation: [Python Socket Documentation](https://docs.python.org/3/library/socket.html)
   - Python Command Pattern tutorial: [YouTube](https://www.youtube.com/watch?v=bpOI2KijqN0&t=100s)
2. **Reused Source Code:**
   - Mostly 16.2,3.py from reused code folder, method handle_client, log method, basis for command pattern but later edited it so not much from it has left.

## Additional Information

- **Contact:**  
  For further information or inquiries, please contact me zajac@spsejecna.cz.

- **Note:**  
  When testing proxy functionality, ensure that remote servers are running on the same port specified in your configuration and that there are no network or firewall restrictions blocking access.
