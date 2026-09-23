#!/usr/bin/env python3
"""Distinct origin and status for proposed vs implemented improvements."""
from pathlib import Path
import sys
root=Path(sys.argv[1]); platform=sys.argv[2]
assert platform in ('android','windows')
def rep(s,a,b,name):
 n=s.count(a)
 if n!=1:raise RuntimeError(name+': '+str(n))
 return s.replace(a,b,1)
p=root/'lib/screens/improvements_screen.dart';s=p.read_text(encoding='utf-8')
s=rep(s,'class ImprovementsScreen extends StatefulWidget {',"""String improvementKind(SstRecord r) {
  final kind = '${r.payload['recordKind'] ?? ''}'.trim();
  if (kind == 'SOLICITACAO' || kind == 'EXECUTADA') return kind;
  return r.status.toLowerCase().contains('realiz') ||
      r.status.toLowerCase().contains('conclu') ? 'EXECUTADA' : 'SOLICITACAO';
}
String improvementKindLabel(SstRecord r) => improvementKind(r) == 'EXECUTADA'
    ? 'MELHORIA EXECUTADA' : 'SOLICITAÇÃO / SUGESTÃO';

class ImprovementsScreen extends StatefulWidget {""",'kind')
s=rep(s,"  String statusFilter = 'Todos';","  String statusFilter = 'Todos';\n  String kindFilter = 'Todos';",'filter field')
s=rep(s,"        if (statusFilter == 'Sugestões' && record.status != 'Sugerida') {","        if (kindFilter != 'Todos' && improvementKind(record) != kindFilter) return false;\n        if (statusFilter == 'Sugestões' && record.status != 'Sugerida') {",'filter')
s=rep(s,"    final suggestions = scoped.where((r) => r.status == 'Sugerida').length;","    final suggestions = scoped.where((r) => improvementKind(r) == 'SOLICITACAO').length;",'summary')
s=rep(s,"_metric('Sugeridas', suggestions, const Color(0xFFF29D18))","_metric('Solicitações', suggestions, const Color(0xFFF29D18))",'summary label')
s=rep(s,"'Sugestões e melhorias realizadas, sempre vinculadas à empresa e ao setor.'","'Solicitações e melhorias executadas, separadas por tipo e situação.'",'description')
s=rep(s,"        label: const Text('Nova melhoria'),","        label: const Text('Novo registro'),",'button')
s=rep(s,"""            DropdownButtonFormField<String>(
              isExpanded: true,
              value: statusFilter,
""","""            DropdownButtonFormField<String>(
              isExpanded: true,
              value: kindFilter,
              decoration: const InputDecoration(labelText: 'Tipo de registro', isDense: true),
              items: const [
                DropdownMenuItem(value: 'Todos', child: Text('Todos os tipos')),
                DropdownMenuItem(value: 'SOLICITACAO', child: Text('Solicitações / sugestões')),
                DropdownMenuItem(value: 'EXECUTADA', child: Text('Melhorias executadas')),
              ],
              onChanged: (value) => setState(() => kindFilter = value ?? 'Todos'),
            ),
            const SizedBox(height: 8),
            DropdownButtonFormField<String>(
              isExpanded: true,
              value: statusFilter,
""",'filter UI')
s=rep(s,"""                const SizedBox(height: 5),
                Text(
                  '${_companyName(record)}""","""                const SizedBox(height: 5),
                Text(improvementKindLabel(record),
                  style: TextStyle(fontSize: 11, fontWeight: FontWeight.w900,
                    color: improvementKind(record) == 'EXECUTADA'
                      ? AuditarBrand.greenDark : const Color(0xFF986416))),
                const SizedBox(height: 5),
                Text(
                  '${_companyName(record)}""",'card')
