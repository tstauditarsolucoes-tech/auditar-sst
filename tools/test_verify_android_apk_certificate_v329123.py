#!/usr/bin/env python3
"""Regression tests for old and current Android apksigner output formats."""
import unittest
from verify_android_apk_certificate_v329123 import verify

CERT = "9E0558D89B6D617E1EF4EFCFF8FBDB126BCBB1646466505F3E7016E83080FABC"
DIFFERENT = "0" * 64

class ApkSignerVerificationTests(unittest.TestCase):
    def test_android_v2_output(self):
        actual = verify("V2 Signer: certificate SHA-256 digest: " + CERT.lower(), CERT)
        self.assertEqual(actual, CERT)

    def test_legacy_output(self):
        self.assertEqual(
            verify("Signer #1 certificate SHA-256 digest: " + CERT.lower(), CERT),
            CERT,
        )

    def test_multiple_matching_signing_schemes(self):
        output = (
            "V1 Signer: certificate SHA-256 digest: " + CERT.lower()
            + "\nV2 Signer: certificate SHA-256 digest: " + CERT.lower()
        )
        self.assertEqual(verify(output, CERT), CERT)

    def test_missing_and_conflicting_are_blocked(self):
        for output in (
            "",
            "certificate SHA-256 digest: " + DIFFERENT,
            "V2 Signer: certificate SHA-256 digest: " + CERT.lower()
            + "\nV3 Signer: certificate SHA-256 digest: " + DIFFERENT,
        ):
            with self.subTest(output=output):
                with self.assertRaises(ValueError):
                    verify(output, CERT)

if __name__ == "__main__":
    unittest.main()
