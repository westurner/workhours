from passlib.hash import pbkdf2_sha512

def hash_passphrase(salt, passphrase):
    return pbkdf2_sha512.encrypt(passphrase,
            salt=(salt and salt.encode('hex')))
