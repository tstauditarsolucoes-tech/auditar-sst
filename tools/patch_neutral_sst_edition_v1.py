#!/usr/bin/env python3
from pathlib import Path
import base64
import re
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'app/Auditar_SST_v1_5_dashboard')

ICON_B64 = '''iVBORw0KGgoAAAANSUhEUgAAAgAAAAIACAYAAAD0eNT6AAAN3UlEQVR42u3dO1ZiWxiFUXCYY2Ri47QFmB3bgBm2oGxcJUb0gIrKUQ+LUjiPvf81Z37vhQ2c9YHiXW+G7XEFAES5cgQAIAAAAAEAAAgAAEAAAAACAAAQAACAAAAABAAAIAAAAAEAAAgAAEAAAAACAAAQAACAAAAABAAAIAAAQAAAAAIAABAAAIAAAAAEAAAgAAAAAQAACAAAQAAAAAIAABAAAIAAAAAEAAAgAAAAAQAACAAAQAAAgAAAAAQAACAAAAABAAAIAABAAAAAAgAAEAAAgAAAAAQAACAAAAABAAAIAABAAAAAAgAAEAAAgAAAAAEAAAgAAEAAAAACAAAQAACAAAAABAAAIAAAAAEAAAgAAEAAAAACAAAQAACAAAAABAAAIAAAAAEAAAIAABAAAIAAAAAEAAAgAAAAAQAACAAAQAAAAAIAABAAAIAAAAAEAAAgAAAAAQAACAAAQAAAAAIAAASAIwAAAQAACAAAQAAApRx2e4cAodabYXt0DGD0V6vV6ubp0QGBAABS3+0LARAAQMjoiwEQAED46IsBEACA4RcCIACA1NEXAyAAgPDRFwMgAADDLwRAAACpoy8GQAAA4aMvBkAAAIZfCIAAAFJHXwyAAACjjxgAAQBGHzEAAgAMP0IABAAYfcQACAAw+ogBEABg+IWAEAABAEZfDAACAIy+GAAEABh+IQAIADD6YgAEABh9xAAIADD8CAEQAGD0EQMgAMDoIwZAAIDhRwiAAACjjxgAAQBGHzEAAgAMP0IABAAYfcQACAAw+ogBEAAYfsOPEAABgNEHMQACAKPPhW7vh9Xb67ODEAMIADD8CaP/L2JACCAAwOgHDb8QEAMIADD6oaMvBsQAAgCMfvjoiwExgAAAwx8++mJACCAAwOgbfiEgBhAAGH2jnzr6YkAMIAAw/ISPvhgQAggAjD6GXwiIAQQARp/U0RcDYgABgOEnfPTFgBBAAGD0MfxCQAwgADD6Rh8xIAYQABh+o48YEAIIAIy+0UcMiAGmc+0IwPD3cqZCAAQAGP3wcxYDIADA6IsBBwJf5HcAgvg9AMNfnRAYh5//+wQAMPo+FQABAEYfMQACAAw/nT2mQgAEABh9nwo4EAQAGH3EAAgAMPoFfN9+G+3fdffyIAZAAIDhrzjy5/53qsWB3xcghb8DECbpbwFUHP25Bt+nBb9LigF/A8AnAGD0Df4ot7lCEPgRAQIADL/Rv+D+VIoBIYAAAKNv9ANjwKcCCAAw+ob/gvvuRwQgAMDwC4Eyz1UhgAAAo2/4g0NADCAAIHT0DX92CIgBWuXvAARq7W8BVP7rfIb/cpX/CmFrMeBvAPgEAAy/4feJwIyvAZ8KIAAw+safE+da9dMAPyJgCVeOAIy/8wWfAACGqYuzrv5/KASfAIDxx7mDAKBv1X6+aYScv9cHAgCMDx4H6IbfAQh08/TY3N8CMDrTGOPn5D3c18rfEJjzuoAAADoaxKmH79S/v6WzEAEgAKD0+Lc0cn/elqXPRwSAAIBS49/LqP16O5c6LxEAAgC6Hv/eR2zJGBABIACg6+Gsdp/8xj60w9cAmV1v33Wea7TuXh7Kv2ud8z72Fhv+BgACAMLGP2H4l7rPPnEAAcAffOc3692wM8D1AAEADbx7NHrznYdPAeBjfgkQigxdlbMx2OATACj17t/4L3dOogIEAHjn77wAAQDGzLmBAIDZtPydZx8X19Ty4+pvACAAwLtYnB/MwrcAgt08Pa4Ou713haHvOj3eIuPndQCfAAAAAgAAEAAAgAAAAAQAACAA4P989xm8DhAAAIAAYC6+Awxe/wgAAEAAAAACAAAQAACAAAAABAB8ju9A4/kPAgAAEADMxXeBweseAQAABLh2BCS7e3lwCB0652fnt/eDgwOfAABJ43/JPwcCAKDT8RcBIACA0PEXASAAKHphx3Okp+ec5z0CAGCBoXx7fTbCCADwnWCSxj/9nbjXOwIAiB7/5AgAAQBEj78IQAAAhI6/CEAAAISOvwhAAACED68IQACACy6hj/+Ut8nzHQEAGP+Gx9BQIwCI4LvBGNj6EeB1jgAADOsn+N8IIwAAwhh/BABA2Lt/448AADD+IAAAjD8IAIgaB4y/5zkCAMD4gwCgBt8Rxvh7fSMAAIw/CAAA4w8CAMD4gwAADL/xBwEADL/xBwEA9UYH4+95BgIA8x1xAAAAxs15AAIAjJtzAgEAs2n5O88+Lq6p5cdV3gBAAIB3sTg/mIVvAQQ7eXpch/eD3d67wtB3nR5vkfHzOoDPAACAAAAABAAAIAABAAAAAAgAAEAAAgAAAAAQAACAAAAABAAAIAABAAAAAAgAAEAAAgAAAAAEAAAgAAEAAAAACAAAQAACAAAAABAAAIAAAAAEAAAgAAEAAAAACAAAQAACAAAAABAAAIAAAAAEAAAIAABAAAIAAAAAEAAAgAAAAAQAACAAAQAAAAAIAABAAAIAAAAAEAAAgAAAAAQAACAAAQAAAAAIAABAAACAAAAABAAAIAABAAAAAAgAAEAAAgAAAAAQAACAAAAABAAAIAABAAAAAAgAAEAAAgAAAAAEAAAgAAEAAAAACAAAQAACAAAAABAAAIAAAAAEAAAgAAEAAAAACAAAQAACAAAAABAAAIAAAAAEAAAgAAEAAAIAAAAAEAAAgAAAAAQAACAAAQAAAAAIAABAAAIAAAAAEAAAgAAAAAQAACAAA4Hw/ANVAgtMw9j/6AAAAAElFTkSuQmCC'''


