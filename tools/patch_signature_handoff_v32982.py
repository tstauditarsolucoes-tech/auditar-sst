#!/usr/bin/env python3
from pathlib import Path
import re, sys

root=Path(sys.argv[1])
platform=(sys.argv[2] if len(sys.argv)>2 else 'android').lower()

def read(rel): return (root/rel).read_text(encoding='utf-8')
def write(rel,text): (root/rel).write_text(text,encoding='utf-8',newline='\n')
def once(text,old,new,label):
    if new in text: return text
    if old not in text: raise RuntimeError('Marcador não localizado: '+label)
    return text.replace(old,new,1)

version='3.30.10+197' if platform=='windows' else '3.29.82+224'
pub=read('pubspec.yaml')
pub,n=re.subn(r'^version:\s*[^\n]+',f'version: {version}',pub,count=1,flags=re.M)
if n!=1: raise RuntimeError('Versão não localizada')
write('pubspec.yaml',pub)

rel='lib/screens/training_records_screen.dart'
c=read(rel)

# Caller: pass participant position/total.
old="""    final result = await Navigator.of(context).push<TrainingSignatureResult>(
      MaterialPageRoute(
        fullscreenDialog: true,
        builder: (_) => TrainingRecordSignatureScreen(
          participant: participant,
          trainingTitle: record?.title ?? '',
        ),
      ),
    );
"""
new="""    final participantId = '${participant['id'] ?? ''}';
    final participantIndex = participants.indexWhere(
      (item) => '${item['id'] ?? ''}' == participantId,
    );
    final result = await Navigator.of(context).push<TrainingSignatureResult>(
      MaterialPageRoute(
        fullscreenDialog: true,
        builder: (_) => TrainingRecordSignatureScreen(
          participant: participant,
          trainingTitle: record?.title ?? '',
          participantIndex: participantIndex >= 0 ? participantIndex + 1 : null,
          participantTotal: participants.length,
        ),
      ),
    );
"""
c=once(c,old,new,'caller signature progress')

# Screen fields.
old="""class TrainingRecordSignatureScreen extends StatefulWidget {
  final Map<String, dynamic> participant;
  final String trainingTitle;

  const TrainingRecordSignatureScreen({
    super.key,
    required this.participant,
    required this.trainingTitle,
  });
"""
new="""class TrainingRecordSignatureScreen extends StatefulWidget {
  final Map<String, dynamic> participant;
  final String trainingTitle;
  final int? participantIndex;
  final int? participantTotal;

  const TrainingRecordSignatureScreen({
    super.key,
    required this.participant,
    required this.trainingTitle,
    this.participantIndex,
    this.participantTotal,
  });
"""
c=once(c,old,new,'signature screen fields')

