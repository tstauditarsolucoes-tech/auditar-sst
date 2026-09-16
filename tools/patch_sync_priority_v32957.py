from pathlib import Path
import re
import sys

root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('app/Auditar_SST_v1_5_dashboard')
pub = root / 'pubspec.yaml'
round_screen = root / 'lib/screens/express_round_screen.dart'
companies = root / 'lib/screens/companies_screen.dart'

# Versiona a correção sem tocar no núcleo de sync rápido.
v = pub.read_text(encoding='utf-8')
assert 'version: 3.29.56+198' in v, 'versão base v3.29.56 não encontrada'
v = v.replace('version: 3.29.56+198', 'version: 3.29.57+199', 1)
pub.write_text(v, encoding='utf-8')

# Ronda: não bloquear a finalização com uma sincronização paralela da empresa.
r = round_screen.read_text(encoding='utf-8')
old = """    try {
      await ManagementPanelService.syncCompany(widget.company);
    } catch (_) {
      // A ronda permanece salva localmente e pode sincronizar depois.
    }
    if (!mounted) return;
"""
if old in r:
    r = r.replace(
        old,
        """    // A sincronização estruturada já é tratada pelo coordenador global.
    // Não abrir uma segunda sincronização aqui: isso concorria com o sync rápido.
    if (!mounted) return;
""",
        1,
    )
else:
    r = re.sub(
        r"\s*try \{\s*await ManagementPanelService\.syncCompany\(widget\.company\);\s*\} catch \(_\) \{.*?\}\s*if \(!mounted\) return;",
        "\n    // A sincronização estruturada já é tratada pelo coordenador global.\n    // Não abrir uma segunda sincronização aqui: isso concorria com o sync rápido.\n    if (!mounted) return;",
        r,
        count=1,
        flags=re.S,
    )
assert 'await ManagementPanelService.syncCompany(widget.company)' not in r
round_screen.write_text(r, encoding='utf-8')

# Empresas/logos: upload da logo não deve disparar um sync estruturado completo.
c = companies.read_text(encoding='utf-8')
pattern = re.compile(
    r"(await MediaSyncService\.uploadCompanyLogoNow\(company\.id\)\.timeout\(\s*const Duration\(seconds: 45\),\s*\);)\s*"
    r"await DeviceSyncService\.synchronize\(\s*force: true,?\s*\)\.timeout\(const Duration\(seconds: 45\)\);\s*"
    r"synced = true;",
    flags=re.S,
)
match = pattern.search(c)
if match:
    c = pattern.sub(
        r"\1\n      // A logo é mídia independente. O coordenador global cuida dos dados estruturados.\n      synced = true;",
        c,
        count=1,
    )
else:
    # Aceita variante com argumento syncMedia removido/formatado.
    c = c.replace(
        """      await MediaSyncService.uploadCompanyLogoNow(company.id).timeout(
        const Duration(seconds: 45),
      );
      await DeviceSyncService.synchronize(
        force: true,
      ).timeout(const Duration(seconds: 45));
      synced = true;
""",
        """      await MediaSyncService.uploadCompanyLogoNow(company.id).timeout(
        const Duration(seconds: 45),
      );
      // A logo é mídia independente. O coordenador global cuida dos dados estruturados.
      synced = true;
""",
        1,
    )

# Recuperação de logos continua automática, mas só depois do primeiro ciclo do sync rápido.
old_call = "    _restoreMissingCompanyLogos(result);\n"
new_call = """    Future.delayed(const Duration(seconds: 15), () {
      if (!mounted) return;
      _restoreMissingCompanyLogos(result);
    });
"""
assert old_call in c, 'chamada automática de restauração de logos não encontrada'
c = c.replace(old_call, new_call, 1)

# Limita a recuperação automática a uma logo por abertura da tela; as demais entram nas próximas aberturas.
old_missing = """      final restored = await MediaSyncService.restoreCompanyLogos(
        companyIds: missing,
      );
"""
new_missing = """      final restored = await MediaSyncService.restoreCompanyLogos(
        companyIds: missing.take(1),
      ).timeout(const Duration(seconds: 12));
"""
assert old_missing in c, 'bloco restoreCompanyLogos não encontrado'
c = c.replace(old_missing, new_missing, 1)

companies.write_text(c, encoding='utf-8')

# Garantias locais.
assert 'version: 3.29.57+199' in pub.read_text(encoding='utf-8')
assert 'Duration(seconds: 15)' in c
assert 'missing.take(1)' in c
assert 'await ManagementPanelService.syncCompany(widget.company)' not in r
# Não aceita sync estruturado imediatamente depois do upload de logo.
pos = c.find('MediaSyncService.uploadCompanyLogoNow(company.id)')
assert pos >= 0
window = c[pos:pos+700]
assert 'DeviceSyncService.synchronize' not in window

print('Android v3.29.57+199: sync estruturado priorizado; logos e Ronda desacoplados do caminho crítico.')