def replace_in(path: Path, replacements):
    text = path.read_text(encoding='utf-8')
    original = text
    for old, new in replacements:
        text = text.replace(old, new)
    if text != original:
        path.write_text(text, encoding='utf-8', newline='\n')


# Identidade visual neutra. Mantemos o nome interno da classe para não tocar
# desnecessariamente na lógica das telas e, especialmente, do sync.
(root / 'lib/brand.dart').write_text('''import 'package:flutter/material.dart';

class AuditarBrand {
  // Identidade visual neutra da edição SST Gestão.
  static const navy = Color(0xFF155E75);
  static const navyDark = Color(0xFF12343B);
  static const navySoft = Color(0xFFEAF4F4);
  static const green = Color(0xFF22A06B);
  static const greenDark = Color(0xFF18794E);
  static const greenSoft = Color(0xFFE9F7EF);
  static const background = Color(0xFFF7F8FA);
  static const surface = Colors.white;
  static const line = Color(0xFFE3E7EC);
  static const danger = Color(0xFFD93025);
  static const warning = Color(0xFFF29D18);
  static const info = Color(0xFF2563B8);
  static const neutral = Color(0xFF667085);

  static const iconAsset = 'assets/branding/sst_icon.png';
  static const transparentIconAsset = 'assets/branding/sst_icon_transparent.png';
  static const logoAsset = 'assets/branding/sst_logo.png';

  static const slogan = 'Segurança do Trabalho na prática';
  static const subtitle = 'GESTÃO DE SEGURANÇA E SAÚDE NO TRABALHO';
}
''', encoding='utf-8', newline='\n')

