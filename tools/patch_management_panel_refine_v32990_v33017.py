#!/usr/bin/env python3
from pathlib import Path
import re, sys

if len(sys.argv)<2:
    raise SystemExit("uso: patch_management_panel_refine_v32990_v33017.py <APP_DIR> [android|windows]")

root=Path(sys.argv[1])
platform=(sys.argv[2] if len(sys.argv)>2 else "android").lower()

def read(rel):
    return (root/rel).read_text(encoding="utf-8")

def write(rel,text):
    (root/rel).write_text(text,encoding="utf-8",newline="\n")

def insert_import(text, statement):
    if statement in text: return text
    imports=list(re.finditer(r"(?m)^import\s+[^;]+;\s*$",text))
    if not imports: raise RuntimeError("imports não localizados")
    pos=imports[-1].end()
    return text[:pos]+"\n"+statement+text[pos:]

def replace_method(text, signature, replacement):
    start=text.find(signature)
    if start<0: raise RuntimeError("método não localizado: "+signature)
    paren=text.find("(",start)
    depth=0; quote=None; esc=False; line=False; block=False
    i=paren; close=None
    while i<len(text):
        ch=text[i]; nxt=text[i+1] if i+1<len(text) else ""
        if line:
            if ch=="\n": line=False
            i+=1; continue
        if block:
            if ch=="*" and nxt=="/": block=False; i+=2; continue
            i+=1; continue
        if quote:
            if esc: esc=False
            elif ch=="\\": esc=True
            elif ch==quote: quote=None
            i+=1; continue
        if ch=="/" and nxt=="/": line=True; i+=2; continue
        if ch=="/" and nxt=="*": block=True; i+=2; continue
        if ch in ("'",'"'): quote=ch; i+=1; continue
        if ch=="(": depth+=1
        elif ch==")":
            depth-=1
            if depth==0: close=i; break
        i+=1
    if close is None: raise RuntimeError("parâmetros não fechados")
    brace=text.find("{",close)
    depth=0; quote=None; esc=False; line=False; block=False
    i=brace
    while i<len(text):
        ch=text[i]; nxt=text[i+1] if i+1<len(text) else ""
        if line:
            if ch=="\n": line=False
            i+=1; continue
        if block:
            if ch=="*" and nxt=="/": block=False; i+=2; continue
            i+=1; continue
        if quote:
            if esc: esc=False
            elif ch=="\\": esc=True
            elif ch==quote: quote=None
            i+=1; continue
        if ch=="/" and nxt=="/": line=True; i+=2; continue
        if ch=="/" and nxt=="*": block=True; i+=2; continue
        if ch in ("'",'"'): quote=ch; i+=1; continue
        if ch=="{": depth+=1
        elif ch=="}":
            depth-=1
            if depth==0: return text[:start]+replacement.rstrip()+text[i+1:]
        i+=1
    raise RuntimeError("fim do método não localizado")

rel="lib/screens/management_panel_screen.dart"
s=read(rel)
s=insert_import(s,"import '../services/media_sync_service.dart';")

old="""  Color companyAccent = AuditarBrand.navy;
  Color companyAccentDark = AuditarBrand.navyDark;
  bool companyIdentityLoaded = false;
"""
new="""  Color companyAccent = AuditarBrand.navy;
  Color companyAccentDark = AuditarBrand.navyDark;
  bool companyIdentityLoaded = false;
  String resolvedCompanyLogoPath = '';
  double companyLogoAspectRatio = 1.0;
"""
if new not in s:
    if old not in s: raise RuntimeError("estado da identidade não localizado")
    s=s.replace(old,new,1)

s=s.replace(
"  String get _companyLogoPath => (widget.company.logoPath ?? '').trim();",
"""  String get _companyLogoPath {
    if (resolvedCompanyLogoPath.trim().isNotEmpty) {
      return resolvedCompanyLogoPath.trim();
    }
    return (widget.company.logoPath ?? '').trim();
  }""",1)

