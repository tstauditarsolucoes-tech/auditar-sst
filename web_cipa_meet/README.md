# Minha CIPA — reuniões Meet e presença (homologação)
 
Módulo servidor de leitura, sem efeito colateral sobre a Central ou o aplicativo instalado. Não é endpoint público; não recebe credenciais do técnico, não grava presença e não assina atas. 
 
## Contrato
- Reunião: modalidade presencial/online/híbrida, janela temporal UTC, link Google Meet, identificador da instância de conferência associado explicitamente pelo organizador, empresa, mandato, convocados.
- A aplicação autenticada precisa implementar loadAuthorizedMeeting(actor, meetingId) consultando armazenamento confiável, checando organizador, empresa, mandato e reunião a cada requisição. Não aceite roster, autorização, identificadores Google verificados ou access token vindos de parâmetros do navegador.
- createGoogleReader recebe access token OAuth do organizador no servidor. Google Meet REST API v2 e escopo https://www.googleapis.com/auth/meetings.space.readonly para salas externas. Habilitar API em projeto Google Cloud e consentimento OAuth; guardar credenciais de atualização cifradas, nunca em Git, navegador, logs ou APK. Não usar AUDITAR_SYNC_KEY.
- collectAttendance consulta salas, instância específica, participantes e sessões; retorna lista provisória, horários UTC, segundos efetivos unidos sem contagem dupla, não identificados separados. Ausência de sessão não comprova ausência total, especialmente em reunião híbrida. Vínculo de conta Google deve ser verificado; nome exibido não basta.
- Instância ainda não vinculada retorna candidatos, não presença. Confirmação administrativa em armazenamento e nova consulta são necessárias.
- Futuro painel administrativo: persistir snapshots por empresa/mandato/reunião, revalidar autorização na escrita, registrar origem e correções manuais, conferir presença e exportar anexo à ata. Não finalizar reunião ou assinatura automaticamente.
- Atualização periódica somente após OAuth + infraestrutura e testes reais. Para entradas/saídas quase em tempo real, Google Workspace Events API (eventos joined/left), Pub/Sub autenticado, deduplicação e renovação da assinatura; consultar API REST para reconciliar. Nenhuma subscription criada nesta revisão.
- Portal do membro: fornecer link apenas para reunião publicada/convocado autorizado via sessão existente. Abrir link em nova aba; clique não registra presença. Não expor lista de outros integrantes ao membro. Avisar sobre coleta de metadados, retenção, acesso restrito e LGPD.
 
## Testes e ativação
node --test web_cipa_meet/attendance.test.mjs
 
Dados fictícios apenas. Necessário instalar e homologar o gateway individual da CIPA (PR 72), vincular contas Google, autorizar organizador e testar duas empresas/mandatos, convidado anônimo, revogação, reconexão, reunião híbrida e expiração OAuth. Não publicar integração real até completar isso. Sem alterações no Apps Script real.
 
Docs: https://developers.google.com/workspace/meet/api/guides/participants
https://developers.google.com/workspace/meet/api/reference/rest/v2/conferenceRecords/list
https://developers.google.com/workspace/events/guides/events-meet
