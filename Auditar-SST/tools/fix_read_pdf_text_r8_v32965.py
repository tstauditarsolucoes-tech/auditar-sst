#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'app/Auditar_SST_v1_5_dashboard')
android = root / 'android'
app = android / 'app'
app.mkdir(parents=True, exist_ok=True)

rules = app / 'proguard-rules.pro'
existing = rules.read_text(encoding='utf-8') if rules.exists() else ''
rule = '-dontwarn com.gemalto.jp2.**\n'
if rule.strip() not in existing:
    rules.write_text(existing + ('\n' if existing and not existing.endswith('\n') else '') + rule, encoding='utf-8')

kts = app / 'build.gradle.kts'
groovy = app / 'build.gradle'

if kts.exists():
    text = kts.read_text(encoding='utf-8')
    marker = '        release {\n'
    inject = (
        '        release {\n'
        '            proguardFiles(\n'
        '                getDefaultProguardFile("proguard-android-optimize.txt"),\n'
        '                "proguard-rules.pro",\n'
        '            )\n'
    )
    if '"proguard-rules.pro"' not in text:
        if marker not in text:
            raise SystemExit('Bloco release nao encontrado em build.gradle.kts')
        text = text.replace(marker, inject, 1)
        kts.write_text(text, encoding='utf-8')
elif groovy.exists():
    text = groovy.read_text(encoding='utf-8')
    marker = '        release {\n'
    inject = (
        '        release {\n'
        "            proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'), 'proguard-rules.pro'\n"
    )
    if 'proguard-rules.pro' not in text:
        if marker not in text:
            raise SystemExit('Bloco release nao encontrado em build.gradle')
        text = text.replace(marker, inject, 1)
        groovy.write_text(text, encoding='utf-8')
else:
    raise SystemExit('Arquivo Gradle do app nao encontrado.')

print('R8_OK: decoder JP2 opcional ignorado para extracao de texto do PDF.')