helper=r'''  Future<String> _resolveCompanyLogoPath() async {
    var path = (widget.company.logoPath ?? '').trim();
    if (path.isNotEmpty && await File(path).exists()) return path;

    try {
      await MediaSyncService.restoreCompanyLogos(
        companyIds: [widget.company.id],
      );
    } catch (_) {}

    try {
      final companies = await AppDatabase.instance.getCompanies(
        onlyActive: false,
      );
      for (final company in companies) {
        if (company.id != widget.company.id) continue;
        final candidate = (company.logoPath ?? '').trim();
        if (candidate.isNotEmpty && await File(candidate).exists()) {
          return candidate;
        }
      }
    } catch (_) {}
    return '';
  }

  String get _companyInitials {
    final parts = widget.company.name
        .trim()
        .split(RegExp(r'\s+'))
        .where((part) => part.isNotEmpty)
        .toList();
    if (parts.isEmpty) return 'EMP';
    if (parts.length == 1) {
      final take = parts.first.length < 2 ? parts.first.length : 2;
      return parts.first.substring(0, take).toUpperCase();
    }
    return '${parts.first[0]}${parts.last[0]}'.toUpperCase();
  }

  String get _companyLocation {
    final city = (widget.company.city ?? '').trim();
    final uf = (widget.company.uf ?? '').trim();
    if (city.isEmpty && uf.isEmpty) return '';
    if (city.isEmpty) return uf;
    if (uf.isEmpty) return city;
    return '$city • $uf';
  }

'''
if "_resolveCompanyLogoPath() async" not in s:
    marker="  Future<void> _loadCompanyIdentity() async {"
    if marker not in s: raise RuntimeError("identidade da empresa não localizada")
    s=s.replace(marker,helper+marker,1)

identity=r'''  Future<void> _loadCompanyIdentity() async {
    Color accent = AuditarBrand.navy;
    Color dark = AuditarBrand.navyDark;
    var ratio = 1.0;
    final path = await _resolveCompanyLogoPath();

    if (path.isNotEmpty) {
      try {
        final file = File(path);
        if (await file.exists()) {
          final bytes = await file.readAsBytes();
          final codec = await ui.instantiateImageCodec(bytes, targetWidth: 96);
          final frame = await codec.getNextFrame();
          final image = frame.image;
          if (image.height > 0) {
            ratio = (image.width / image.height).clamp(.45, 4.0).toDouble();
          }
          final data = await image.toByteData(format: ui.ImageByteFormat.rawRgba);
          if (data != null) {
            final counts = <int, int>{};
            for (var i = 0; i + 3 < data.lengthInBytes; i += 4) {
              final r = data.getUint8(i);
              final g = data.getUint8(i + 1);
              final b = data.getUint8(i + 2);
              final a = data.getUint8(i + 3);
              if (a < 170) continue;
              final maxChannel = [r,g,b].reduce((a,b)=>a>b?a:b);
              final minChannel = [r,g,b].reduce((a,b)=>a<b?a:b);
              if (minChannel > 238 || maxChannel < 28) continue;
              final spread = maxChannel-minChannel;
              final key=((r>>4)<<8)|((g>>4)<<4)|(b>>4);
              counts[key]=(counts[key]??0)+1+(spread~/32);
            }
            if (counts.isNotEmpty) {
              final selected=counts.entries.reduce((a,b)=>a.value>=b.value?a:b).key;
              final r=(((selected>>8)&0xF)<<4)+8;
              final g=(((selected>>4)&0xF)<<4)+8;
              final b=((selected&0xF)<<4)+8;
              final hsl=HSLColor.fromColor(Color.fromARGB(255,r,g,b));
              if (hsl.saturation>=.10) {
                accent=hsl
                    .withSaturation(hsl.saturation.clamp(.32,.88).toDouble())
                    .withLightness(hsl.lightness.clamp(.30,.52).toDouble())
                    .toColor();
                dark=hsl
                    .withSaturation(hsl.saturation.clamp(.26,.90).toDouble())
                    .withLightness(hsl.lightness.clamp(.15,.28).toDouble())
                    .toColor();
              }
            }
          }
          image.dispose();
          codec.dispose();
        }
      } catch (_) {}
    }

    if (!mounted) return;
    setState(() {
      resolvedCompanyLogoPath=path;
      companyLogoAspectRatio=ratio;
      companyAccent=accent;
      companyAccentDark=dark;
      companyIdentityLoaded=true;
    });
  }'''
