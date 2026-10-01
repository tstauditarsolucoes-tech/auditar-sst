#!/usr/bin/env python3
"""Auditar SST v3.29.149 / v3.30.68

Pacote operacional final:
- central unificada de DDS, treinamentos e integrações;
- atalhos rápidos no painel da CIPA;
- diagnóstico ADM com resumo de saúde;
- sem schema novo e sem alterar núcleo protegido.
"""
from pathlib import Path
import hashlib
import shutil
import sys

if len(sys.argv) < 3:
    raise SystemExit(
        "uso: patch_operational_finish_v329149_v33068.py "
        "<APP_DIR> <android|windows>"
    )

root = Path(sys.argv[1])
platform = sys.argv[2].strip().lower()
repo = Path(__file__).resolve().parents[1]
if platform not in ("android", "windows"):
    raise SystemExit("plataforma invalida")


def read(rel):
    return (root / rel).read_text(encoding="utf-8")


def write(rel, value):
    (root / rel).write_text(value, encoding="utf-8", newline="\n")


def once(text, old, new, label):
    if new in text:
        return text
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: esperado 1, encontrado {count}")
    return text.replace(old, new, 1)


protected = [
    "lib/database.dart",
    "lib/services/device_sync_service.dart",
    "lib/services/apps_script_http.dart",
    "lib/services/sync_coordinator.dart",
    "lib/services/auth_service.dart",
    "lib/services/drive_service.dart",
    "lib/services/media_sync_service.dart",
    "lib/services/ai_assistant_service.dart",
    "painel_web_google_apps_script/Code.gs",
    "painel_web_google_apps_script/MultiUser.gs",
    "painel_web_google_apps_script/ClientPortal.gs",
    "painel_web_google_apps_script/ClientPortal.html",
    "painel_web_google_apps_script/ReportEmail.gs",
]
before = {
    name: hashlib.sha256((root / name).read_bytes()).hexdigest()
    for name in protected
}

# ------------------------------------------------------------------
# Central de capacitação e DDS: somente leitura sobre registros atuais.
# ------------------------------------------------------------------
src = repo / "feature_sources/training_activity_center_v329149.dart"
dst = root / "lib/screens/training_activity_center_screen.dart"
shutil.copyfile(src, dst)

rel = "lib/screens/field_intelligence_center_screen.dart"
s = read(rel)
s = once(
    s,
    "import 'trainings_screen.dart';\n",
    "import 'trainings_screen.dart';\n"
    "import 'training_activity_center_screen.dart';\n",
    "import central capacitacao",
)

attention_anchor = """              if ((trainingSummary['expired'] ?? 0) > 0)
                quickRow('${trainingSummary['expired']} treinamento(s) vencido(s)',
                  () => openPage(TrainingsScreen(companyId: selectedCompanyId))),
"""
attention_new = attention_anchor + """              quickRow(
                'Consultar DDS, treinamentos e integrações',
                () => openPage(
                  TrainingActivityCenterScreen(
                    companyId: selectedCompanyId,
                    companyName: selectedCompany?.name ?? '',
                  ),
                ),
              ),
"""
if "Consultar DDS, treinamentos e integrações" not in s:
    if attention_anchor not in s:
        raise RuntimeError("ancora central capacitacao ausente")
    s = s.replace(attention_anchor, attention_new, 1)

diag_anchor = """    return ListView(
      padding: const EdgeInsets.all(14),
      children: [
        title('Diagnóstico técnico ADM',
          'Somente leitura. Não altera fila, banco ou sincronização.'),
        const SizedBox(height: 10),
"""
diag_new = """    final healthy = structuredPending == 0 &&
        mediaPending == 0 &&
        lastSyncError.isEmpty &&
        mediaSyncError.isEmpty;
    return ListView(
      padding: const EdgeInsets.all(14),
      children: [
        title('Diagnóstico técnico ADM',
          'Somente leitura. Não altera fila, banco ou sincronização.'),
        const SizedBox(height: 10),
        Card(
          color: healthy
              ? AuditarBrand.greenSoft
              : const Color(0xFFFFF4DF),
          child: ListTile(
            leading: Icon(
              healthy
                  ? Icons.verified_outlined
                  : Icons.warning_amber_rounded,
              color: healthy
                  ? AuditarBrand.greenDark
                  : const Color(0xFFAD6409),
            ),
            title: Text(
              healthy
                  ? 'Operação local sem alertas técnicos'
                  : 'Este aparelho requer atenção',
              style: const TextStyle(fontWeight: FontWeight.w900),
            ),
            subtitle: Text(
              healthy
                  ? 'Fila limpa e nenhum erro recente registrado.'
                  : 'Confira filas pendentes e os erros apresentados abaixo.',
            ),
            trailing: TextButton(
              onPressed: showQueue,
              child: const Text('Fila'),
            ),
          ),
        ),
        const SizedBox(height: 10),
"""
s = once(s, diag_anchor, diag_new, "resumo saude adm")
s = once(
    s,
    "    final version = Platform.isWindows ? '3.30.67' : '3.29.148';",
    "    final version = Platform.isWindows ? '3.30.68' : '3.29.149';",
    "versao diagnostico",
)
write(rel, s)

