import cryptacular.bcrypt

from sqlalchemy import Column
from sqlalchemy.orm import synonym
from sqlalchemy.types import Integer
from sqlalchemy.types import Unicode


from ..models import Base
from ..models import DBSession

crypt = cryptacular.bcrypt.BCRYPTPasswordManager()
SALT = "88"
def salt_passphrase(passphrase,salt=SALT):
    return ':'.join((passphrase, salt))

def hash_passphrase(passphrase):
    return unicode(crypt.encode(salt_passphrase(passphrase)))

class User(Base):
    """
    Application's user model.
    """
    __tablename__ = 'users'
    user_id = Column(Integer, primary_key=True)
    username = Column(Unicode(20), unique=True)
    name = Column(Unicode(50))
    email = Column(Unicode(50))

    _passphrase = Column('passphrase', Unicode(60))

    def _get_passphrase(self):
        return self._passphrase

    def _set_passphrase(self, passphrase):
        self._passphrase = hash_passphrase(passphrase)

    passphrase = property(_get_passphrase, _set_passphrase)
    passphrase = synonym('_passphrase', descriptor=passphrase)

    def __init__(self, username, passphrase, name, email):
        self.username = username
        self.name = name
        self.email = email
        self.passphrase = passphrase

    @classmethod
    def get_by_username(cls, username):
        return DBSession.query(cls).filter(cls.username==username).first()

    @classmethod
    def check_passphrase(cls, username, passphrase):
        user = cls.get_by_username(username)
        if not user:
            return False
        return crypt.check(user.passphrase,salt_passphrase(passphrase))