s=replace_method(s,"  Future<void> _loadCompanyIdentity() async",identity)

logo=r'''  Widget _companyLogoWidget({
    double size = 64,
  }) {
    if (!_hasCompanyLogo) {
      return Container(
        width: size,
        height: size,
        alignment: Alignment.center,
        decoration: BoxDecoration(
          color: Colors.white.withValues(alpha: .14),
          borderRadius: BorderRadius.circular(18),
          border: Border.all(color: Colors.white24),
        ),
        child: Text(
          _companyInitials,
          style: const TextStyle(
            color: Colors.white,
            fontSize: 18,
            fontWeight: FontWeight.w900,
          ),
        ),
      );
    }

    final width=companyLogoAspectRatio>=2.2
        ? size*2.05
        : companyLogoAspectRatio>=1.35
            ? size*1.65
            : size;

    return AnimatedContainer(
      duration: const Duration(milliseconds: 220),
      width: width,
      height: size,
      padding: const EdgeInsets.all(7),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(18),
        boxShadow: const [
          BoxShadow(
            color: Color(0x26000000),
            blurRadius: 14,
            offset: Offset(0,5),
          ),
        ],
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(11),
        child: Image.file(
          File(_companyLogoPath),
          fit: BoxFit.contain,
          errorBuilder: (_,__,___)=>Center(
            child: Text(
              _companyInitials,
              style: TextStyle(
                color: companyAccentDark,
                fontWeight: FontWeight.w900,
              ),
            ),
          ),
        ),
      ),
    );
  }'''
s=replace_method(s,"  Widget _companyLogoWidget(",logo)

# Evita duas leituras concorrentes da logo e atualiza a identidade ao puxar a tela.
s=s.replace(
"""  void initState() {
    super.initState();
    _load();
    _loadCompanyIdentity();
  }
""",
"""  void initState() {
    super.initState();
    _load();
  }
""",1)

load_start=s.find("  Future<void> _load() async")
load_end=s.find("  int _intValue",load_start)
if "await _loadCompanyIdentity();" not in s[load_start:load_end]:
    old_tail="""      panelUrl = url;
      loading = false;
    });
  }
"""
    new_tail="""      panelUrl = url;
      loading = false;
    });
    await _loadCompanyIdentity();
  }
"""
    if old_tail not in s: raise RuntimeError("final de _load não localizado")
    s=s.replace(old_tail,new_tail,1)

