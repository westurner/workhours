import cryptacular.bcrypt

crypt = cryptacular.bcrypt.BCRYPTPasswordManager()
SALT = "88"

def salt_passphrase(passphrase,salt=SALT):
    return ':'.join((passphrase, salt))

def hash_passphrase(passphrase):
    return unicode(crypt.encode(salt_passphrase(passphrase)))
