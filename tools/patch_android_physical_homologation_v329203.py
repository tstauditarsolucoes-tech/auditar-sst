#!/usr/bin/env python3
"""Prepare independent optimized Android candidate; never embed production credentials."""
from pathlib import Path
import hashlib
import re
import sys

root = Path(sys.argv[1])
protected = [root/'lib/database.dart', root/'lib/models.dart', *sorted((root/'lib/services').glob('*.dart'))]
before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in protected if p.is_file()}

def replace_once(s, old, new):
    if s.count(old) != 1:
        raise RuntimeError("Unexpected source anchor: " + old[:100])
    return s.replace(old, new, 1)

logo = root/'lib/widgets/auditar_brand_logo.dart'
s = logo.read_text(encoding='utf-8')
s = replace_once(s, 'return Row(', 'final logo = Row(')
# The brand row is non-flexible and has a finite natural size. Compact mode
# scales only when the AppBar allocates less space; normal branding unchanged.
tail = re.search(r'\n(\s*)\);\s*\n  }\s*\n}\s*$', s)
if not tail:
    raise RuntimeError("Unexpected brand widget ending")
s = s[:tail.start()] + '''
    );
    return compact
        ? FittedBox(
            fit: BoxFit.scaleDown,
            alignment: Alignment.centerLeft,
            child: logo,
          )
        : logo;
  }
}
'''
logo.write_text(s, encoding='utf-8')
test = root/'test/auditar_compact_toolbar_test.dart'
if test.exists():
    raise RuntimeError("Unexpected existing test")
test.write_text("""import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import '../lib/widgets/auditar_brand_logo.dart';

void main() {
  for (final width in [320.0, 360.0, 412.0]) {
    for (final scale in [1.0, 1.3, 2.0]) {
      testWidgets('compact AppBar width=$width textScale=$scale', (tester) async {
        tester.view.devicePixelRatio = 1;
        tester.view.physicalSize = Size(width, 800);
        addTearDown(tester.view.resetPhysicalSize);
        addTearDown(tester.view.resetDevicePixelRatio);
        await tester.pumpWidget(MaterialApp(
          builder: (context, child) => MediaQuery(
            data: MediaQuery.of(context).copyWith(textScaler: TextScaler.linear(scale)),
            child: child!,
          ),
          home: Scaffold(
            appBar: AppBar(
              titleSpacing: 16,
              title: const AuditarBrandLogo(compact: true, onDark: true, iconSize: 34),
              actions: [
                for (final icon in [Icons.cloud_done_outlined, Icons.search, Icons.refresh, Icons.help_outline, Icons.settings_outlined])
                  IconButton(onPressed: () {}, icon: Icon(icon)),
              ],
            ),
          ),
        ));
        await tester.pumpAndSettle();
        expect(tester.takeException(), isNull);
        expect(find.byType(IconButton), findsNWidgets(5));
      });
    }
  }
}
""", encoding='utf-8')
gradle = root/'android/app/build.gradle.kts'
s = gradle.read_text(encoding='utf-8')
s = replace_once(s, 'applicationId = "br.com.auditar.auditar_sst"', 'applicationId = "br.com.auditar.auditar_sst.homolog"')
gradle.write_text(s, encoding='utf-8')
manifest = root/'android/app/src/main/AndroidManifest.xml'
s = manifest.read_text(encoding='utf-8')
s = replace_once(s, 'android:label="Auditar SST"', 'android:label="Auditar SST Teste"')
manifest.write_text(s, encoding='utf-8')
pub = root/'pubspec.yaml'
s = replace_once(pub.read_text(encoding='utf-8'), 'version: 3.29.202+344', 'version: 3.29.203+345')
pub.write_text(s, encoding='utf-8')
assert all(hashlib.sha256(p.read_bytes()).hexdigest() == h for p,h in before.items())
print('UI patch and independent Android package prepared; protected services unchanged.')