# ------------------------------------------------------------------
# CIPA: atalhos operacionais dentro do painel existente.
# ------------------------------------------------------------------
cipa_rel = "lib/screens/cipa_management_screen.dart"
cipa = read(cipa_rel)
panel_anchor = """          const SizedBox(height: 14),
          Row(
            children: [
              const Expanded(
                child: Text(
                  'Alertas importantes',
"""
panel_new = """          const SizedBox(height: 14),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(13),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Acesso rápido às pendências',
                    style: TextStyle(
                      fontWeight: FontWeight.w900,
                      fontSize: 15,
                    ),
                  ),
                  const SizedBox(height: 9),
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: [
                      ActionChip(
                        avatar: const Icon(Icons.event_outlined, size: 18),
                        label: Text('Reuniões • $pending'),
                        onPressed: () =>
                            DefaultTabController.of(context).animateTo(3),
                      ),
                      ActionChip(
                        avatar: const Icon(Icons.description_outlined, size: 18),
                        label: Text('Atas • $pendingMinutesCount'),
                        onPressed: () =>
                            DefaultTabController.of(context).animateTo(4),
                      ),
                      ActionChip(
                        avatar: const Icon(Icons.task_alt_outlined, size: 18),
                        label: Text('Ações • $openActions'),
                        onPressed: () =>
                            DefaultTabController.of(context).animateTo(5),
                      ),
                      ActionChip(
                        avatar: const Icon(Icons.school_outlined, size: 18),
                        label: Text('Treinamentos • $pendingTrainingCount'),
                        onPressed: () =>
                            DefaultTabController.of(context).animateTo(7),
                      ),
                      ActionChip(
                        avatar: const Icon(Icons.folder_copy_outlined, size: 18),
                        label: const Text('Documentos'),
                        onPressed: () =>
                            DefaultTabController.of(context).animateTo(8),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 14),
          Row(
            children: [
              const Expanded(
                child: Text(
                  'Alertas importantes',
"""
cipa = once(cipa, panel_anchor, panel_new, "atalhos CIPA")
write(cipa_rel, cipa)

# ------------------------------------------------------------------
# Versão.
# ------------------------------------------------------------------
pub_rel = "pubspec.yaml"
pub = read(pub_rel)
old_release, new_release = (
    ("3.29.148+290", "3.29.149+291")
    if platform == "android"
    else ("3.30.67+254", "3.30.68+255")
)
marker = "version: " + old_release
if pub.count(marker) != 1:
    raise RuntimeError("versao esperada ausente: " + old_release)
write(pub_rel, pub.replace(marker, "version: " + new_release, 1))

changed = [
    name
    for name, digest in before.items()
    if hashlib.sha256((root / name).read_bytes()).hexdigest() != digest
]
if changed:
    raise SystemExit("PROTECTED_CORE_MODIFIED: " + repr(changed))

for marker in [
    "TrainingActivityCenterScreen",
    "Consultar DDS, treinamentos e integrações",
    "Operação local sem alertas técnicos",
]:
    if marker not in read(
        "lib/screens/field_intelligence_center_screen.dart"
    ):
        raise RuntimeError("marcador central ausente: " + marker)

for marker in [
    "Acesso rápido às pendências",
    "Treinamentos • $pendingTrainingCount",
    "DefaultTabController.of(context).animateTo(8)",
]:
    if marker not in read(cipa_rel):
        raise RuntimeError("marcador CIPA ausente: " + marker)

print("OPERATIONAL_FINISH_OK", platform, new_release)
print("SYNC_DB_AUTH_MEDIA_AI_DRIVE_GS_BYTE_IDENTICAL_OK")
