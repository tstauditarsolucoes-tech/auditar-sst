#!/usr/bin/env python3
"""Mobile layout fixes for the link panel and long safety records."""
from pathlib import Path
import sys
root=Path(sys.argv[1]);platform=sys.argv[2]
assert platform in ('android','windows')
def rep(s,a,b,label):
    count=s.count(a)
    if count!=1:raise RuntimeError(f'{label}: {count}')
    return s.replace(a,b,1)
p=root/'lib/screens/management_panel_screen.dart';s=p.read_text(encoding='utf-8')
start=s.index("""            if (configured) ...[
              Row(
                children: [
                  Expanded(
                    child: OutlinedButton.icon(""",s.index("  Widget _linkCard()"))
end=s.index("""              const SizedBox(height: 8),
              SizedBox(
                width: double.infinity,
                child: FilledButton.icon(""",start)
original=s[start:end]
if "label: const Text('Compartilhar')" not in original:raise RuntimeError('panel link buttons changed')
replacement="""            if (configured) ...[
              SizedBox(
                width: double.infinity,
                child: OutlinedButton.icon(
                  onPressed: enabled ? _copyLink : null,
                  icon: const Icon(Icons.copy_rounded, size: 18),
                  label: const Text('Copiar link do painel'),
                ),
              ),
              const SizedBox(height: 8),
              SizedBox(
                width: double.infinity,
                child: OutlinedButton.icon(
                  onPressed: enabled ? _shareLink : null,
                  icon: const Icon(Icons.share_outlined, size: 18),
                  label: const Text('Compartilhar link'),
                ),
              ),
"""
s=s[:start]+replacement+s[end:]
key="""            if (syncing) ...[
              const SizedBox(height: 10),
              const LinearProgressIndicator(),
            ],"""
value="""            if (AuthService.isAdmin && configured) ...[
              const SizedBox(height: 10),
              SizedBox(
                width: double.infinity,
                child: TextButton.icon(
                  icon: const Icon(Icons.login_outlined),
                  label: const Text('Copiar acesso individual do cliente'),
                  onPressed: () async {
                    final url = panelUrl.split('?').first + '?cliente=1';
                    await Clipboard.setData(ClipboardData(text: url));
                    if (!mounted) return;
                    ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
                      content: Text('Link copiado. A Central precisa estar implantada com o módulo de clientes.')));
                  },
                ),
              ),
            ],
            if (syncing) ...[
              const SizedBox(height: 10),
              const LinearProgressIndicator(),
            ],"""
s=rep(s,key,value,'client link copy')
p.write_text(s,encoding='utf-8',newline='\n')
p=root/'lib/screens/sst_records_screen.dart';s=p.read_text(encoding='utf-8')
s=rep(s,"""                            record.title,
                            style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 15),""","""                            record.title,
                            maxLines: 3,
                            overflow: TextOverflow.ellipsis,
                            style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 15),""",'long safety record')
p.write_text(s,encoding='utf-8',newline='\n')
print('PANEL_LINK_AND_LONG_RECORD_LAYOUT_OK',platform)
