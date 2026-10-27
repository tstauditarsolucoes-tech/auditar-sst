#!/usr/bin/env python3
"""Validate an APK's public signing certificate from apksigner --print-certs.

Supports Android Build Tools outputs like:
- V2 Signer: certificate SHA-256 digest: <hex>
- Signer #1 certificate SHA-256 digest: <hex>
Rejects empty, malformed, and multiple conflicting certificates.
"""
from pathlib import Path
import os
import re
import sys


def certificate_digests(output: str) -> set[str]:
    return {
        match.group(1).upper()
        for match in re.finditer(
            r"certificate SHA-256 digest:\s*([0-9a-fA-F]{64})(?![0-9a-fA-F])",
            output,
            flags=re.IGNORECASE,
        )
    }


def verify(output: str, expected: str) -> str:
    clean_expected = re.sub(r"[:\s]", "", expected).upper()
    if not re.fullmatch(r"[0-9A-F]{64}", clean_expected):
        raise ValueError("invalid pinned certificate fingerprint")
    fingerprints = certificate_digests(output)
    if len(fingerprints) != 1:
        raise ValueError(
            "APK signing certificate missing or conflicting across signing schemes"
        )
    actual = next(iter(fingerprints))
    if actual != clean_expected:
        raise ValueError(
            f"APK certificate {actual} differs from pinned certificate {clean_expected}"
        )
    return actual


if __name__ == "__main__":
    content = Path(sys.argv[1]).read_text(encoding="utf-8")
    pinned = os.environ.get("AUDITAR_ANDROID_SIGNER_SHA256", "")
    try:
        verified = verify(content, pinned)
    except (ValueError, OSError) as error:
        print(f"::error::APK signing verification failed: {error}", file=sys.stderr)
        sys.exit(1)
    print(f"SAFE_APK_CERTIFICATE_VERIFIED: {verified}")