# Widget visual de marca refeito do zero para não carregar nenhum texto/logo Auditar.
(root / 'lib/widgets/auditar_brand_logo.dart').write_text('''import 'package:flutter/material.dart';

import '../brand.dart';

class AuditarBrandLogo extends StatelessWidget {
  final double iconSize;
  final bool showSubtitle;
  final Color? textColor;

  const AuditarBrandLogo({
    super.key,
    this.iconSize = 44,
    this.showSubtitle = true,
    this.textColor,
  });

  @override
  Widget build(BuildContext context) {
    final color = textColor ?? AuditarBrand.navyDark;
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Image.asset(
          AuditarBrand.iconAsset,
          width: iconSize,
          height: iconSize,
          fit: BoxFit.contain,
        ),
        const SizedBox(width: 10),
        Flexible(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'SST Gestão',
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: TextStyle(
                  color: color,
                  fontWeight: FontWeight.w900,
                  fontSize: iconSize * .40,
                  letterSpacing: -.3,
                ),
              ),
              if (showSubtitle)
                Text(
                  'Segurança do Trabalho',
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: TextStyle(
                    color: color.withValues(alpha: .72),
                    fontWeight: FontWeight.w600,
                    fontSize: iconSize * .20,
                  ),
                ),
            ],
          ),
        ),
      ],
    );
  }
}
''', encoding='utf-8', newline='\n')

# Substituições estritamente de identidade/apresentação.
replacements = [
    ('assets/branding/auditar_icon_transparent.png', 'assets/branding/sst_icon_transparent.png'),
    ('assets/branding/auditar_icon.png', 'assets/branding/sst_icon.png'),
    ('assets/branding/auditar_logo.jpg', 'assets/branding/sst_logo.png'),
    ('AUDITAR SST', 'SST GESTÃO'),
    ('Auditar SST', 'SST Gestão'),
    ('Central Auditar', 'Central SST'),
    ('Biblioteca Auditar', 'Biblioteca SST'),
    ('Padrão Auditar atual', 'Padrão SST'),
    ('Auditar Executivo', 'Executivo SST'),
    ('Auditar Fotográfico', 'Fotográfico SST'),
    ('Auditar Obra', 'Obra SST'),
    ('Auditar Técnico Clean', 'Técnico Clean'),
    ('Auditar NR-12', 'NR-12 SST'),
    ('Logo Auditar', 'Logo do sistema'),
    ('Azul Auditar', 'Azul petróleo'),
    ('Auditar + cliente', 'Sistema + cliente'),
    ('Somente Auditar', 'Somente sistema'),
    ('Relatorio_Executivo_Auditar_SST.pdf', 'Relatorio_Executivo_SST.pdf'),
    ('Relatorio_Completo_Auditar_SST.pdf', 'Relatorio_Completo_SST.pdf'),
    ('Auditar_SST_AutoBackup_', 'SST_Gestao_AutoBackup_'),
    ('Auditar_SST_Backup_Completo_', 'SST_Gestao_Backup_Completo_'),
    ('Backup completo Auditar SST', 'Backup completo SST Gestão'),
    ('Backup completo do aplicativo Auditar SST.', 'Backup completo do aplicativo SST Gestão.'),
    ('Este arquivo não é um backup completo válido do Auditar SST.', 'Este arquivo não é um backup completo válido do SST Gestão.'),
    ('Substituído pela Auditar', 'Substituído pelo responsável SST'),
    ("'Empresa', 'Auditar', 'Terceirizada', 'Não definido'", "'Empresa', 'Responsável SST', 'Terceirizada', 'Não definido'"),
    ('A assinatura é coletada dentro do Auditar e sai diretamente no PDF.', 'A assinatura é coletada no aplicativo e sai diretamente no PDF.'),
    ('A configuração já vem pronta nas versões distribuídas pela Auditar.', 'A configuração já vem pronta nesta versão do aplicativo.'),
    ('Indicador gerencial interno Auditar:', 'Indicador gerencial interno:'),
    ('a rota de foto mais madura do Auditar.', 'a rota de foto mais madura do sistema.'),
    ("text: 'Auditar '", "text: 'SST Gestão '"),
]

