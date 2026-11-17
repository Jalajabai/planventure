import unittest

from utils.security import generate_salt, hash_password, verify_password


class PasswordUtilsTests(unittest.TestCase):
    def test_hash_verifies_and_is_salted(self):
        first = hash_password('correct horse')
        second = hash_password('correct horse')

        self.assertNotEqual(first, second)
        self.assertNotIn('correct horse', first)
        self.assertTrue(verify_password('correct horse', first))
        self.assertTrue(verify_password('correct horse', second))
        self.assertFalse(verify_password('wrong', first))

    def test_explicit_salt_is_reproducible(self):
        salt = generate_salt(rounds=4)

        self.assertTrue(salt.startswith('$2b$04$'))
        self.assertEqual(hash_password('pw', salt), hash_password('pw', salt))
        self.assertNotEqual(generate_salt(rounds=4), salt)

    def test_unicode_password(self):
        password_hash = hash_password('pässwörd-密码', generate_salt(rounds=4))
        self.assertTrue(verify_password('pässwörd-密码', password_hash))

    def test_invalid_passwords_rejected(self):
        for password in ('', None, 123, 'a' * 73, 'é' * 37):
            with self.subTest(password=password):
                with self.assertRaises(ValueError):
                    hash_password(password)
        self.assertTrue(verify_password('a' * 72, hash_password('a' * 72, generate_salt(4))))

    def test_malformed_hash_never_matches(self):
        for stored in ('', 'not-a-hash', None, '$2b$04$short'):
            with self.subTest(stored=stored):
                self.assertFalse(verify_password('pw', stored))
        self.assertFalse(verify_password('', hash_password('pw', generate_salt(4))))


if __name__ == '__main__':
    unittest.main()
