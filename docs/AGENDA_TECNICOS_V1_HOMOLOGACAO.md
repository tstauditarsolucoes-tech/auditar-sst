# Agenda de Técnicos V1 — CANDIDATA, NÃO INSTALADA
O arquivo OperationalAgendaV1.gs é um módulo ADDITIVO para homologação. Não executar setupAuditar().
O módulo tem:
- list (ADM lista tudo; técnico enxerga somente as tarefas próprias e de empresas autorizadas)
- create (somente ADM; requer requestId único, title, companyId, technicianId, scheduledAt, dueAt opcional)
- status (técnico atribuído ou ADM; planned -> in_progress, blocked, done; cancelamento somente ADM; motivo obrigatório para bloqueio e conclusão)
- trilha de auditoria separada; não encerra NC nem edita banco/sincronização.
Para funcionar o roteador POST precisa invocar agendaTecnicosV1_(request) apenas quando action=="agenda_tecnicos_v1", tratando o JSON no mesmo padrão das rotas existentes.
A integração da rota DEVE SER HOMOLOGADA com contas ADM e TST, nunca publicada às cegas.
A interface Android/Windows para agenda ainda depende de integração; arquivos de origem são candidatos, não instaladores completos.
Privacidade: comunicar supervisão e retenção à equipe, coletar somente dados necessários, não implementar localização em segundo plano.
