#!/usr/bin/env python3
"""Static inventory of screen destinations; never delete or modify app modules.

This counts Dart screen constructors, NOT user journeys. A shared destination
is commonly a legitimate shortcut and never proof of duplicated functionality.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
import json
from pathlib import Path
import re

CLASS = re.compile(r"\bclass\s+([A-Z][A-Za-z0-9_]*(?:Screen|Page|Hub))\s+extends\b")
TARGET = re.compile(r"\b([A-Z][A-Za-z0-9_]*(?:Screen|Page|Hub))\s*\(")


def scan(root: Path) -> dict:
    root = root.resolve()
    folder = root / "lib" / "screens"
    if not folder.is_dir():
        raise ValueError("Missing assembled Flutter lib/screens")
    sources = {
        p: p.read_text(encoding="utf-8") for p in sorted(folder.glob("*.dart"))
    }
    definitions: dict[str, list[str]] = defaultdict(list)
    own_classes: dict[Path, set[str]] = {}
    for path, source in sources.items():
        names = set(CLASS.findall(source))
        own_classes[path] = names
        for name in names:
            definitions[name].append(path.relative_to(root).as_posix())
    references: dict[str, list[dict]] = defaultdict(list)
    for path, source in sources.items():
        origin = path.relative_to(root).as_posix()
        for hit in TARGET.finditer(source):
            target = hit.group(1)
            # A class declaration/own constructor is not an outbound route.
            if target not in definitions or target in own_classes[path]:
                continue
            references[target].append({
                "from": origin,
                "line": source.count("\n", 0, hit.start()) + 1,
            })
    shared = []
    within = []
    for target, occurrences in references.items():
        by_source: dict[str, list[int]] = defaultdict(list)
        for item in occurrences:
            by_source[item["from"]].append(item["line"])
        destinations = sorted(by_source)
        if len(destinations) >= 2:
            shared.append({
                "destination": target,
                "defined_in": sorted(definitions[target]),
                "referenced_by": destinations,
                "file_count": len(destinations),
                "occurrences": len(occurrences),
            })
        for origin, lines in by_source.items():
            if len(lines) >= 2:
                within.append({
                    "destination": target,
                    "source": origin,
                    "lines": sorted(lines),
                    "constructor_count": len(lines),
                })
    shared.sort(key=lambda x: (-x["file_count"], x["destination"]))
    within.sort(key=lambda x: (-x["constructor_count"], x["source"], x["destination"]))
    ambiguous = [
        {"class": k, "definitions": sorted(v)}
        for k, v in sorted(definitions.items())
        if len(v) > 1
    ]
    return {
        "scope": "Assembled Flutter screen sources (static constructor heuristic)",
        "warning": "A reference does not prove a reachable button. Multiple references do not prove duplicate business functions. Never delete automatically.",
        "screen_files_scanned": len(sources),
        "screen_classes_defined": len(definitions),
        "ambiguous_class_definitions": ambiguous,
        "targets_referenced_from_multiple_screens": shared,
        "targets_repeated_within_one_screen": within,
    }


def markdown(result: dict) -> str:
    out = [
        "# Referências repetidas de telas — Auditar SST",
        "",
        "**Análise estática do aplicativo montado.** Aponta caminhos para revisão; não prova que uma função é inútil.",
        "Atalhos para a mesma tela são esperados na Home, em Visita Rápida e na área de obras.",
        "",
        f"- Arquivos de telas: **{result['screen_files_scanned']}**",
        f"- Classes de tela: **{result['screen_classes_defined']}**",
        f"- Destinos referenciados por várias telas: **{len(result['targets_referenced_from_multiple_screens'])}**",
        f"- Destinos com várias referências no mesmo arquivo: **{len(result['targets_repeated_within_one_screen'])}**",
        f"- Definições de classe ambíguas: **{len(result['ambiguous_class_definitions'])}**",
        "",
        "## Destinos compartilhados entre telas",
        "",
    ]
    for item in result["targets_referenced_from_multiple_screens"][:60]:
        sources = ", ".join("`" + x + "`" for x in item["referenced_by"])
        out.append(f"- **{item['destination']}** ({item['file_count']} telas): {sources}")
    if not result["targets_referenced_from_multiple_screens"]:
        out.append("Nenhum destino compartilhado identificado.")
    out += ["", "## Várias referências ao mesmo destino dentro de uma tela", ""]
    for item in result["targets_repeated_within_one_screen"][:80]:
        out.append(f"- `{item['source']}` → **{item['destination']}** ({item['constructor_count']} referências, linhas {', '.join(map(str,item['lines'][:15]))})")
    if not result["targets_repeated_within_one_screen"]:
        out.append("Nenhuma candidata encontrada.")
    out += ["", "## Classes definidas em mais de um arquivo", ""]
    for item in result["ambiguous_class_definitions"]:
        out.append(f"- **{item['class']}**: {', '.join(item['definitions'])}")
    if not result["ambiguous_class_definitions"]:
        out.append("Nenhuma.")
    out += [
        "", "## Próximo passo de auditoria manual", "",
        "1. Conferir se a referência cria um botão, é código auxiliar ou rota programática.",
        "2. Comparar fluxo, salvamento, dados e permissões antes de chamar qualquer função de duplicada.",
        "3. Verificar Android e Windows em instalações reais. Só propor exclusão depois de validar ausência de dependências e receber autorização.",
    ]
    return "\n".join(out) + "\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("app_dir", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    report = scan(args.app_dir)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "DESTINOS_REPETIDOS.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (args.output_dir / "DESTINOS_REPETIDOS.md").write_text(
        markdown(report), encoding="utf-8"
    )
    print("AUDITAR_SHARED_SCREEN_DESTINATIONS_OK",
          "files", report["screen_files_scanned"],
          "shared", len(report["targets_referenced_from_multiple_screens"]),
          "same_file", len(report["targets_repeated_within_one_screen"]),
          "class_collisions", len(report["ambiguous_class_definitions"]))


if __name__ == "__main__":
    main()
