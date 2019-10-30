import tempfile
import os
import argparse
from datetime import datetime
from subprocess import call
from getpass import getpass
from hashlib import sha512
import pyAesCrypt
import git

EDITOR = os.environ.get('EDITOR', 'vim')
VIEWER = 'less'

ENCRYPTED_FILE = "/home/sidgupta/Competitions/journal/data/enc_journal.aes"
DECRYPTED_FILE = "/home/sidgupta/Competitions/journal/data/dec_journal.txt"


class Journal:
    def __init__(self):
        self.salt = "4ctUnojNULLh811F"
        self.heading = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.password = None
        self.message = None
        self.repo = git.Repo(os.path.dirname(ENCRYPTED_FILE))

    def get_password(self):
        """
        Takes password as input to be used to encrypt/decrypt the journal
        :return: None
        """
        password = getpass("Enter Password: ")

        if not os.path.exists(ENCRYPTED_FILE):
            confirm_password = getpass("Confirm Password: ")

            while password != confirm_password:
                print("Passwords don't match, enter again")
                password = getpass("Enter Password: ")
                confirm_password = getpass("Confirm Password: ")

        salted_pass = bytes(self.salt + password + self.salt, 'utf-8')

        for i in range(1000):
            salted_pass = sha512(salted_pass).digest()

        self.password = str(salted_pass)

        if os.path.exists(ENCRYPTED_FILE):
            if self.decrypt():
                os.remove(DECRYPTED_FILE)
            else:
                self.password = None
                self.get_password()

    def decrypt(self):
        """
        Decrypt the journal
        :return:
        """
        if self.password is None:
            self.get_password()

        if not os.path.exists(ENCRYPTED_FILE):
            print("Encrypted file not found!")
            return False

        try:
            pyAesCrypt.decryptFile(ENCRYPTED_FILE, DECRYPTED_FILE, self.password, 16*1024)
        except ValueError as e:
            print(e)
            return False
        return True

    def encrypt(self):
        """
        Encrypt the journal
        :return:
        """
        if os.path.exists(DECRYPTED_FILE):
            pyAesCrypt.encryptFile(DECRYPTED_FILE, ENCRYPTED_FILE, self.password, 16*1024)
            os.remove(DECRYPTED_FILE)
        else:
            print("Decrypted file not found for encryption")

    def get_entry(self):
        """
        Take journal entry from user using EDITOR
        :return:
        """
        self.heading = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        with tempfile.NamedTemporaryFile(mode='r+', suffix=".tmp") as tf:
            tf.write(self.heading + '\n\n')
            tf.flush()
            call([EDITOR, tf.name])

            tf.seek(0)
            message = tf.read()

        self.message = message

    def append_message(self):
        """
        Append the new journal entry to the main journal
        :return:
        """
        message = "\n" + self.message
        if os.path.exists(ENCRYPTED_FILE):
            if self.decrypt():
                with open(DECRYPTED_FILE, 'a') as fp:
                    fp.write(message)
                self.encrypt()
            else:
                print("Could not add message, decryption failed")
        else:
            initial_message = "Journal\n"
            with open(DECRYPTED_FILE, 'w') as fp:
                fp.write(initial_message)
                fp.write(message)
            self.encrypt()

    def commit(self):
        self.repo.index.add(ENCRYPTED_FILE)
        self.repo.index.commit("Added journal entry for {}".format(self.heading))
        origin = self.repo.remote("origin")
        origin.push(refspec='master:master')

    def create_entry(self):
        """
        Create journal entry
        :return:
        """
        self.get_password()
        self.get_entry()
        self.append_message()
        self.commit()

    def show_journal(self):
        self.decrypt()
        call([VIEWER, DECRYPTED_FILE])
        self.encrypt()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Secure Journal")
    parser.add_argument('--read', action='store_true')
    args = parser.parse_args()

    if args.read:
        journal = Journal()
        journal.show_journal()
    else:
        journal = Journal()
        journal.create_entry()
