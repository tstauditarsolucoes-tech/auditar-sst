#!/usr/bin/env python3
"""Android: complementa NR-01 a NR-38 (exceto 02/27) sem alterar núcleo.

Usar APÓS patch_sst_deep_catalog_v2.py e patch_nr12_bakery_library_v1.py.
Só acrescenta modelos de orientação, filtro por NR e testes; falha em mudanças
inesperadas de layout. Não toca sync, IA, base, login, Drive, PDF ou Apps Script.
"""
from pathlib import Path
import hashlib
import shutil
import sys

if len(sys.argv)!=2:
    raise SystemExit("Uso: patch_all_nrs_library_v1.py <APP_DIR>")
app=Path(sys.argv[1])
repo=Path(__file__).resolve().parents[1]
catalog=app/"lib/services/offline_sst_deep_catalog_v2.dart"
oldnr=app/"lib/services/offline_sst_bakery_nr12_v1.dart"
newnr=app/"lib/services/offline_sst_all_nrs_v1.dart"
widget=app/"lib/widgets/offline_report_inline_suggestions.dart"
deep_test=app/"test/offline_sst_deep_catalog_test.dart"
new_test=app/"test/offline_sst_all_nrs_test.dart"
bakery_test=app/"test/offline_sst_bakery_nr12_test.dart"
assert all(p.exists() for p in [catalog,oldnr,widget,deep_test,bakery_test]), (
    "Biblioteca antiga ainda não montada: nenhuma alteração aplicada")
assert not newnr.exists() and not new_test.exists(), (
    "Extensão das demais NRs já instalada: não duplicar modelos")
allowed={catalog,widget,deep_test,bakery_test,newnr,new_test}
protected={
    p:hashlib.sha256(p.read_bytes()).hexdigest()
    for folder in (app/"lib",app/"painel_web_google_apps_script")
    if folder.is_dir()
    for p in folder.rglob("*")
    if p.is_file() and p not in allowed
}

def exactly_one(source,old,new,why):
    count=source.count(old)
    if count!=1:
        raise RuntimeError(f"{why}: âncora {count}, esperado exatamente 1")
    return source.replace(old,new,1)

src=catalog.read_text(encoding="utf-8")
src=exactly_one(src,
    "import 'offline_sst_bakery_nr12_v1.dart';",
    "import 'offline_sst_bakery_nr12_v1.dart';\n"
    "import 'offline_sst_all_nrs_v1.dart';",
    "import do novo catálogo")
src=exactly_one(src,
    "    ...OfflineSstBakeryNr12Catalog.entries,",
    "    ...OfflineSstBakeryNr12Catalog.entries,\n"
    "    ...OfflineSstAllNrsCatalog.entries,",
    "mesclar modelos antigos sem alterar IDs")
src=exactly_one(src,"    int limit=250,","    int limit=500,",
    "limite geral de consulta, antes da filtragem")
src=exactly_one(src,
    "return entries.where((e) =>\n      RegExp(e['entityRegex']!).hasMatch(s)",
    "return entries.where((e) =>\n      e['browseOnly'] != 'true' &&\n"
    "      RegExp(e['entityRegex']!).hasMatch(s)",
    "não automatizar enquadramento de NR-3/15/16/28")
catalog.write_text(src,encoding="utf-8",newline="\n")
shutil.copyfile(repo/"feature_sources/offline_sst_all_nrs_v1.dart",newnr)

ui=widget.read_text(encoding="utf-8")
ui=exactly_one(ui,
    "import '../services/offline_sst_deep_catalog_v2.dart';",
    "import '../services/offline_sst_deep_catalog_v2.dart';\n"
    "import '../services/offline_sst_all_nrs_v1.dart';",
    "import NR específica no navegador")
old="""                    for(final area in areas) Padding(
                      padding:const EdgeInsets.only(right:6),
                      child:ChoiceChip(label:Text(area),selected:selected==area,
                        onSelected:(v) {if(v) refresh(()=>selected=area);}),
                    ),"""
new="""                    for(final area in areas) Padding(
                      padding:const EdgeInsets.only(right:6),
                      child:ChoiceChip(label:Text(area),selected:selected==area,
                        onSelected:(v) {if(v) refresh(()=>selected=area);}),
                    ),
                    Padding(
                      padding:const EdgeInsets.only(left:6,right:6),
                      child:PopupMenuButton<String>(
                        tooltip:'Escolher outra NR',
                        onSelected:(nr)=>refresh(()=>selected=nr),
                        itemBuilder:(context)=>[
                          for(final nr in OfflineSstAllNrsCatalog.activeStandards)
                            PopupMenuItem<String>(value:nr,child:Text(nr)),
                        ],
                        child:Chip(label:Row(mainAxisSize:MainAxisSize.min,
                          children:[
                            Text(OfflineSstAllNrsCatalog.activeStandards.contains(selected)
                                && !areas.contains(selected)
                                ? selected : 'Mais NRs'),
                            const Icon(Icons.arrow_drop_down),
                          ])),
                      ),
                    ),"""
