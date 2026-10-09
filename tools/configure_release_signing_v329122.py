#!/usr/bin/env python3
"""Configure only the generated Android release signer; preserve app identity/data.

Run after flutter create. Secrets are passed through environment variables;
do not commit a keystore, passwords, or a debug signing fallback.
"""
from pathlib import Path
import re
import sys

root = Path(sys.argv[1])
gradle = root / "android/app/build.gradle.kts"
source = gradle.read_text(encoding="utf-8")
package = 'br.com.auditar.auditar_sst'
if not re.search(r'\bapplicationId\s*=\s*"' + re.escape(package) + r'"', source):
    raise SystemExit("SAFE_SIGNING: package ID changed; refusing release")
debug = 'signingConfig = signingConfigs.getByName("debug")'
if source.count(debug) != 1:
    raise SystemExit("SAFE_SIGNING: expected one debug release signer; inspect Gradle template")
if source.count("    buildTypes {") != 1:
    raise SystemExit("SAFE_SIGNING: unsupported Gradle template; no edit performed")
config = '''    signingConfigs {
        create("auditarRelease") {
            storeFile = file(System.getenv("AUDITAR_ANDROID_KEYSTORE_PATH")
                ?: error("AUDITAR_ANDROID_KEYSTORE_PATH is required"))
            storePassword = System.getenv("AUDITAR_ANDROID_STORE_PASSWORD")
                ?: error("AUDITAR_ANDROID_STORE_PASSWORD is required")
            keyAlias = System.getenv("AUDITAR_ANDROID_KEY_ALIAS")
                ?: error("AUDITAR_ANDROID_KEY_ALIAS is required")
            keyPassword = System.getenv("AUDITAR_ANDROID_KEY_PASSWORD")
                ?: error("AUDITAR_ANDROID_KEY_PASSWORD is required")
        }
    }

'''
source = source.replace("    buildTypes {", config + "    buildTypes {", 1)
source = source.replace(debug, 'signingConfig = signingConfigs.getByName("auditarRelease")', 1)
assert debug not in source
assert source.count('signingConfig = signingConfigs.getByName("auditarRelease")') == 1
gradle.write_text(source, encoding="utf-8", newline="\n")
print("SAFE_SIGNING_CONFIGURED: release only; package ID and other files unchanged")
