#!/usr/bin/env python3
"""Inventory the *assembled* Auditar SST Flutter app, without editing app sources.

A screen candidate without a static import chain is NOT proof of an unused feature.
Repeated menu labels are likewise only review candidates.
"""
from __future__ import annotations
import argparse
from collections import defaultdict, deque
from datetime import datetime, timezone
import json
from pathlib import Path
import re

IMPORT = re.compile(r"""(?m)^\s*(?:import|export|part)\s+['"]([^'"]+\.dart)['"]""")
CLASS = re.compile(r"\bclass\s+(\w+(?:Screen|Page|Dialog|Hub))\s+extends\s+")
LABEL = re.compile(
    r"""(?:label|title|tooltip)\s*:\s*(?:const\s+)?Text\s*\(\s*(['"])([^'"\n]{3,90})\1"""
)
LITERAL = re.compile(r"\b(?:Screen|Page|Dialog|Hub)\b")
GSACTIONS = ("offline_knowledge_sync_v1", "worksite_followup_sync_v1",
             "client_treatment_v2", "company_group_sync_v1")


def relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def imports_of(path: Path, root: Path, text: str):
    for match in IMPORT.finditer(text):
        uri = match.group(1)
        if uri.startswith("dart:"):
            continue
        if uri.startswith("package:"):
            prefix = "package:auditar_sst/"
            if not uri.startswith(prefix):
                continue
            target = root / "lib" / uri[len(prefix):]
        else:
            target = path.parent / uri
        try:
            absolute = target.resolve()
            absolute.relative_to((root / "lib").resolve())
        except ValueError:
            continue
        yield uri, absolute


def scan(root: Path) -> dict:
    root = root.resolve()
    lib = root / "lib"
    if not (lib / "main.dart").is_file():
        raise ValueError("Missing assembled lib/main.dart")
    darts = sorted(path for path in lib.rglob("*.dart") if path.is_file())
    content = {p.resolve(): p.read_text(encoding="utf-8") for p in darts}
    imports = defaultdict(list)
    missing = []
    for path, source in content.items():
        for uri, dest in imports_of(path, root, source):
            if dest in content:
                imports[path].append(dest)
            elif not dest.exists():
                missing.append({"file": relative(path, root), "import": uri})
    entries = [path for path in content if path.parent == lib and
               (path.name == "main.dart" or path.name.startswith("main_"))]
    reachable = set(entries)
    waiting = deque(entries)
    while waiting:
        path = waiting.popleft()
        for imported in imports[path]:
            if imported not in reachable:
                reachable.add(imported)
                waiting.append(imported)

    screens = []
    for path, source in content.items():
        if "/screens/" not in path.as_posix():
            continue
        found = CLASS.findall(source)
        if not found and not path.name.endswith("_screen.dart"):
            continue
        screens.append({
            "file": relative(path, root),
            "classes": found,
            "statically_reachable": path in reachable,
            "imported_by": sorted(relative(src, root) for src, dependencies
                                  in imports.items() if path in dependencies),
        })

    by_label = defaultdict(list)
    for path, source in content.items():
        if "/screens/" not in path.as_posix():
            continue
        for match in LABEL.finditer(source):
            label = match.group(2).strip()
            line_no = source.count("\n", 0, match.start()) + 1
            by_label[label.casefold()].append({
                "label": label, "file": relative(path, root), "line": line_no
            })
    repeated = []
    for key, positions in by_label.items():
        files = {pos["file"] for pos in positions}
        if len(files) > 1:
            repeated.append({"label": positions[0]["label"],
                             "screen_count": len(files),
                             "occurrences": sorted(positions,
                               key=lambda v: (v["file"], v["line"]))})
    repeated.sort(key=lambda item: (-item["screen_count"], item["label"].casefold()))

    portal = root / "painel_web_google_apps_script" / "Code.gs"
    backend = portal.read_text(encoding="utf-8") if portal.is_file() else ""
    all_client = "\n".join(content.values())
    gs = [{
        "route": key, "mentioned_in_assembled_app": key in all_client,
        "mentioned_in_candidate_Code_gs": key in backend,
        "production_deployment_verified": False,
    } for key in GSACTIONS]
    unused = [x for x in screens if not x["statically_reachable"]]
    return {
        "generation_time_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "Compiled Flutter source assembled by this CI run",
        "disclaimer": ("Static evidence only. Not-statically-reachable is NOT "
                       "proof that a screen is unused or safe to remove. "
                       "Matching labels do not prove functional duplication."),
        "dart_file_count": len(darts),
        "screen_file_count": len(screens),
        "statically_reachable_screen_count": len(screens) - len(unused),
        "potentially_unreachable_screens": unused,
        "all_screen_files": screens,
        "repeated_navigation_labels": repeated,
        "missing_local_imports": missing,
        "backend_route_candidates": gs,
    }


