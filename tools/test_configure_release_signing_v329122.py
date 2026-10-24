#!/usr/bin/env python3
"""Regression tests: release signing must not fall back to an ephemeral debug key."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).with_name("configure_release_signing_v329122.py")
TEMPLATE = """plugins { id("com.android.application") }
android {
    namespace = "br.com.auditar.auditar_sst"
    defaultConfig {
        applicationId = "br.com.auditar.auditar_sst"
    }
    buildTypes {
        release {
            signingConfig = signingConfigs.getByName("debug")
        }
    }
}
"""


def apply(template):
    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)
        file = root / "android/app/build.gradle.kts"
        file.parent.mkdir(parents=True)
        file.write_text(template, encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(root)],
            text=True, capture_output=True, check=False,
        )
        return result, file.read_text(encoding="utf-8")


class ReleaseSigningTests(unittest.TestCase):
    def test_signer_is_original_key_only(self):
        result, content = apply(TEMPLATE)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('create("auditarRelease")', content)
        self.assertIn('signingConfig = signingConfigs.getByName("auditarRelease")', content)
        self.assertNotIn('signingConfig = signingConfigs.getByName("debug")', content)
        self.assertIn('applicationId = "br.com.auditar.auditar_sst"', content)
        self.assertIn('AUDITAR_ANDROID_KEYSTORE_PATH', content)

    def test_wrong_package_is_blocked_and_source_is_not_modified(self):
        altered = TEMPLATE.replace(
            'applicationId = "br.com.auditar.auditar_sst"',
            'applicationId = "br.com.auditar.auditar_sst.teste"',
        )
        result, content = apply(altered)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(altered, content)

    def test_unknown_signing_template_is_blocked(self):
        altered = TEMPLATE.replace('signingConfigs.getByName("debug")',
                                   'signingConfigs.getByName("release")')
        result, content = apply(altered)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(altered, content)


if __name__ == "__main__":
    unittest.main()
