enum FieldVisitPriorityLevel { critical, high, attention, info, ok }

class FieldVisitPriorityItem {
  const FieldVisitPriorityItem({
    required this.code,
    required this.title,
    required this.detail,
    required this.level,
  });

  final String code;
  final String title;
  final String detail;
  final FieldVisitPriorityLevel level;
}

class FieldOperationalPriorityService {
  const FieldOperationalPriorityService._();

  static List<FieldVisitPriorityItem> build({
    required int highCriticalOpen,
    required int overdueActions,
    required int recurrenceGroups,
    required int expiredTrainings,
    required int awaitingEvidence,
    required int openNonConformities,
    required int pendingSync,
    int? daysSinceLastInspection,
  }) {
    final items = <FieldVisitPriorityItem>[];

    if (highCriticalOpen > 0) {
      items.add(FieldVisitPriorityItem(
        code: 'critical_nc',
        title: 'Revisar NCs de prioridade alta/crítica',
        detail: '$highCriticalOpen registro(s) exigem atenção prioritária.',
        level: FieldVisitPriorityLevel.critical,
      ));
    }
    if (overdueActions > 0) {
      items.add(FieldVisitPriorityItem(
        code: 'overdue_actions',
        title: 'Cobrar ações vencidas',
        detail: '$overdueActions ação(ões) estão com prazo vencido.',
        level: FieldVisitPriorityLevel.high,
      ));
    }
    if (recurrenceGroups > 0) {
      items.add(FieldVisitPriorityItem(
        code: 'recurrence',
        title: 'Verificar possíveis recorrências',
        detail: '$recurrenceGroups grupo(s) semelhante(s) foram encontrados no histórico.',
        level: FieldVisitPriorityLevel.high,
      ));
    }
    if (expiredTrainings > 0) {
      items.add(FieldVisitPriorityItem(
        code: 'training',
        title: 'Conferir treinamentos vencidos',
        detail: '$expiredTrainings treinamento(s) estão vencidos.',
        level: FieldVisitPriorityLevel.attention,
      ));
    }
    if (awaitingEvidence > 0) {
      items.add(FieldVisitPriorityItem(
        code: 'evidence',
        title: 'Coletar evidência da correção',
        detail: '$awaitingEvidence registro(s) têm foto inicial e aguardam evidência posterior.',
        level: FieldVisitPriorityLevel.attention,
      ));
    }
    if (openNonConformities > 0 && highCriticalOpen == 0) {
      items.add(FieldVisitPriorityItem(
        code: 'open_nc',
        title: 'Revisar não conformidades abertas',
        detail: '$openNonConformities ocorrência(s) continuam abertas.',
        level: FieldVisitPriorityLevel.attention,
      ));
    }
    if (daysSinceLastInspection == null || daysSinceLastInspection >= 30) {
      items.add(FieldVisitPriorityItem(
        code: 'inspection_due',
        title: 'Programar nova vistoria',
        detail: daysSinceLastInspection == null
            ? 'Nenhuma vistoria anterior foi localizada neste recorte.'
            : 'Última vistoria identificada há $daysSinceLastInspection dia(s).',
        level: FieldVisitPriorityLevel.info,
      ));
    }
    if (pendingSync > 0) {
      items.add(FieldVisitPriorityItem(
        code: 'sync',
        title: 'Conferir itens aguardando sincronização',
        detail: '$pendingSync item(ns) ainda aguardam envio deste aparelho.',
        level: FieldVisitPriorityLevel.info,
      ));
    }

    if (items.isEmpty) {
      return const [
        FieldVisitPriorityItem(
          code: 'ok',
          title: 'Sem prioridade operacional imediata',
          detail: 'Os indicadores locais não apontaram pendência crítica para esta visita.',
          level: FieldVisitPriorityLevel.ok,
        ),
      ];
    }
    return items;
  }
}