# Replace build block header/content before signature canvas.
old="""  @override
  Widget build(BuildContext context) {
    final name = '${widget.participant['name'] ?? ''}';
    final cpf = '${widget.participant['cpf'] ?? ''}'.trim();

    return Scaffold(
      appBar: AppBar(title: const Text('Assinatura do participante')),
      body: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              name,
              style: const TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.w900,
                color: AuditarBrand.navy,
              ),
            ),
            if (cpf.isNotEmpty) Text('CPF: $cpf'),
            const SizedBox(height: 5),
            Text(
              widget.trainingTitle,
              style: const TextStyle(fontWeight: FontWeight.w700),
            ),
            const SizedBox(height: 10),
            const Text(
              'Ao assinar, o participante confirma sua presença no treinamento acima. A assinatura ficará vinculada à ficha, data e empresa.',
              style: TextStyle(fontSize: 12.5, color: Colors.black54),
            ),
            const SizedBox(height: 12),
            Expanded(
"""
new="""  @override
  Widget build(BuildContext context) {
    final name = '${widget.participant['name'] ?? ''}'.trim();
    final cpf = '${widget.participant['cpf'] ?? ''}'.trim();
    final role = '${widget.participant['role'] ?? ''}'.trim();
    final sector = '${widget.participant['sector'] ?? ''}'.trim();
    final hasProgress = widget.participantIndex != null &&
        widget.participantTotal != null &&
        widget.participantTotal! > 0;

    return Scaffold(
      appBar: AppBar(title: const Text('Assinatura do treinamento')),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                width: double.infinity,
                padding: const EdgeInsets.fromLTRB(16, 14, 16, 14),
                decoration: BoxDecoration(
                  color: AuditarBrand.navySoft,
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(
                    color: AuditarBrand.navy.withValues(alpha: .16),
                  ),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.center,
                  children: [
                    const Text(
                      'ASSINANDO AGORA',
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        fontSize: 12,
                        letterSpacing: 1.3,
                        fontWeight: FontWeight.w900,
                        color: AuditarBrand.greenDark,
                      ),
                    ),
                    const SizedBox(height: 5),
                    Text(
                      name.isEmpty ? 'PARTICIPANTE' : name.toUpperCase(),
                      textAlign: TextAlign.center,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        fontSize: 25,
                        height: 1.08,
                        fontWeight: FontWeight.w900,
                        color: AuditarBrand.navyDark,
                      ),
                    ),
                    if (role.isNotEmpty || sector.isNotEmpty) ...[
                      const SizedBox(height: 6),
                      Text(
                        [
                          if (role.isNotEmpty) role,
                          if (sector.isNotEmpty) sector,
                        ].join(' • '),
                        textAlign: TextAlign.center,
                        style: const TextStyle(
                          fontSize: 13,
                          fontWeight: FontWeight.w700,
                          color: Colors.black87,
                        ),
                      ),
                    ],
                    if (hasProgress) ...[
                      const SizedBox(height: 8),
                      Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 12,
                          vertical: 5,
                        ),
                        decoration: BoxDecoration(
                          color: Colors.white,
                          borderRadius: BorderRadius.circular(20),
                        ),
                        child: Text(
                          'Participante ${widget.participantIndex} de ${widget.participantTotal}',
                          style: const TextStyle(
                            fontSize: 12,
                            fontWeight: FontWeight.w800,
                            color: AuditarBrand.navy,
                          ),
                        ),
                      ),
                    ],
                    if (cpf.isNotEmpty) ...[
                      const SizedBox(height: 6),
                      Text(
                        'CPF: $cpf',
                        style: const TextStyle(
                          fontSize: 11.5,
                          color: Colors.black54,
                        ),
                      ),
                    ],
                  ],
                ),
              ),
              const SizedBox(height: 10),
              Text(
                widget.trainingTitle,
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(
                  fontWeight: FontWeight.w800,
                  color: AuditarBrand.navy,
                ),
              ),
              const SizedBox(height: 5),
              const Text(
                'Confira seu nome acima antes de assinar. Ao confirmar, sua assinatura ficará vinculada a esta ficha de treinamento.',
                style: TextStyle(fontSize: 12.2, color: Colors.black54),
              ),
              const SizedBox(height: 10),
              const Row(
                children: [
                  Icon(
                    Icons.draw_outlined,
                    size: 19,
                    color: AuditarBrand.greenDark,
                  ),
                  SizedBox(width: 6),
                  Text(
                    'ASSINE NO QUADRO ABAIXO',
                    style: TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.w900,
                      color: AuditarBrand.navy,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 6),
              Expanded(
"""
c=once(c,old,new,'signature screen prominent header')

# Need close SafeArea: body currently ends Padding -> Column -> Scaffold.
old="""          ],
        ),
      ),
    );
  }
}
"""
new="""            ],
          ),
        ),
      ),
    );
  }
}
"""
# replace last occurrence after class; rsplit safer
idx=c.rfind(old)
if idx<0: raise RuntimeError('Fechamento signature screen não localizado')
c=c[:idx]+new+c[idx+len(old):]

write(rel,c)

assert f'version: {version}' in read('pubspec.yaml')
assert 'ASSINANDO AGORA' in read(rel)
assert 'Participante ${widget.participantIndex} de ${widget.participantTotal}' in read(rel)
assert 'ASSINE NO QUADRO ABAIXO' in read(rel)
assert 'participantIndex: participantIndex >= 0 ? participantIndex + 1 : null' in read(rel)
print('SIGNATURE_HANDOFF_OK',platform,version)
