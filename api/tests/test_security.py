import unittest

from pydantic import ValidationError

from app.core.config import Config
from app.core.crypto import hash_password, verify_password
from app.core.jwt import create_token_pair, decode_access_token, decode_refresh_token


class SecurityTest(unittest.TestCase):
    def test_password_hash_round_trip(self):
        password_hash = hash_password("Password123!")

        self.assertNotEqual(password_hash, "Password123!")
        self.assertTrue(verify_password("Password123!", password_hash))
        self.assertFalse(verify_password("WrongPassword", password_hash))

    def test_token_pair_round_trip(self):
        access_token, refresh_token = create_token_pair(42, 3)

        access_payload = decode_access_token(access_token)
        refresh_payload = decode_refresh_token(refresh_token)
        self.assertIsNotNone(access_payload)
        self.assertIsNotNone(refresh_payload)
        self.assertEqual(access_payload["sub"], "42")
        self.assertEqual(access_payload["token_version"], 3)
        self.assertEqual(access_payload["type"], "access")
        self.assertEqual(refresh_payload["sub"], "42")
        self.assertEqual(refresh_payload["token_version"], 3)
        self.assertEqual(refresh_payload["type"], "refresh")

    def test_production_token_secrets_require_32_bytes(self):
        settings = {
            "_env_file": None,
            "APP_ENV": "production",
            "FRONTEND_ORIGINS": ["https://example.com"],
            "REFRESH_TOKEN_SECRET": "r" * 32,
        }

        with self.assertRaisesRegex(
            ValidationError,
            "ACCESS_TOKEN_SECRET must be at least 32 bytes for production",
        ):
            Config(ACCESS_TOKEN_SECRET="a" * 31, **settings)

        config = Config(ACCESS_TOKEN_SECRET="a" * 32, **settings)
        self.assertEqual(config.ACCESS_TOKEN_SECRET, "a" * 32)


if __name__ == "__main__":
    unittest.main()