for path in list((root / 'lib').rglob('*.dart')) + [root / 'pubspec.yaml']:
    replace_in(path, replacements)

# Nome do pacote Flutter é neutro. Imports package: também acompanham o novo nome.
pub = root / 'pubspec.yaml'
text = pub.read_text(encoding='utf-8')
text = re.sub(r'^name:\s*[^\n]+', 'name: sst_gestao', text, count=1, flags=re.M)
text = re.sub(r'^version:\s*[^\n]+', 'version: 1.0.0+1', text, count=1, flags=re.M)
pub.write_text(text, encoding='utf-8', newline='\n')
for path in (root / 'lib').rglob('*.dart'):
    replace_in(path, [('package:auditar_sst/', 'package:sst_gestao/')])
for path in (root / 'test').rglob('*.dart') if (root / 'test').exists() else []:
    replace_in(path, [('package:auditar_sst/', 'package:sst_gestao/')])

# Isolamento local: a edição neutra pode coexistir com a versão Auditar no PC.
replace_in(root / 'lib/database.dart', [
    ('auditar_sst.db', 'sst_gestao.db'),
    ("auditar_sst_$safeUserId.db", "sst_gestao_$safeUserId.db"),
    ("auditar_sst_$_activeUserId.db", "sst_gestao_$_activeUserId.db"),
])
replace_in(root / 'lib/services/auth_service.dart', [
    ('auditar_sst_auth.json', 'sst_gestao_auth.json'),
    ('auditar_offline_login_v1', 'sst_gestao_offline_login_v1'),
    ('auditar_offline_salt_v1', 'sst_gestao_offline_salt_v1'),
    ('auditar_offline_verifier_v1', 'sst_gestao_offline_verifier_v1'),
    ('auditar_offline_user_v1', 'sst_gestao_offline_user_v1'),
])
replace_in(root / 'lib/services/auth_secure_store.dart', [
    ('auditar_sst_session_token_v1', 'sst_gestao_session_token_v1'),
])
replace_in(root / 'lib/services/backup_service.dart', [
    ('auditar_sst_backup_', 'sst_gestao_backup_'),
    ('auditar_sst.db', 'sst_gestao.db'),
    ('database/auditar_sst.db', 'database/sst_gestao.db'),
    ('auditar_sst_restore_', 'sst_gestao_restore_'),
])
replace_in(root / 'lib/services/background_sync_service.dart', [
    ('auditar.background.sync', 'sst.gestao.background.sync'),
])

# Ícone/logo neutros. Os arquivos originais da Auditar são removidos para não
# serem empacotados nem mesmo como ativos não utilizados.
branding = root / 'assets/branding'
branding.mkdir(parents=True, exist_ok=True)
for old in ['auditar_icon.png', 'auditar_icon_transparent.png', 'auditar_logo.jpg']:
    p = branding / old
    if p.exists():
        p.unlink()
icon = base64.b64decode(ICON_B64)
for name in ['sst_icon.png', 'sst_icon_transparent.png', 'sst_logo.png']:
    (branding / name).write_bytes(icon)

# Segurança: nenhum texto de apresentação conhecido pode continuar com marca Auditar.
visible_patterns = [
    r"['\"][^'\"\n]*Auditar SST[^'\"\n]*['\"]",
    r"['\"][^'\"\n]*AUDITAR SST[^'\"\n]*['\"]",
    r"['\"][^'\"\n]*Central Auditar[^'\"\n]*['\"]",
    r"['\"][^'\"\n]*Logo Auditar[^'\"\n]*['\"]",
    r"['\"][^'\"\n]*pela Auditar[^'\"\n]*['\"]",
]
issues=[]
for path in (root / 'lib').rglob('*.dart'):
    data=path.read_text(encoding='utf-8')
    for pattern in visible_patterns:
        if re.search(pattern, data):
            issues.append(f'{path.relative_to(root)} => {pattern}')
if issues:
    raise SystemExit('Identidade Auditar ainda visível: ' + '; '.join(issues))

print('NEUTRAL_SST_V1_OK: identidade visual neutralizada, ativos Auditar removidos e armazenamento local isolado; núcleo funcional preservado.')
