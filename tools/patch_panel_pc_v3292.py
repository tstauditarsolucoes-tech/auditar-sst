#!/usr/bin/env python3
from __future__ import annotations
import sys
from pathlib import Path

CSS_MARKER = '/* v3.29.2 painel gerencial desktop e contraste */'
CSS_PATCH = r'''
    /* v3.29.2 painel gerencial desktop e contraste */
    :root{--surface-raised:#ffffff;--shadow-soft:0 8px 24px rgba(15,30,74,.07);--shadow-card:0 3px 12px rgba(15,30,74,.06)}
    button,.tab-button,.text-button,.print-button,.count-chip,.status-chip,.period-chip,.issue-chip{-webkit-text-fill-color:currentColor!important;text-shadow:none!important;opacity:1!important}
    .tab-button{color:#536079!important;border:1px solid transparent}.tab-button:hover{color:var(--navy)!important;background:#f2f5fb}.tab-button[aria-selected="true"]{color:var(--navy)!important;background:#eef3ff;border-color:#dce5f6;box-shadow:0 1px 2px rgba(15,30,74,.05)}
    .text-button{color:var(--navy)!important}.count-chip{color:var(--navy)!important;background:#edf2ff}.period-chip{color:var(--navy)!important;background:#edf2ff}.status-green{color:#08752b!important}.status-yellow{color:#9b5b00!important}.status-red{color:#b42318!important}.status-purple{color:#5f3fb3!important}
    .section-title{letter-spacing:-.01em}.section-note{line-height:1.45}.metric-card,.panel,.table-panel,.trend-panel,.priority-item,.sector-item{box-shadow:var(--shadow-card)}
    .metric-card{position:relative;overflow:hidden;border-top:3px solid #d9e2f4}.metric-card.tone-green{border-top-color:var(--green)}.metric-card.tone-yellow{border-top-color:#e89a16}.metric-card.tone-red{border-top-color:var(--red)}.metric-card.tone-purple{border-top-color:var(--purple)}
    .executive-reading{border-left:4px solid var(--navy);background:linear-gradient(90deg,#f8faff 0,#fff 34%);box-shadow:var(--shadow-card)}
    .issue-chip{background:#fff;color:#344054;border-color:#dfe4ec;box-shadow:0 1px 2px rgba(15,30,74,.04)}.issue-chip.critical{color:#b42318!important;background:#fff3f2;border-color:#f4c7c3}
    .table-panel{background:#fff}.table-scroll{scrollbar-color:#bcc6d8 transparent}th{color:#465269;background:#f7f9fc;font-weight:850;position:sticky;top:0;z-index:1}tbody tr:hover td{background:#f8fafc}td{color:#273142}
    .overall-badge{box-shadow:0 10px 24px rgba(2,10,38,.18)}.overall-value{letter-spacing:-.02em}.overall-detail{font-weight:700}
    .executive-module{transition:transform .15s ease,box-shadow .15s ease}.executive-module:hover{transform:translateY(-1px);box-shadow:var(--shadow-soft)}
    .sector-rank-row{padding:12px 4px}.rank-number{background:#eef3ff}.activity-item{padding:12px 2px}
    @media(min-width:960px){
      .page-width{width:min(1280px,calc(100% - 48px))}.topbar{padding:18px 0 24px}.brand-row{margin-bottom:18px}.company-row{align-items:stretch}.overall-badge{min-width:290px;padding:16px 18px;display:flex;flex-direction:column;justify-content:center}.overall-value{font-size:27px}.overall-label{font-size:10px}.overall-detail{font-size:12px}
      .tabs{gap:6px;padding:9px 0}.tab-button{min-height:44px;padding:0 16px;font-size:12.5px}main{padding:22px 0 44px}.section-title{font-size:19px}.section-head.spaced{margin-top:30px}.metric-grid{gap:12px}.metric-card{min-height:112px;padding:16px}.metric-label{font-size:11.5px}.metric-value{font-size:30px}.metric-context{font-size:11px;line-height:1.35}.panel{padding:17px}.trend-panel{padding:18px}.table-panel{border-radius:18px}.executive-modules{gap:14px}.executive-module{min-height:220px}
    }
'''