header=r'''  Widget _header() {
    final cnpj=(widget.company.cnpj??'').trim();
    final location=_companyLocation;

    return Container(
      clipBehavior: Clip.antiAlias,
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [_companyHeaderColor,_companyHeaderDark],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(22),
        boxShadow: const [
          BoxShadow(
            color: Color(0x1F000000),
            blurRadius: 18,
            offset: Offset(0,8),
          ),
        ],
      ),
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: LayoutBuilder(
          builder: (context,constraints) {
            final compact=constraints.maxWidth<520;
            return Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  crossAxisAlignment: CrossAxisAlignment.center,
                  children: [
                    _companyLogoWidget(size: compact?58:70),
                    const SizedBox(width: 13),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            widget.company.name,
                            maxLines: 2,
                            overflow: TextOverflow.ellipsis,
                            style: TextStyle(
                              color: Colors.white,
                              fontSize: compact?18:21,
                              height: 1.05,
                              fontWeight: FontWeight.w900,
                            ),
                          ),
                          const SizedBox(height: 6),
                          Wrap(
                            spacing: 8,
                            runSpacing: 5,
                            children: [
                              if (cnpj.isNotEmpty)
                                _headerMetaChip(Icons.badge_outlined,cnpj),
                              if (location.isNotEmpty)
                                _headerMetaChip(Icons.location_on_outlined,location),
                            ],
                          ),
                        ],
                      ),
                    ),
                    if (!compact) ...[
                      const SizedBox(width: 10),
                      _panelStatusChip(),
                    ],
                  ],
                ),
                if (compact) ...[
                  const SizedBox(height: 12),
                  _panelStatusChip(),
                ],
                const SizedBox(height: 14),
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.symmetric(horizontal:12,vertical:9),
                  decoration: BoxDecoration(
                    color: Colors.white.withValues(alpha:.09),
                    borderRadius: BorderRadius.circular(13),
                    border: Border.all(color: Colors.white12),
                  ),
                  child: Wrap(
                    spacing: 16,
                    runSpacing: 6,
                    children: [
                      const Text(
                        'Acompanhamento gerencial SST',
                        style: TextStyle(
                          color: Colors.white,
                          fontSize: 12.5,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                      Text(
                        'Código: $_shortCode',
                        style: const TextStyle(
                          color: Colors.white70,
                          fontSize: 11.5,
                        ),
                      ),
                      Text(
                        'Atualizado: ${_formatSyncDate()}',
                        style: const TextStyle(
                          color: Colors.white70,
                          fontSize: 11.5,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            );
          },
        ),
      ),
    );
  }

  Widget _panelStatusChip() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal:10,vertical:6),
      decoration: BoxDecoration(
        color: enabled
            ? Colors.white.withValues(alpha:.95)
            : Colors.white24,
        borderRadius: BorderRadius.circular(20),
      ),
      child: Text(
        enabled?'PAINEL ATIVO':'PAINEL DESATIVADO',
        style: TextStyle(
          color: enabled?_companyHeaderColor:Colors.white,
          fontSize: 10,
          fontWeight: FontWeight.w900,
        ),
      ),
    );
  }

  Widget _headerMetaChip(IconData icon,String text) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal:8,vertical:5),
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha:.10),
        borderRadius: BorderRadius.circular(10),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon,size:13,color:Colors.white70),
          const SizedBox(width:4),
          Text(
            text,
            style: const TextStyle(
              color: Colors.white70,
              fontSize: 10.8,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }'''
s=replace_method(s,"  Widget _header()",header)

metric=r'''  Widget _metric(String label,String value,IconData icon,Color color) {
    return Card(
      margin: EdgeInsets.zero,
      elevation: 0,
      child: Container(
        constraints: const BoxConstraints(minHeight: 105),
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: color.withValues(alpha:.14)),
          color: color.withValues(alpha:.035),
        ),
        child: Row(
          children: [
            Container(
              width: 40,
              height: 40,
              decoration: BoxDecoration(
                color: color.withValues(alpha:.11),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Icon(icon,color:color,size:21),
            ),
            const SizedBox(width:10),
            Expanded(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    value,
                    style: TextStyle(
                      color: color,
                      fontSize: 22,
                      height: 1,
                      fontWeight: FontWeight.w900,
                    ),
                  ),
                  const SizedBox(height:5),
                  Text(
                    label,
                    maxLines:2,
                    overflow:TextOverflow.ellipsis,
                    style: const TextStyle(
                      fontSize:10.8,
                      height:1.15,
                      color:Colors.black54,
                      fontWeight:FontWeight.w600,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }'''
s=replace_method(s,"  Widget _metric(",metric)

