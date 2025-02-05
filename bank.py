import threading
import json
import os

class Bank:
    def __init__(self, bank_code):
        self.bank_code = bank_code  # e.g. automatically obtained local IP address
        self.accounts = {}  # key: account number (int), value: current balance
        self.account_lock = threading.Lock()
        self.next_account_number = 10000  # initial account number
        self.free_accounts = []  # list of recycled account numbers

    def create_account(self):
        with self.account_lock:
            if self.free_accounts:
                # Recycle the smallest available account number
                account_number = self.free_accounts.pop(0)
            else:
                if self.next_account_number > 99999:
                    raise Exception("OUR BANK DOES NOT ALLOW NEW ACCOUNT CREATION.")
                account_number = self.next_account_number
                self.next_account_number += 1
            self.accounts[account_number] = 0
        return account_number

    def deposit(self, account_number, amount):
        with self.account_lock:
            if account_number not in self.accounts:
                raise Exception("ACCOUNT NUMBER AND AMOUNT ARE NOT IN THE CORRECT FORMAT.")
            self.accounts[account_number] += amount

    def withdraw(self, account_number, amount):
        with self.account_lock:
            if account_number not in self.accounts:
                raise Exception("ACCOUNT NUMBER AND AMOUNT ARE NOT IN THE CORRECT FORMAT.")
            if self.accounts[account_number] < amount:
                raise Exception("INSUFFICIENT FUNDS")
            self.accounts[account_number] -= amount

    def get_balance(self, account_number):
        with self.account_lock:
            if account_number not in self.accounts:
                raise Exception("THE ACCOUNT NUMBER FORMAT IS NOT CORRECT.")
            return self.accounts[account_number]

    def remove_account(self, account_number):
        with self.account_lock:
            if account_number not in self.accounts:
                raise Exception("THE ACCOUNT NUMBER FORMAT IS NOT CORRECT.")
            if self.accounts[account_number] != 0:
                raise Exception("CANNOT DELETE AN ACCOUNT THAT HAS FUNDS.")
            del self.accounts[account_number]
            # Recycle the account number for future use.
            self.free_accounts.append(account_number)
            self.free_accounts.sort()

    def get_total_amount(self):
        with self.account_lock:
            return sum(self.accounts.values())

    def get_client_count(self):
        with self.account_lock:
            return len(self.accounts)

    def save_data(self, file_name="accounts.json"):
        with self.account_lock:
            data = {
                "accounts": self.accounts,
                "free_accounts": self.free_accounts,
                "next_account_number": self.next_account_number
            }
        with open(file_name, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def load_data(self, file_name="accounts.json"):
        if os.path.exists(file_name):
            try:
                with open(file_name, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.accounts = {int(k): v for k, v in data.get("accounts", {}).items()}
                    self.free_accounts = sorted([int(x) for x in data.get("free_accounts", [])])
                    self.next_account_number = data.get("next_account_number", 10000)
            except Exception:
                # If loading fails, keep default values.
                pass
