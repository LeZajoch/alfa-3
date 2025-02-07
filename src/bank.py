"""
This module defines the Bank class which handles account management operations,
such as creating accounts (with recycling of deleted account numbers), deposit,
withdrawal, account deletion, and saving/loading the account data to/from a JSON file.
"""

import threading
import json
import os


class Bank:
    def __init__(self, bank_code):
        """
        Initializes the Bank instance.

        Args:
            bank_code (str): Unique identifier for the bank (typically the local IP address).
        """
        self.bank_code = bank_code
        self.accounts = {}  # key: account number (int), value: current balance
        self.account_lock = threading.Lock()
        self.next_account_number = 10000  # initial account number
        self.free_accounts = []  # list of recycled account numbers

    def create_account(self):
        """
        Creates a new account. Recycles the smallest available account number if possible.

        Returns:
            int: The new account number.

        Raises:
            Exception: If no new account can be created.
        """
        with self.account_lock:
            if self.free_accounts:
                # Recycle the smallest available account number.
                account_number = self.free_accounts.pop(0)
            else:
                if self.next_account_number > 99999:
                    raise Exception("OUR BANK DOES NOT ALLOW NEW ACCOUNT CREATION.")
                account_number = self.next_account_number
                self.next_account_number += 1
            self.accounts[account_number] = 0
        return account_number

    def deposit(self, account_number, amount):
        """
        Deposits the specified amount into the account.

        Args:
            account_number (int): The account number.
            amount (int): The amount to deposit.

        Raises:
            Exception: If the account number is not valid.
        """
        with self.account_lock:
            if account_number not in self.accounts:
                raise Exception("ACCOUNT NUMBER AND AMOUNT ARE NOT IN THE CORRECT FORMAT.")
            self.accounts[account_number] += amount

    def withdraw(self, account_number, amount):
        """
        Withdraws the specified amount from the account.

        Args:
            account_number (int): The account number.
            amount (int): The amount to withdraw.

        Raises:
            Exception: If the account number is not valid or funds are insufficient.
        """
        with self.account_lock:
            if account_number not in self.accounts:
                raise Exception("ACCOUNT NUMBER AND AMOUNT ARE NOT IN THE CORRECT FORMAT.")
            if self.accounts[account_number] < amount:
                raise Exception("INSUFFICIENT FUNDS")
            self.accounts[account_number] -= amount

    def get_balance(self, account_number):
        """
        Returns the current balance of the account.

        Args:
            account_number (int): The account number.

        Returns:
            int: The current balance.

        Raises:
            Exception: If the account number is not found.
        """
        with self.account_lock:
            if account_number not in self.accounts:
                raise Exception("THE ACCOUNT NUMBER FORMAT IS NOT CORRECT.")
            return self.accounts[account_number]

    def remove_account(self, account_number):
        """
        Removes an account if its balance is zero and recycles its number.

        Args:
            account_number (int): The account number to remove.

        Raises:
            Exception: If the account is not found or contains funds.
        """
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
        """
        Returns the total funds across all accounts.

        Returns:
            int: Total amount of funds in the bank.
        """
        with self.account_lock:
            return sum(self.accounts.values())

    def get_client_count(self):
        """
        Returns the number of active accounts.

        Returns:
            int: The count of accounts.
        """
        with self.account_lock:
            return len(self.accounts)

    def save_data(self, file_name="accounts.json"):
        """
        Saves the current bank data (accounts, free accounts, next account number) to a JSON file atomically.

        The data is first written to a temporary file, which is then atomically replaced to ensure consistency.

        Args:
            file_name (str): The name of the file to save the data.
        """
        with self.account_lock:
            data = {
                "accounts": self.accounts,
                "free_accounts": self.free_accounts,
                "next_account_number": self.next_account_number
            }
        temp_file = file_name + ".tmp"
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        os.replace(temp_file, file_name)  # Atomic replace

    def load_data(self, file_name="accounts.json"):
        """
        Loads bank data from a JSON file, if it exists.

        Args:
            file_name (str): The name of the file from which to load the data.
        """
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