attention=r'''  Widget _managementAttentionCard({
    required int openNcCount,
    required int overdueActions,
    required int expiredTrainings,
    required int missingTrainings,
    required int criticalSectors,
  }) {
    final critical=overdueActions>0||criticalSectors>0;
    final attention=openNcCount>0||
        expiredTrainings>0||
        missingTrainings>0||
        critical;
    final color=critical
        ? const Color(0xFFD93025)
        : attention
            ? const Color(0xFFF29D18)
            : companyAccent;
    final title=critical
        ? 'Itens que exigem prioridade'
        : attention
            ? 'Pontos para acompanhamento'
            : 'Sem pendências prioritárias nos indicadores atuais';
    final chips=<MapEntry<String,int>>[
      MapEntry('Ações vencidas',overdueActions),
      MapEntry('Setores críticos',criticalSectors),
      MapEntry('NC abertas',openNcCount),
      MapEntry('Treinamentos vencidos',expiredTrainings),
      MapEntry('Obrigatórios sem registro',missingTrainings),
    ].where((entry)=>entry.value>0).toList();

    return Card(
      margin: EdgeInsets.zero,
      elevation:0,
      child: Container(
        width:double.infinity,
        padding: const EdgeInsets.all(15),
        decoration: BoxDecoration(
          color:color.withValues(alpha:.045),
          borderRadius:BorderRadius.circular(14),
          border:Border.all(color:color.withValues(alpha:.17)),
        ),
        child:Column(
          crossAxisAlignment:CrossAxisAlignment.start,
          children:[
            Row(
              children:[
                Container(
                  width:40,
                  height:40,
                  decoration:BoxDecoration(
                    color:color.withValues(alpha:.12),
                    borderRadius:BorderRadius.circular(12),
                  ),
                  child:Icon(
                    attention?Icons.priority_high_rounded:Icons.verified_outlined,
                    color:color,
                  ),
                ),
                const SizedBox(width:10),
                Expanded(
                  child:Text(
                    title,
                    style:TextStyle(
                      color:color,
                      fontSize:15,
                      fontWeight:FontWeight.w900,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height:7),
            Text(
              attention
                  ? 'Priorize os itens abaixo e acompanhe a evolução nas próximas atualizações.'
                  : 'Os indicadores consolidados não apontam pendências prioritárias neste momento.',
              style: const TextStyle(
                fontSize:12.2,
                color:Colors.black54,
                height:1.35,
              ),
            ),
            if(chips.isNotEmpty)...[
              const SizedBox(height:11),
              Wrap(
                spacing:7,
                runSpacing:7,
                children:chips.map((entry)=>Container(
                  padding:const EdgeInsets.symmetric(horizontal:9,vertical:6),
                  decoration:BoxDecoration(
                    color:Colors.white,
                    borderRadius:BorderRadius.circular(20),
                    border:Border.all(color:color.withValues(alpha:.18)),
                  ),
                  child:Text(
                    '${entry.value} • ${entry.key}',
                    style:TextStyle(
                      fontSize:10.8,
                      color:color,
                      fontWeight:FontWeight.w700,
                    ),
                  ),
                )).toList(),
              ),
            ],
          ],
        ),
      ),
    );
  }'''
s=replace_method(s,"  Widget _managementAttentionCard(",attention)

