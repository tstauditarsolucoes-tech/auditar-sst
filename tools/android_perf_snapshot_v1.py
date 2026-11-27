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
from unittest.mock import patch

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

def adb(*args, serial=None):
    try:
        completed = subprocess.run(
            ["adb", *(["-s", serial] if serial else []), *args], capture_output=True, text=True,
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
    serial = devices[0][0]
    def shell(*args):
        return adb("shell", *args, serial=serial)
    if not shell("pm", "path", package).strip().startswith("package:"):
        raise RuntimeError("Package de teste nao encontrado.")
    pid = shell("pidof", package).strip()
    if not re.fullmatch(r"[1-9][0-9]*", pid):
        raise RuntimeError("Abra o candidato no aparelho antes de medir.")
    gfx = shell("dumpsys", "gfxinfo", package)
    mem = shell("dumpsys", "meminfo", package)
    if shell("pidof", package).strip() != pid:
        raise RuntimeError("Processo mudou durante a medicao; repita o roteiro.")
    metrics = parse(gfx, mem)
    if metrics["frames"] is not None and metrics["janky_frames"] is not None and metrics["janky_frames"] > metrics["frames"]:
        metrics["frames"] = metrics["janky_frames"] = None
    if all(value is None for value in metrics.values()):
        raise RuntimeError("Nenhuma metrica reconhecida; nao interpretar como desempenho aprovado.")
    return {"package": package, "metrics": metrics,
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

class SnapshotTests(unittest.TestCase):
    def test_only_read_commands_and_pinned_device(self):
        outputs = ["List of devices attached\nTEST123\tdevice\n", "package:/test.apk",
                   "321", "Total frames rendered: 50\nJanky frames: 5 (10%)",
                   "TOTAL PSS: 9876", "321"]
        with patch(__name__ + ".adb", side_effect=outputs) as mock:
            result = snapshot("com.example.homolog")
        self.assertEqual(result["metrics"]["frames"], 50)
        self.assertEqual(result["metrics"]["total_pss_kb"], 9876)
        self.assertNotIn("TEST123", json.dumps(result))
        self.assertEqual([c.args for c in mock.call_args_list], [
            ("devices",), ("shell", "pm", "path", "com.example.homolog"),
            ("shell", "pidof", "com.example.homolog"),
            ("shell", "dumpsys", "gfxinfo", "com.example.homolog"),
            ("shell", "dumpsys", "meminfo", "com.example.homolog"),
            ("shell", "pidof", "com.example.homolog")])
        self.assertTrue(all(c.kwargs == {"serial": "TEST123"} for c in mock.call_args_list[1:]))

    def test_reject_multiple_or_unauthorized_devices(self):
        for devices in ["A\tdevice\nB\tdevice", "A\tunauthorized", ""]:
            with patch(__name__ + ".adb", return_value="List of devices attached\n" + devices) as mock:
                with self.assertRaises(RuntimeError):
                    snapshot("com.example.homolog")
                self.assertEqual(mock.call_count, 1)

    def test_reject_process_restart_or_no_metrics(self):
        for gfx, mem, final_pid in [
            ("Total frames rendered: 10", "TOTAL PSS: 1000", "322"),
            ("", "", "321"),
        ]:
            with patch(__name__ + ".adb", side_effect=[
                    "List of devices attached\nA\tdevice", "package:/test.apk",
                    "321", gfx, mem, final_pid]):
                with self.assertRaises(RuntimeError):
                    snapshot("com.example.homolog")

    def test_invalid_package_never_calls_adb(self):
        with patch(__name__ + ".adb") as mock:
            with self.assertRaises(ValueError):
                snapshot("com.example;reboot")
            mock.assert_not_called()

    def test_adb_command_and_sanitized_error(self):
        with patch("subprocess.run", return_value=subprocess.CompletedProcess([], 0, stdout="ok")) as mock:
            self.assertEqual(adb("shell", "pidof", "com.example", serial="A"), "ok")
            self.assertEqual(mock.call_args.args[0], ["adb", "-s", "A", "shell", "pidof", "com.example"])
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("secret-like", 30)):
            with self.assertRaisesRegex(RuntimeError, "ADB indisponivel") as cm:
                adb("devices")
            self.assertNotIn("secret-like", str(cm.exception))

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", nargs="?")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return 0 if unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])).wasSuccessful() else 1
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
