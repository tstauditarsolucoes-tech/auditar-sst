#!/usr/bin/env python3
"""Repair company logo cache/Drive recovery without changing structured sync."""
from pathlib import Path
import sys
root=Path(sys.argv[1]); platform=sys.argv[2]
assert platform in ('android','windows')
def replace_one(s,a,b,label):
 n=s.count(a)
 if n!=1: raise RuntimeError(f'{label}: expected one occurrence, got {n}')
 return s.replace(a,b,1)
p=root/'lib/services/media_sync_service.dart'
s=p.read_text(encoding='utf-8')
start=s.index('  static Future<int> restoreCompanyLogos({')
end=s.index('  static Future<int> restoreInspectionMedia(',start)
section=s[start:end]
section=replace_one(section,
"""      final lookedUp = await _lookupAssetOnDrive(db, asset);
      if (lookedUp != null) asset = lookedUp;
      if ('${asset['drive_file_id'] ?? ''}'.trim().isEmpty) continue;

      try {
        if (await _downloadAsset(db, asset)) recovered++;
      } catch (_) {
        // Falha de rede não apaga a logo nem bloqueia os dados estruturados.
      }""",
"""      // The structured company snapshot can contain a filesystem path from
      // another device. Reuse our own cached media before making network calls.
      final cachedPath = '${asset['local_path'] ?? ''}'.trim();
      if (cachedPath.isNotEmpty && await File(cachedPath).exists()) {
        await _applyEntityPath(db, asset, cachedPath);
        recovered++;
        continue;
      }

      // A known Drive id is enough to recover offline-cache loss. If it has
      // become stale (e.g. logo replaced), resolve the current catalog id too.
      var downloaded = false;
      if ('${asset['drive_file_id'] ?? ''}'.trim().isNotEmpty) {
        try {
          downloaded = await _downloadAsset(db, asset);
        } catch (_) {}
      }
      if (downloaded) {
        recovered++;
        continue;
      }
      final lookedUp = await _lookupAssetOnDrive(db, asset);
      if (lookedUp != null) asset = lookedUp;
      if ('${asset['drive_file_id'] ?? ''}'.trim().isEmpty) continue;
      try {
        if (await _downloadAsset(db, asset)) recovered++;
      } catch (_) {
        // A missing remote backup cannot be reconstructed; keep the company.
      }""",'cache-first and remote recovery')
s=s[:start]+section+s[end:]
p.write_text(s,encoding='utf-8',newline='\n')

p=root/'lib/screens/companies_screen.dart'
s=p.read_text(encoding='utf-8')
s=replace_one(s,"  bool recoveringLogos = false;","  bool recoveringLogos = false;\n  bool _restoringMissingLogos = false;",'in-flight flag')
s=replace_one(s,
"""  Future<void> _restoreMissingCompanyLogos(List<Company> snapshot) async {
    final missing = <String>[];""",
"""  Future<void> _restoreMissingCompanyLogos(List<Company> snapshot) async {
    if (_restoringMissingLogos || recoveringLogos) return;
    final missing = <String>[];""",'guard reentry')
s=replace_one(s,
"""    if (missing.isEmpty) return;

    try {
      final restored = await MediaSyncService.restoreCompanyLogos(
        companyIds: missing,
      ).timeout(const Duration(seconds: 45));
      if (restored <= 0 || !mounted) return;
      final refreshed = await AppDatabase.instance.getCompanies(
        onlyActive: false,
      );
      if (!mounted) return;
      setState(() => companies = refreshed);
    } catch (_) {
      // A ausência de internet não interfere na lista de empresas.
    }
  }""",
"""    if (missing.isEmpty) return;
    _restoringMissingLogos = true;
    try {
      final restored = await MediaSyncService.restoreCompanyLogos(
        companyIds: missing,
      ).timeout(const Duration(seconds: 45));
      if (restored <= 0 || !mounted) return;
      final refreshed = await AppDatabase.instance.getCompanies(
        onlyActive: false,
      );
      if (!mounted) return;
      setState(() => companies = refreshed);
    } catch (_) {
      // A ausência de internet não interfere na lista de empresas.
    } finally {
      _restoringMissingLogos = false;
    }
  }""",'nonblocking refresh guarded')
s=replace_one(s,
"""      if (recovered > 0) await _load();
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(
        recovered > 0
          ? '$recovered logo(s) recuperada(s) do backup.'
          : 'Nenhuma logo disponível no backup da Central. Os cadastros foram preservados.',
      )));""",
"""      // Always refresh: cached images may have been relinked in this device.
      final refreshed = await AppDatabase.instance.getCompanies(
        onlyActive: false,
      );
      if (!mounted) return;
      setState(() => companies = refreshed);
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(
        recovered > 0
          ? '$recovered logo(s) recuperada(s) do aparelho ou do backup.'
          : 'Nenhuma logo recuperável foi localizada. Cadastros preservados; confira outro aparelho ou recadastre a imagem.',
      )));""",'accurate user message')
s=replace_one(s,
"""    if(old!=null&&old.isNotEmpty&&old!=stored){try{final f=File(old);if(await f.exists())await f.delete();}catch(_){}}""",
"""    // Keep the preceding image until the replacement is protected remotely.
    if(synced && old!=null&&old.isNotEmpty&&old!=stored){
      try{final f=File(old);if(await f.exists())await f.delete();}catch(_){}
    }""",'backup fallback on failed upload')
s=replace_one(s,
"""          child: Image.file(File(path), fit: BoxFit.contain),""",
"""          child: Image.file(File(path), fit: BoxFit.contain,
            errorBuilder: (_, __, ___) => const Icon(
              Icons.business_rounded, color: AuditarBrand.navy)),""",'bad image guard')
p.write_text(s,encoding='utf-8',newline='\n')

# Do not change device_sync_service or sync_coordinator.
pub=root/'pubspec.yaml';s=pub.read_text(encoding='utf-8')
old,new={'android':('3.29.112+254','3.29.113+255'),'windows':('3.30.36+223','3.30.37+224')}[platform]
s=replace_one(s,'version: '+old,'version: '+new,'version bump')
pub.write_text(s,encoding='utf-8',newline='\n')
print('COMPANY_LOGO_RECOVERY_CACHE_FIRST_OK',platform,new)