sector=r'''  Widget _sectorCard(Map<String,Object?> row) {
    final conformity=_sectorConformity(row);
    final hasData=_sectorHasInspectionData(row);
    final openNcs=_intValue(row,'open_ncs');
    final overdue=_intValue(row,'overdue_ncs');
    final color=!hasData
        ? Colors.blueGrey
        : conformity>=80
            ? companyAccent
            : conformity>=60
                ? const Color(0xFFF29D18)
                : const Color(0xFFD93025);
    final status=!hasData
        ? 'SEM DADOS'
        : overdue>0
            ? 'COM VENCIMENTO'
            : conformity<60
                ? 'ATENÇÃO'
                : conformity<80
                    ? 'ACOMPANHAR'
                    : 'EM DIA';

    return Card(
      margin:const EdgeInsets.only(bottom:8),
      elevation:0,
      child:Padding(
        padding:const EdgeInsets.all(13),
        child:Column(
          children:[
            Row(
              children:[
                Expanded(
                  child:Text(
                    '${row['name'] ?? 'Setor'}',
                    style:const TextStyle(
                      fontSize:13.5,
                      fontWeight:FontWeight.w900,
                    ),
                  ),
                ),
                Container(
                  padding:const EdgeInsets.symmetric(horizontal:8,vertical:4),
                  decoration:BoxDecoration(
                    color:color.withValues(alpha:.10),
                    borderRadius:BorderRadius.circular(20),
                  ),
                  child:Text(
                    status,
                    style:TextStyle(
                      color:color,
                      fontSize:9.5,
                      fontWeight:FontWeight.w900,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height:10),
            Row(
              children:[
                Expanded(
                  child:ClipRRect(
                    borderRadius:BorderRadius.circular(10),
                    child:LinearProgressIndicator(
                      value:hasData?conformity/100:0,
                      minHeight:7,
                      color:color,
                      backgroundColor:color.withValues(alpha:.10),
                    ),
                  ),
                ),
                const SizedBox(width:10),
                SizedBox(
                  width:42,
                  child:Text(
                    hasData?'$conformity%':'—',
                    textAlign:TextAlign.right,
                    style:TextStyle(
                      color:color,
                      fontWeight:FontWeight.w900,
                      fontSize:12,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height:8),
            Row(
              children:[
                Icon(
                  Icons.report_problem_outlined,
                  size:15,
                  color:openNcs>0?const Color(0xFFD93025):Colors.black38,
                ),
                const SizedBox(width:4),
                Text(
                  '$openNcs NC aberta${openNcs==1?'':'s'}',
                  style:const TextStyle(fontSize:11,color:Colors.black54),
                ),
                if(overdue>0)...[
                  const SizedBox(width:12),
                  const Icon(
                    Icons.schedule_rounded,
                    size:15,
                    color:Color(0xFFD93025),
                  ),
                  const SizedBox(width:4),
                  Text(
                    '$overdue vencida${overdue==1?'':'s'}',
                    style:const TextStyle(
                      fontSize:11,
                      color:Color(0xFFD93025),
                      fontWeight:FontWeight.w700,
                    ),
                  ),
                ],
              ],
            ),
          ],
        ),
      ),
    );
  }'''
s=replace_method(s,"  Widget _sectorCard(",sector)

# Refinamentos leves de hierarquia e responsividade sem alterar a lógica.
s=s.replace("'O que a gerência acompanha'","'Resumo executivo'",1)
s=s.replace("maxColumns: 3,","maxColumns: 6,",1)
s=s.replace("color: AuditarBrand.navy,\n              fontWeight: FontWeight.w800,","color: companyAccentDark,\n              fontWeight: FontWeight.w800,",1)

relpub="pubspec.yaml"
pub=read(relpub)
version="3.30.17+204" if platform=="windows" else "3.29.90+232"
pub,n=re.subn(r"(?m)^version:\s*[^\r\n]+","version: "+version,pub,count=1)
if n!=1: raise RuntimeError("versão não localizada")
write(relpub,pub)
write(rel,s)

screen=read(rel)
for marker in [
    "MediaSyncService.restoreCompanyLogos",
    "resolvedCompanyLogoPath",
    "companyLogoAspectRatio",
    "Resumo executivo",
    "Itens que exigem prioridade",
    "PAINEL ATIVO",
    "_headerMetaChip",
]:
    assert marker in screen, "painel refinado sem "+marker

for forbidden in [
    "DeviceSyncService.synchronize",
    "SyncCoordinator",
    "media_upload",
    "device_push",
    "device_pull",
]:
    assert forbidden not in screen, "painel acoplado à sincronização: "+forbidden

assert f"version: {version}" in read(relpub)
print("MANAGEMENT_PANEL_REFINED_OK",platform,version)
