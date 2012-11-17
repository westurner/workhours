import colander
import operator

def validate_password(node, value):
    """ checks to make sure that the value matches another value """
    if not value[0] == value[1]:
        raise colander.Invalid(node, "passwords do not match")

class PasswordItem(colander.TupleSchema):
    password = colander.SchemaNode(colander.String())
    confirm_password = colander.SchemaNode(colander.String())

class PasswordSchema(colander.Schema):
    password = PasswordItem(validator=validate_password)

import unittest
class TestColanderPassword(unittest.TestCase):
    def test_password_success(self):
        pw = PasswordSchema()
        I = {"password": ('one','one')}
        self.assertEqual(I, pw.deserialize(I))

    def test_password_fail(self):
        pw = PasswordSchema()
        I = {"password": ('one','two')}
        self.assertRaises(colander.Invalid, pw.deserialize, I)

    def test_password_null_fail(self):
        pw = PasswordSchema()
        I = {"password": ('one','')}
        self.assertRaises(colander.Invalid, pw.deserialize, I)
        I = {"password": ('','')}
        self.assertRaises(colander.Invalid, pw.deserialize, I)
        I = {"password": ('','one')}
        self.assertRaises(colander.Invalid, pw.deserialize, I)

if __name__=="__main__":
    unittest.main(verbosity=2)
#pw = Password('one','one')
#pw.serialize()
#pw2 = Password('one','two')
#pw.serialize()

