"""Read-only Android performance snapshot for a dedicated test device.

Run from a trusted PC with adb installed: python tools/android_perf_snapshot_v1.py PACKAGE
Collect before/after the same manual flow in each candidate. No install, force-stop,
reset, logcat, raw dumps or network access by this script.
"""
import argparse
import json
import re
import subprocess
import sys
import unittest

PACKAGE = re.compile(r"[A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z][A-Za-z0-9_]*)+\Z")
METRICS = {
    "frames": r"(?m)^\s*Total frames rendered:\s*(\d+)",
    "janky_frames": r"(?m)^\s*Janky frames:\s*(\d+)",
    "p50_ms": r"(?m)^\s*50th percentile:\s*(\d+)ms",
    "p90_ms": r"(?m)^\s*90th percentile:\s*(\d+)ms",
    "p95_ms": r"(?m)^\s*95th percentile:\s*(\d+)ms",
    "p99_ms": r"(?m)^\s*99th percentile:\s*(\d+)ms",
    "total_pss_kb": r"(?m)^\s*TOTAL PSS:\s*(\d+)",
}

def parse(gfx, mem):
    result = {}
    for key, pattern in METRICS.items():
        source = mem if key == "total_pss_kb" else gfx
        matches = re.findall(pattern, source)
        # Multiple process summaries are ambiguous: do not combine them silently.
        result[key] = int(matches[0]) if len(matches) == 1 else None
    return result

def adb(*args):
    try:
        completed = subprocess.run(
            ["adb", *args], capture_output=True, text=True,
            errors="replace", timeout=30, check=True,
        )
    except (OSError, subprocess.SubprocessError):
        raise RuntimeError("ADB indisponivel ou comando falhou; confira o dispositivo autorizado.") from None
    return completed.stdout

def snapshot(package):
    if not PACKAGE.fullmatch(package):
        raise ValueError("Informe o package Android exato do candidato.")
    devices = [line.split() for line in adb("devices").splitlines()[1:] if line.strip()]
    if len(devices) != 1 or len(devices[0]) < 2 or devices[0][1] != "device":
        raise RuntimeError("Conecte somente um dispositivo de teste autorizado.")
    if not adb("shell", "pm", "path", package).strip().startswith("package:"):
        raise RuntimeError("Package de teste nao encontrado.")
    if not adb("shell", "pidof", package).strip():
        raise RuntimeError("Abra o candidato no aparelho antes de medir.")
    gfx = adb("shell", "dumpsys", "gfxinfo", package)
    mem = adb("shell", "dumpsys", "meminfo", package)
    return {"package": package, "metrics": parse(gfx, mem),
            "scope": "snapshot cumulativo; nao mede startup nem prova estabilidade"}

class ParserTests(unittest.TestCase):
    def test_values(self):
        self.assertEqual(parse("Total frames rendered: 100\nJanky frames: 4 (4%)\n95th percentile: 21ms", "TOTAL PSS: 120000 TOTAL RSS: 50000")["total_pss_kb"], 120000)
        self.assertEqual(parse("Total frames rendered: 100\nJanky frames: 4 (4%)", "")["janky_frames"], 4)
    def test_missing_and_multiple(self):
        self.assertIsNone(parse("", "")["frames"])
        self.assertIsNone(parse("Total frames rendered: 1\nTotal frames rendered: 2", "")["frames"])
    def test_package(self):
        self.assertIsNotNone(PACKAGE.fullmatch("com.example.homolog"))
        self.assertIsNone(PACKAGE.fullmatch("com.example;reboot"))

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", nargs="?")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return 0 if unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromTestCase(ParserTests)).wasSuccessful() else 1
    if not args.package:
        parser.error("Informe o package ou --self-test")
    try:
        print(json.dumps(snapshot(args.package), indent=2))
    except (ValueError, RuntimeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