s=rep(s,"  String status = 'Sugerida';","  String status = 'Sugerida';\n  String recordKind = 'SOLICITACAO';",'form state')
s=rep(s,"    status = record?.status ?? 'Sugerida';","    recordKind = record == null ? 'SOLICITACAO' : improvementKind(record);\n    status = record?.status ?? 'Sugerida';",'legacy')
s=rep(s,"      'companyName': company.name,","      'recordKind': recordKind,\n      'companyName': company.name,",'save kind')
s=rep(s,"        title: Text(widget.existing == null ? 'Nova melhoria' : 'Editar melhoria', maxLines: 1, overflow: TextOverflow.ellipsis),","        title: Text(widget.existing == null ? 'Novo registro' : 'Editar registro', maxLines: 1, overflow: TextOverflow.ellipsis),",'title')
s=rep(s,"""          children: [
            _section('Empresa e setor'),""","""          children: [
            _section('Tipo de registro'),
            DropdownButtonFormField<String>(
              value: recordKind,
              isExpanded: true,
              decoration: const InputDecoration(labelText: 'O que deseja registrar? *'),
              items: const [
                DropdownMenuItem(value: 'SOLICITACAO', child: Text('Solicitação / sugestão de melhoria')),
                DropdownMenuItem(value: 'EXECUTADA', child: Text('Melhoria já executada')),
              ],
              onChanged: (value) => setState(() {
                recordKind = value ?? recordKind;
                status = recordKind == 'EXECUTADA' ? 'Realizada' : 'Sugerida';
                if (recordKind == 'EXECUTADA') completedDate ??= DateTime.now();
              }),
            ),
            const SizedBox(height: 6),
            Text(recordKind == 'EXECUTADA'
                ? 'Registre o que foi feito, o resultado e as fotos de antes e depois.'
                : 'Registre o pedido de melhoria e acompanhe sua situação.',
                style: const TextStyle(fontSize: 12, color: Colors.black54)),
            const SizedBox(height: 14),
            _section('Empresa e setor'),""",'form type')
s=rep(s,"            _section('Sugestão / melhoria'),","            _section(recordKind == 'EXECUTADA' ? 'Melhoria executada' : 'Solicitação / sugestão'),",'section')
s=rep(s,"                labelText: 'Sugestão / melhoria proposta *',","                labelText: recordKind == 'EXECUTADA' ? 'Melhoria realizada *' : 'Melhoria proposta *',",'label')
s=rep(s,"""                  items: const ['Sugerida', 'Planejada', 'Em execução', 'Realizada']
                      .map((value) => DropdownMenuItem(value: value, child: Text(value)))
                      .toList(),""","""                  items: (recordKind == 'EXECUTADA'
                      ? const ['Realizada']
                      : const ['Sugerida', 'Planejada', 'Em execução', 'Realizada'])
                      .map((value) => DropdownMenuItem(value: value, child: Text(value)))
                      .toList(),""",'status')
s=rep(s,"child: Text(saving ? 'Salvando...' : 'Salvar melhoria'),","child: Text(saving ? 'Salvando...' : 'Salvar registro'),",'save label')
p.write_text(s,encoding='utf-8',newline='\n')
p=root/'lib/services/improvement_pdf_service.dart';s=p.read_text(encoding='utf-8')
s=rep(s,"    final suggestions = sorted.where((record) => record.status == 'Sugerida').length;","    final suggestions = sorted.where((record) => _kind(record) == 'SOLICITACAO').length;",'pdf summary')
s=rep(s,"_metric('Sugeridas', suggestions, amber),","_metric('Solicitações', suggestions, amber),",'pdf metric')
s=rep(s,"    final statusColor = _realized(record)","    final kindLabel = _kind(record) == 'EXECUTADA' ? 'MELHORIA EXECUTADA' : 'SOLICITAÇÃO / SUGESTÃO';\n    final statusColor = _realized(record)",'pdf label')
s=rep(s,"""          pw.SizedBox(height: 4),
          pw.Text(
            [sector, location, 'Prioridade ${record.priority}'].where((value) => value.isNotEmpty).join(' • '),""","""          pw.SizedBox(height: 4),
          pw.Text(kindLabel, style: pw.TextStyle(fontSize: 8, fontWeight: pw.FontWeight.bold,
              color: _kind(record) == 'EXECUTADA' ? green : amber)),
          pw.SizedBox(height: 4),
          pw.Text(
            [sector, location, 'Prioridade ${record.priority}'].where((value) => value.isNotEmpty).join(' • '),""",'pdf row')
s=rep(s,"  static bool _realized(SstRecord record) =>","""  static String _kind(SstRecord record) {
    final kind = '${record.payload['recordKind'] ?? ''}'.trim();
    if (kind == 'SOLICITACAO' || kind == 'EXECUTADA') return kind;
    return _realized(record) ? 'EXECUTADA' : 'SOLICITACAO';
  }

  static bool _realized(SstRecord record) =>""",'pdf legacy')
p.write_text(s,encoding='utf-8',newline='\n')
p=root/'pubspec.yaml';s=p.read_text(encoding='utf-8')
before,after={'android':('3.29.108+250','3.29.109+251'),'windows':('3.30.32+219','3.30.33+220')}[platform]
s=rep(s,'version: '+before,'version: '+after,'version')
p.write_text(s,encoding='utf-8',newline='\n')
print('IMPROVEMENT_CLASSIFICATION_OK',platform,after)
