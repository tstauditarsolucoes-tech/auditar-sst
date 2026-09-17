#!/usr/bin/env python3
from pathlib import Path
import binascii
import math
import re
import struct
import sys
import zlib

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'app/Auditar_SST_v1_5_dashboard')

PROTECTED_CORE = {
    'lib/services/device_sync_service.dart',
    'lib/services/media_sync_service.dart',
    'lib/services/apps_script_http.dart',
    'lib/services/sync_coordinator.dart',
    'lib/services/drive_service.dart',
}


def replace_in(path: Path, replacements):
    rel = str(path.relative_to(root)).replace('\\', '/') if path.is_relative_to(root) else ''
    if rel in PROTECTED_CORE:
        return
    text = path.read_text(encoding='utf-8')
    original = text
    for old, new in replacements:
        text = text.replace(old, new)
    if text != original:
        path.write_text(text, encoding='utf-8', newline='\n')


def png_chunk(kind: bytes, data: bytes) -> bytes:
    return struct.pack('>I', len(data)) + kind + data + struct.pack(
        '>I', binascii.crc32(kind + data) & 0xFFFFFFFF
    )


def point_segment_distance(px, py, x1, y1, x2, y2):
    dx = x2 - x1
    dy = y2 - y1
    denom = dx * dx + dy * dy
    if denom == 0:
        return math.hypot(px - x1, py - y1)
    t = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / denom))
    qx = x1 + t * dx
    qy = y1 + t * dy
    return math.hypot(px - qx, py - qy)


def write_neutral_png(path: Path, size=512):
    # Ícone original e neutro: fundo petróleo, escudo branco e check verde.
    bg = (18, 52, 59, 255)
    white = (255, 255, 255, 255)
    teal = (34, 160, 107, 255)
    yellow = (245, 183, 49, 255)
    cx = size / 2
    rows = []
    for y in range(size):
        row = bytearray([0])
        for x in range(size):
            color = bg
            # Escudo estilizado: topo arredondado e ponta inferior.
            nx = abs(x - cx)
            shield_top = 112 <= y <= 300 and nx <= 144
            shield_lower = 300 < y <= 424 and nx <= (144 - (y - 300) * 0.88)
            top_round = ((x - cx) / 150) ** 2 + ((y - 146) / 88) ** 2 <= 1 and y <= 190
            if shield_top or shield_lower or top_round:
                color = white
            # Faixa de capacete de segurança na parte superior do escudo.
            if 165 <= y <= 195 and abs(x - cx) <= 105:
                color = yellow
            if 145 <= y < 165 and ((x - cx) / 88) ** 2 + ((y - 165) / 42) ** 2 <= 1:
                color = yellow
            # Check central.
            if point_segment_distance(x, y, 190, 282, 238, 330) <= 17:
                color = teal
            if point_segment_distance(x, y, 238, 330, 333, 235) <= 17:
                color = teal
            row.extend(color)
        rows.append(bytes(row))
    raw = b''.join(rows)
    png = b'\x89PNG\r\n\x1a\n'
    png += png_chunk(b'IHDR', struct.pack('>IIBBBBB', size, size, 8, 6, 0, 0, 0))
    png += png_chunk(b'IDAT', zlib.compress(raw, 9))
    png += png_chunk(b'IEND', b'')
    path.write_bytes(png)


# Identidade visual neutra. Mantemos nomes internos de classes para reduzir risco.
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

# Nome interno do pacote Flutter separado.
pub = root / 'pubspec.yaml'
text = pub.read_text(encoding='utf-8')
text = re.sub(r'^name:\s*[^\n]+', 'name: sst_gestao', text, count=1, flags=re.M)
text = re.sub(r'^version:\s*[^\n]+', 'version: 1.0.0+1', text, count=1, flags=re.M)
pub.write_text(text, encoding='utf-8', newline='\n')
for base in [root / 'lib', root / 'test']:
    if base.exists():
        for path in base.rglob('*.dart'):
            replace_in(path, [('package:auditar_sst/', 'package:sst_gestao/')])

# Armazenamento e credenciais locais isolados da edição Auditar.
replace_in(root / 'lib/database.dart', [
    ('auditar_sst_$safeUserId.db', 'sst_gestao_$safeUserId.db'),
    ('auditar_sst_$_activeUserId.db', 'sst_gestao_$_activeUserId.db'),
    ('auditar_sst.db', 'sst_gestao.db'),
    ("'app_name': 'Auditar SST'", "'app_name': 'SST Gestão'"),
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
    ('database/auditar_sst.db', 'database/sst_gestao.db'),
    ('auditar_sst.db', 'sst_gestao.db'),
    ('auditar_sst_restore_', 'sst_gestao_restore_'),
])
replace_in(root / 'lib/services/background_sync_service.dart', [
    ('auditar.background.sync', 'sst.gestao.background.sync'),
])

# Remove todos os ativos originais da marca Auditar e cria ativos neutros.
branding = root / 'assets/branding'
branding.mkdir(parents=True, exist_ok=True)
for old in ['auditar_icon.png', 'auditar_icon_transparent.png', 'auditar_logo.jpg']:
    p = branding / old
    if p.exists():
        p.unlink()
for name in ['sst_icon.png', 'sst_icon_transparent.png', 'sst_logo.png']:
    write_neutral_png(branding / name)

# Verificação de identidade visível. Nomes internos de classes podem continuar.
visible_forbidden = [
    'Auditar SST',
    'AUDITAR SST',
    'Central Auditar',
    'Padrão Auditar',
    'Auditar Executivo',
    'Auditar Fotográfico',
    'Auditar Obra',
    'Auditar Técnico Clean',
    'Auditar NR-12',
    'Logo Auditar',
    'Auditar + cliente',
    'Somente Auditar',
    'Substituído pela Auditar',
]
issues = []
for path in (root / 'lib').rglob('*.dart'):
    rel = str(path.relative_to(root)).replace('\\', '/')
    if rel in PROTECTED_CORE:
        continue
    data = path.read_text(encoding='utf-8')
    for phrase in visible_forbidden:
        if phrase in data:
            issues.append(f'{rel}: {phrase}')
if issues:
    raise SystemExit('Identidade Auditar ainda visível: ' + '; '.join(issues))

print('NEUTRAL_SST_V1_OK: identidade Auditar removida da apresentação; ativos neutros gerados; armazenamento local isolado; núcleo de sync intocado.')