ui=exactly_one(ui,old,new,"seletor compacto para as outras 36 NRs")
# 3/15/16/28: browse-only must not be ranked as an automatic suggestion,
# even if fallback ranking finds similar terms.
ui=exactly_one(ui,
    "    final title = _normalize(item.title);",
    """    if (item.id.startsWith('all-nrs-03-') ||
        item.id.startsWith('all-nrs-15-') ||
        item.id.startsWith('all-nrs-16-') ||
        item.id.startsWith('all-nrs-28-')) {
      return 0; // Apenas consulta técnica: nunca sugerir NC automática.
    }
    final title = _normalize(item.title);""",
    "bloqueio de enquadramento automático no ranking")
# A navegação por catálogo permite leitura das informações, mas nunca aplica
# ao registro de NC as entradas classificadas como consulta técnica.
ui=exactly_one(ui,
    """                        onTap:(){
                          final id=item['id'] ?? '';""",
    """                        onTap:() async {
                          if (item['browseOnly'] == 'true') {
                            await showDialog<void>(
                              context: innerContext,
                              builder: (dialogContext) => AlertDialog(
                                title: Text(item['title'] ?? 'Consulta técnica'),
                                content: SingleChildScrollView(
                                  child: Text([
                                    item['description'] ?? '',
                                    if ((item['risk'] ?? '').isNotEmpty)
                                      'Risco ou tema: '+item['risk']!,
                                    item['recommendation'] ?? '',
                                    'Orientação de consulta, não constitui '
                                    'enquadramento nem registra NC automaticamente.',
                                  ].where((v)=>v.isNotEmpty).join('\\n\\n')),
                                ),
                                actions: [
                                  TextButton(
                                    onPressed: ()=>Navigator.of(dialogContext).pop(),
                                    child: const Text('Fechar'),
                                  ),
                                ],
                              ),
                            );
                            return;
                          }
                          final id=item['id'] ?? '';""",
    "consulta técnica somente leitura")
ui=exactly_one(ui,
    "subtitle:Text((item['nr'] ?? '')+' • '+(item['risk'] ?? '')),",
    """subtitle:Text((item['nr'] ?? '')+' • '+(item['risk'] ?? '')+
                          (item['browseOnly']=='true' ? ' • Apenas consulta' : '')),""",
    "rótulo consulta")
widget.write_text(ui,encoding="utf-8",newline="\n")

# Additions do not change old test intent or the old catalog IDs.
oldtest=deep_test.read_text(encoding="utf-8")
oldtest=exactly_one(oldtest,
    "acervo detalhado: 194 casos",
    "acervo detalhado: 345 casos",
    "nome do teste do acervo completo")
oldtest=exactly_one(oldtest,
    "expect(all.length,194);",
    "expect(all.length,345);",
    "contagem geral")
oldtest=exactly_one(oldtest,
    "expect(all.map((e)=>e['id']).toSet().length,194);",
    "expect(all.map((e)=>e['id']).toSet().length,345);",
    "unicidade de IDs")
deep_test.write_text(oldtest,encoding="utf-8",newline="\n")
# O teste do complemento de panificação continua exigindo exatamente 194
# quando compilado sozinho; só no pacote conjunto passa a exigir 345.
bakery_source=bakery_test.read_text(encoding="utf-8")
bakery_source=exactly_one(bakery_source,
    "expect(entries.length, 194);",
    "expect(entries.length, 345);",
    "teste acumulado NR-12 + demais NRs")
bakery_source=exactly_one(bakery_source,
    "expect(entries.map((e) => e['id']).toSet().length, 194);",
    "expect(entries.map((e) => e['id']).toSet().length, 345);",
    "unicidade acumulada NR-12")
bakery_test.write_text(bakery_source,encoding="utf-8",newline="\n")
shutil.copyfile(
    repo/"feature_sources/offline_sst_all_nrs_test_v1.dart",new_test)

for p,digest in protected.items():
    assert hashlib.sha256(p.read_bytes()).hexdigest()==digest,str(p)
assert "OfflineSstAllNrsCatalog.entries" in catalog.read_text()
assert "PopupMenuButton<String>" in widget.read_text()
assert "Apenas consulta" in widget.read_text()
assert "Apenas consulta técnica" in widget.read_text() or "Apenas consulta" in widget.read_text()
assert "expect(entries.length, 345)" in bakery_test.read_text()
assert "e['browseOnly'] != 'true'" in catalog.read_text()
print("ALL_NRS_LIBRARY_READY: 151 adicionais; 345 modelos profundos; 36 NRs")
print("NO_SYNC_DB_AUTH_AI_MEDIA_DRIVE_PDF_GS_MODIFICATIONS")
