"""Migração conservadora das rotas da Home para o seletor de vistoria.

Altera somente _open(const NewInspectionScreen(), tutorialId: 'new_inspection'),
inclusive quando o Dart foi formatado em múltiplas linhas. Nunca altera
outros destinos de navegação ou serviços do Auditar SST.
"""
import re

_LEGACY_NEW_INSPECTION = re.compile(
    r"(?P<open>\b_open\(\s*)"
    r"const\s+NewInspectionScreen\(\s*\)"
    r"(?P<tail>\s*,\s*tutorialId:\s*['\"]new_inspection['\"]\s*,?\s*\))"
)


def reroute_home_new_inspections(source: str) -> tuple[str, int]:
    """Atualiza entre 1 e 4 CTAs conhecidos; falha se o layout for desconhecido."""
    matches = list(_LEGACY_NEW_INSPECTION.finditer(source))
    if not 1 <= len(matches) <= 4:
        raise RuntimeError(f"Rotas de nova vistoria inesperadas: {len(matches)}")
    updated = _LEGACY_NEW_INSPECTION.sub(
        lambda match: match.group('open') +
        'const AuditarVisitTypeChooserScreen()' + match.group('tail'),
        source,
    )
    if _LEGACY_NEW_INSPECTION.search(updated):
        raise RuntimeError("Rotas antigas restantes; homologação interrompida")
    return updated, len(matches)
