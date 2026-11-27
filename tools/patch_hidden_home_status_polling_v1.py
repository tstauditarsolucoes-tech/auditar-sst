"""Proposed UI-only removal of unused automatic sync-status queries.

Run ONLY on assembled homologation sources, never an installed app.
Reject unfamiliar source rather than guessing. Keep actual sync unchanged.
"""
from pathlib import Path
import argparse
import re
import unittest

EVENT = "      if (result.mediaChanged) unawaited(_refreshSyncStatus());\n"
REFRESH = "      unawaited(_refreshSyncStatus());\n"
CARD = r"\b_syncQueueCard\s*\("
STATUS = r"\b_refreshSyncStatus\s*\("

def transform(source):
    if len(re.findall(CARD, source)) != 1 or not re.search(
            r"\bWidget\s+_syncQueueCard\s*\(", source):
        raise ValueError("Cartao pode estar em uso; nenhuma alteracao")
    if not re.search(r"\bFuture<void>\s+_refreshSyncStatus\s*\(", source):
        raise ValueError("Metodo de status desconhecido")
    if len(re.findall(STATUS, source)) != 4:
        raise ValueError("Chamadas de status divergentes; revisar fonte")
    if source.count(EVENT) != 1 or source.count(REFRESH) != 1:
        raise ValueError("Gatilhos automaticos divergentes; revisar fonte")
    if "DeviceSyncService.events.listen" not in source or "_syncImmediatelyOnHomeEntry()" not in source:
        raise ValueError("Fluxo de sync esperado ausente")
    # Do not remove the method or manual retry path; just the two known
    # automatic calls that feed the no-longer-rendered card.
    updated = source.replace(EVENT, "", 1).replace(REFRESH, "", 1)
    if len(re.findall(STATUS, updated)) != 2:
        raise ValueError("Contagem final divergente")
    if updated.count("DeviceSyncService.synchronize(") != source.count("DeviceSyncService.synchronize("):
        raise ValueError("Sync alterado")
    return updated

def apply(root):
    path = root / "lib/screens/home_screen.dart"
    if path.is_symlink() or path.resolve().parent != (root.resolve() / "lib/screens"):
        raise ValueError("Caminho inesperado")
    original = path.read_text(encoding="utf-8")
    updated = transform(original)
    path.write_text(updated, encoding="utf-8", newline="\n")

FIXTURE = """  Widget _syncQueueCard() { return Card(); }
  Future<void> _refreshSyncStatus() async {}
  Future<void> _retryEvidenceUpload() async {
      await DeviceSyncService.sendPendingMediaNow();
      await _refreshSyncStatus();
  }
  Future<void> _syncImmediatelyOnHomeEntry() async {
      await DeviceSyncService.synchronize(force: true);
  }
  void listen() {
    _deviceSyncSubscription = DeviceSyncService.events.listen((result) {
      if (!mounted) return;
      if (result.mediaChanged) unawaited(_refreshSyncStatus());
      if (result.received <= 0) return;
      unawaited(_refresh(showLoading: false));
    });
  }
  Future<void> _refresh() async {
      unawaited(_refreshSyncStatus());
  }
"""

class Tests(unittest.TestCase):
    def test_exact_change(self):
        updated = transform(FIXTURE)
        self.assertEqual(updated, FIXTURE.replace(EVENT, "").replace(REFRESH, ""))
        self.assertIn("DeviceSyncService.synchronize(force: true)", updated)
        self.assertIn("DeviceSyncService.sendPendingMediaNow()", updated)
        self.assertIn("unawaited(_refresh(showLoading: false))", updated)
        self.assertIn("await _refreshSyncStatus();", updated)
    def test_visible_card_blocks(self):
        with self.assertRaises(ValueError):
            transform(FIXTURE + "\n_syncQueueCard();")
    def test_extra_status_call_blocks(self):
        with self.assertRaises(ValueError):
            transform(FIXTURE + "\n_refreshSyncStatus();")
    def test_unknown_anchor_blocks(self):
        with self.assertRaises(ValueError):
            transform(FIXTURE.replace(EVENT, ""))
    def test_already_applied_blocks(self):
        with self.assertRaises(ValueError):
            transform(transform(FIXTURE))
    def test_preserve_file_on_failed_validation(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "lib/screens/home_screen.dart"
            p.parent.mkdir(parents=True)
            p.write_text(FIXTURE + "\n_syncQueueCard();")
            before = p.read_bytes()
            with self.assertRaises(ValueError):
                apply(Path(tmp))
            self.assertEqual(p.read_bytes(), before)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        unittest.main(argv=["self-test"])
    elif args.root is not None:
        apply(args.root)
        print("HIDDEN_HOME_STATUS_POLLING_REMOVED_UI_ONLY")
    else:
        parser.error("Informe a raiz montada ou --self-test")