def markdown(report: dict) -> str:
    lines = [
        "# Inventário automatizado de navegação — Auditar SST",
        "",
        "**Escopo:** código Flutter montado neste build, não apenas arquivos históricos "
        "do GitHub. Nenhum dado ou tela foi alterado pela auditoria.",
        "",
        "**Atenção:** resultados são candidatos para revisão, nunca autorização para "
        "excluir funcionalidades.",
        "",
        "## Resumo",
        "",
        f"- Arquivos Dart: **{report['dart_file_count']}**",
        f"- Arquivos de telas: **{report['screen_file_count']}**",
        f"- Telas com cadeia estática a partir dos entrypoints: "
        f"**{report['statically_reachable_screen_count']}**",
        f"- Telas sem cadeia estática detectada: "
        f"**{len(report['potentially_unreachable_screens'])}**",
        f"- Rótulos em mais de um arquivo: "
        f"**{len(report['repeated_navigation_labels'])}**",
        f"- Imports locais ausentes: **{len(report['missing_local_imports'])}**",
        "",
        "## Candidatas a revisão de acesso (não remover automaticamente)",
        ""
    ]
    for entry in report["potentially_unreachable_screens"]:
        lines.append(f"- \x60{entry['file']}\x60 — "
                     f"{', '.join(entry['classes']) or 'sem classe Screen detectada'}")
    if not report["potentially_unreachable_screens"]:
        lines.append("Nenhuma candidata estática detectada.")
    lines += ["", "## Rótulos repetidos entre telas", ""]
    for value in report["repeated_navigation_labels"][:60]:
        positions = ", ".join(f"\x60{x['file']}:{x['line']}\x60"
                              for x in value["occurrences"][:8])
        lines.append(f"- **{value['label']}** ({value['screen_count']} arquivos): {positions}")
    if not report["repeated_navigation_labels"]:
        lines.append("Nenhum rótulo literal repetido entre arquivos.")
    lines += ["", "## Rotas de integração presentes no pacote", ""]
    for candidate in report["backend_route_candidates"]:
        lines.append(f"- \x60{candidate['route']}\x60: "
                     f"app={'sim' if candidate['mentioned_in_assembled_app'] else 'não'}; "
                     f"GS candidato={'sim' if candidate['mentioned_in_candidate_Code_gs'] else 'não'}; "
                     "GS em produção **não verificado**")
    lines += ["", "## Imports locais ausentes", ""]
    for value in report["missing_local_imports"]:
        lines.append(f"- \x60{value['file']}\x60 → \x60{value['import']}\x60")
    if not report["missing_local_imports"]:
        lines.append("Nenhum.")
    lines += ["", "## Critério para tratar uma função como inútil", "",
        "A função só pode ser classificada como dispensável após confirmação "
        "de ausência no aplicativo montado, inexistência de usuários/dados "
        "dependentes, testes reais Android/Windows e autorização para remoção.",
        "", "Relatório JSON contém o inventário completo de telas e ocorrências."]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("app_dir", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--check-imports", action="store_true")
    args = parser.parse_args()
    result = scan(args.app_dir)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "NAVIGACAO_INVENTARIO.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")
    (args.output_dir / "NAVIGACAO_INVENTARIO.md").write_text(
        markdown(result), encoding="utf-8")
    print("AUDITAR_NAVIGATION_INVENTORY_OK",
          "screens", result["screen_file_count"],
          "static_candidates", len(result["potentially_unreachable_screens"]),
          "repeated_labels", len(result["repeated_navigation_labels"]),
          "missing_imports", len(result["missing_local_imports"]))
    if args.check_imports and result["missing_local_imports"]:
        raise SystemExit("Missing local Dart imports: see NAVIGACAO_INVENTARIO.json")


if __name__ == "__main__":
    main()
