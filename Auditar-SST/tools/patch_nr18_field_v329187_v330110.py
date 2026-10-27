#!/usr/bin/env python3
"""Add isolated NR-18 on-site checklist to existing worksite view, without changing SST core."""
import hashlib
import re
from pathlib import Path
import shutil
import sys

root = Path(sys.argv[1])
platform = sys.argv[2]
assert platform in ("android", "windows")
repo = Path(__file__).resolve().parents[1]
existing = root/"lib/screens/worksite_followup_screen.dart"
new = root/"lib/screens/nr18_field_checklist_screen.dart"
test = root/"test/nr18_field_checklist_test.dart"
assert existing.is_file() and not new.exists(), "Unexpected NR-18 baseline"
old_version,new_version = (("3.29.186+328","3.29.187+329")
    if platform=="android" else ("3.30.109+296","3.30.110+297"))
pubspec = root/"pubspec.yaml"
version_text = pubspec.read_text(encoding="utf-8")
assert version_text.count("version: "+old_version)==1
allowed = {existing}
protected = [p for folder in ("lib","painel_web_google_apps_script")
    for p in (root/folder).rglob("*")
    if p.is_file() and p not in allowed]
digest={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in protected}
value=existing.read_text(encoding="utf-8")
anchor="import 'manager_reports_screen.dart';"
assert value.count(anchor)==1
value=value.replace(anchor,anchor+"\nimport 'nr18_field_checklist_screen.dart';",1)
# The assembled screen has already passed through dart format in older steps.
# Anchor to the *semantic* phase dropdown instead of brittle whitespace.
phase_field = re.compile(
    r"DropdownButtonFormField\s*<\s*String\s*>\s*\(\s*key\s*:\s*ValueKey\s*\(\s*'phase-'"
)
matches = list(phase_field.finditer(value))
assert len(matches) == 1, "Expected exactly one worksite phase field"
addition="""        Card(child:Padding(padding:const EdgeInsets.all(12),
          child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[
            Text('Segurança da obra • NR-18',
              style:Theme.of(context).textTheme.titleMedium),
            const SizedBox(height:6),
            const Text('Roteiro orientativo por etapa, com registro local dos pontos verificados. Não cria NC automática.'),
            const SizedBox(height:8),
            FilledButton.icon(
              onPressed:()=>_open(Nr18FieldChecklistScreen(
                company:widget.company,phase:_record.phase)),
              icon:const Icon(Icons.rule_folder_outlined),
              label:const Text('Inspecionar NR-18')),
          ]))),
        const SizedBox(height:16),
"""
# Preserve the exact original dropdown code; only prepend the new NR-18 card.
value = value[:matches[0].start()] + addition + value[matches[0].start():]
existing.write_text(value,encoding="utf-8")
shutil.copyfile(repo/"feature_sources/nr18_field_checklist_screen_v329187.dart",new)
shutil.copyfile(repo/"feature_sources/nr18_field_checklist_test_v329187.dart",test)
pubspec.write_text(version_text.replace("version: "+old_version,
                                        "version: "+new_version),encoding="utf-8")
for path,original in digest.items():
    assert hashlib.sha256(path.read_bytes()).hexdigest()==original,str(path)
print("NR18_FIELD_READY",platform,new_version,"CORE_GS_MEDIA_SYNC_AUTH_UNCHANGED")
