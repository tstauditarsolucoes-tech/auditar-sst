#!/usr/bin/env python3
from __future__ import annotations
import re
import sys
from pathlib import Path


def fail(message: str) -> None:
    raise RuntimeError(message)


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    if old not in text:
        fail(f'marcador não encontrado: {label}')
    return text.replace(old, new, 1)


def main() -> int:
    if len(sys.argv) != 2:
        print('uso: patch_contrast_all_v3293.py <raiz-do-app>', file=sys.stderr)
        return 2

    root = Path(sys.argv[1]).resolve()
    main_dart = root / 'lib/main.dart'
    action_plan = root / 'lib/screens/action_plan_screen.dart'
    non_conformities = root / 'lib/screens/non_conformities_screen.dart'
    trainings = root / 'lib/screens/trainings_screen.dart'
    safety = root / 'lib/screens/safety_observations_screen.dart'
    pubspec = root / 'pubspec.yaml'
    home = root / 'lib/screens/home_screen.dart'

    for p in (main_dart, action_plan, non_conformities, trainings, safety, pubspec, home):
        if not p.exists():
            fail(f'arquivo ausente: {p}')

    text = main_dart.read_text(encoding='utf-8')
    old_label = 'labelStyle: TextStyle(fontWeight: FontWeight.w700),'
    new_label = """labelStyle: TextStyle(
            color: AuditarBrand.navy,
            fontWeight: FontWeight.w800,
          ),
          checkmarkColor: AuditarBrand.greenDark,"""
    if 'checkmarkColor: AuditarBrand.greenDark' not in text:
        if old_label in text:
            text = text.replace(old_label, new_label, 1)
        else:
            existing = """labelStyle: TextStyle(
            color: AuditarBrand.navy,
            fontWeight: FontWeight.w700,
          ),"""
            if existing not in text:
                fail('chipTheme global não encontrado')
            text = text.replace(
                existing,
                """labelStyle: TextStyle(
            color: AuditarBrand.navy,
            fontWeight: FontWeight.w800,
          ),
          checkmarkColor: AuditarBrand.greenDark,""",
                1,
            )
    main_dart.write_text(text, encoding='utf-8')

    text = action_plan.read_text(encoding='utf-8')
    old = """                  return ChoiceChip(
                    selected: selectedFilter == filter,
                    label: Text('$filter ${_count(filter)}'),
                    onSelected: (_) => setState(() => selectedFilter = filter),
                  );"""
    new = """                  return ChoiceChip(
                    selected: selectedFilter == filter,
                    backgroundColor: Colors.white,
                    selectedColor: AuditarBrand.greenSoft,
                    checkmarkColor: AuditarBrand.greenDark,
                    side: const BorderSide(color: AuditarBrand.line),
                    labelStyle: const TextStyle(
                      color: AuditarBrand.navy,
                      fontWeight: FontWeight.w800,
                    ),
                    label: Text('$filter ${_count(filter)}'),
                    onSelected: (_) => setState(() => selectedFilter = filter),
                  );"""
    text = replace_once(text, old, new, 'filtros do plano de ação')
    action_plan.write_text(text, encoding='utf-8')

    text = non_conformities.read_text(encoding='utf-8')
    if 'selectedColor: AuditarBrand.greenSoft' not in text:
        old = """                  return ChoiceChip(
                    selected: selected,
                    label: Text('${_shortStatus(status)} $count'),"""
        new = """                  return ChoiceChip(
                    selected: selected,
                    backgroundColor: Colors.white,
                    selectedColor: AuditarBrand.greenSoft,
                    checkmarkColor: AuditarBrand.greenDark,
                    side: const BorderSide(color: AuditarBrand.line),
                    labelStyle: TextStyle(
                      color: selected
                          ? AuditarBrand.greenDark
                          : AuditarBrand.navy,
                      fontWeight: FontWeight.w800,
                    ),
                    label: Text('${_shortStatus(status)} $count'),"""
        text = replace_once(text, old, new, 'filtros de não conformidades')
    non_conformities.write_text(text, encoding='utf-8')

    text = trainings.read_text(encoding='utf-8')
    text = text.replace(
        'color: selected ? Colors.white : AuditarBrand.navyDark,',
        'color: selected ? AuditarBrand.greenDark : AuditarBrand.navyDark,',
        1,
    )
    text = text.replace(
        'selectedColor: AuditarBrand.greenDark,\n                      backgroundColor: Colors.white,',
        'selectedColor: AuditarBrand.greenSoft,\n                      checkmarkColor: AuditarBrand.greenDark,\n                      backgroundColor: Colors.white,',
        1,
    )
    trainings.write_text(text, encoding='utf-8')

    text = safety.read_text(encoding='utf-8')
    text = text.replace(
        'selected ? Colors.white : AuditarBrand.navyDark,',
        'selected ? AuditarBrand.greenDark : AuditarBrand.navyDark,',
        1,
    )
    text = text.replace(
        'selectedColor: AuditarBrand.greenDark,\n                        backgroundColor: Colors.white,',
        'selectedColor: AuditarBrand.greenSoft,\n                        checkmarkColor: AuditarBrand.greenDark,\n                        backgroundColor: Colors.white,',
        1,
    )
    safety.write_text(text, encoding='utf-8')

    pub = pubspec.read_text(encoding='utf-8')
    if 'version: 3.29.3+145' not in pub:
        pub2 = re.sub(
            r'^version:\s*3\.29\.[0-2]\+\d+\s*$',
            'version: 3.29.3+145',
            pub,
            count=1,
            flags=re.M,
        )
        if pub2 == pub:
            fail('versão 3.29.x base não encontrada no pubspec')
        pubspec.write_text(pub2, encoding='utf-8')

    home_text = home.read_text(encoding='utf-8')
    home_text = re.sub(r'versão 3\.29\.[0-2]', 'versão 3.29.3', home_text)
    home.write_text(home_text, encoding='utf-8')

    problematic = []
    for p in root.glob('lib/screens/*.dart'):
        src = p.read_text(encoding='utf-8')
        for match in re.finditer(r'ChoiceChip\s*\(', src):
            block = src[match.start():match.start() + 1100]
            if 'selected ? Colors.white' in block:
                problematic.append(p.name)
    if problematic:
        fail('ChoiceChip ainda com texto branco selecionado: ' + ', '.join(sorted(set(problematic))))

    checks = {
        main_dart: 'checkmarkColor: AuditarBrand.greenDark',
        action_plan: 'selectedColor: AuditarBrand.greenSoft',
        non_conformities: 'selectedColor: AuditarBrand.greenSoft',
        trainings: 'selected ? AuditarBrand.greenDark : AuditarBrand.navyDark',
        safety: 'selected ? AuditarBrand.greenDark : AuditarBrand.navyDark',
        pubspec: 'version: 3.29.3+145',
    }
    for p, marker in checks.items():
        if marker not in p.read_text(encoding='utf-8'):
            fail(f'validação v3.29.3 falhou em {p.name}: {marker}')

    note = root / 'MUDANCAS_V3_29_3_CONTRASTE_GERAL.txt'
    note.write_text(
        'Auditar SST v3.29.3 — contraste geral Android e Windows\n\n'
        '- Corrige textos/nome de filtros que podiam ficar brancos em fundo claro.\n'
        '- Padroniza ChoiceChip/Chip com texto escuro e seleção clara.\n'
        '- Corrige Plano de Ação, Não Conformidades, Treinamentos e Observações.\n'
        '- Mantém assinatura em tela cheia no Android.\n'
        '- Mantém Gov.br, emissão sem assinatura e plano de ação opcional.\n'
        '- Não remove módulos nem altera banco de dados ou sincronização.\n',
        encoding='utf-8',
    )

    print('v3.29.3: contraste geral de filtros/chips corrigido no Android e Windows')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
