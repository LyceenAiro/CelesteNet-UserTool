import hashlib
import os
import binascii

class PasswordHelper:
    @staticmethod
    def generate_salt():
        return binascii.hexlify(os.urandom(16)).decode('utf-8')
    
    @staticmethod
    def hash_password(password: str, salt: str):
        iterations = 100000
        key = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            iterations
        )
        return binascii.hexlify(key).decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, salt: str, stored_hash: str):
        new_hash = PasswordHelper.hash_password(password, salt)
        return new_hash == stored_hash