def fail(message: str) -> None:
    raise RuntimeError(message)


def main() -> int:
    if len(sys.argv) != 2:
        print('uso: patch_panel_pc_v3292.py <raiz-do-app>', file=sys.stderr)
        return 2
    root = Path(sys.argv[1]).resolve()
    main_dart = root / 'lib/main.dart'
    nc = root / 'lib/screens/non_conformities_screen.dart'
    index = root / 'painel_web_google_apps_script/Index.html'
    pubspec = root / 'pubspec.yaml'
    home = root / 'lib/screens/home_screen.dart'
    for p in (main_dart, nc, index, pubspec, home):
        if not p.exists():
            fail(f'arquivo ausente: {p}')

    text = main_dart.read_text(encoding='utf-8')
    old = "labelStyle: TextStyle(fontWeight: FontWeight.w700),"
    new = "labelStyle: TextStyle(\n            color: AuditarBrand.navy,\n            fontWeight: FontWeight.w700,\n          ),"
    if new not in text:
        if old not in text:
            fail('chipTheme esperado não encontrado em main.dart')
        text = text.replace(old, new, 1)
    main_dart.write_text(text, encoding='utf-8')

    text = nc.read_text(encoding='utf-8')
    anchor = "                  return ChoiceChip(\n                    selected: selected,\n                    label: Text('${_shortStatus(status)} $count'),"
    replacement = "                  return ChoiceChip(\n                    selected: selected,\n                    backgroundColor: Colors.white,\n                    selectedColor: AuditarBrand.greenSoft,\n                    checkmarkColor: AuditarBrand.greenDark,\n                    side: const BorderSide(color: AuditarBrand.line),\n                    labelStyle: TextStyle(\n                      color: selected\n                          ? AuditarBrand.greenDark\n                          : AuditarBrand.navy,\n                      fontWeight: FontWeight.w800,\n                    ),\n                    label: Text('${_shortStatus(status)} $count'),"
    if replacement not in text:
        if anchor not in text:
            fail('ChoiceChip de NC não encontrado')
        text = text.replace(anchor, replacement, 1)
    nc.write_text(text, encoding='utf-8')

    html = index.read_text(encoding='utf-8')
    if CSS_MARKER not in html:
        if '</style>' not in html:
            fail('fechamento </style> não encontrado em Index.html')
        html = html.replace('</style>', CSS_PATCH + '\n  </style>', 1)
    index.write_text(html, encoding='utf-8')

    pub = pubspec.read_text(encoding='utf-8')
    if 'version: 3.29.2+144' not in pub:
        if 'version: 3.29.1+143' in pub:
            pub = pub.replace('version: 3.29.1+143', 'version: 3.29.2+144', 1)
        elif 'version: 3.29.0+142' in pub:
            pub = pub.replace('version: 3.29.0+142', 'version: 3.29.2+144', 1)
        else:
            fail('versão base não encontrada no pubspec')
        pubspec.write_text(pub, encoding='utf-8')

    home_text = home.read_text(encoding='utf-8')
    home_text = home_text.replace('versão 3.29.1', 'versão 3.29.2').replace('versão 3.29.0', 'versão 3.29.2')
    home.write_text(home_text, encoding='utf-8')

    checks = {
        main_dart: 'color: AuditarBrand.navy',
        nc: 'selectedColor: AuditarBrand.greenSoft',
        index: CSS_MARKER,
        pubspec: 'version: 3.29.2+144',
    }
    for p, marker in checks.items():
        if marker not in p.read_text(encoding='utf-8'):
            fail(f'validação v3.29.2 falhou em {p.name}: {marker}')

    print('v3.29.2: painel gerencial refinado e contraste dos chips do PC corrigido')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
