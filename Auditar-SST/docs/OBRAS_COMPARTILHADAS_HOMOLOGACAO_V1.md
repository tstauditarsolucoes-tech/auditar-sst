# Obras compartilhadas — homologação do módulo V1

Estado: preparado na branch feature/client-panel-permissions-v329106; NÃO publicado na Central. PR #15 permanece Draft.

## Escopo separado
- Novo arquivo Apps Script: feature_sources/WorksiteFollowupCloud_v1.gs, com função worksiteFollowupCloudV1_.
- Rota separada no doPost: worksite_followup_sync_v1. Não utiliza device_sync ou as rotas de fotos/relatórios.
- Nova aba isolada: AUDITAR_WORKSITE_FOLLOWUP_V1, na planilha atual de autenticação.
- Acompanhamento identificado pelo ID de cada obra/empresa existente, não pelo nome da construtora.
- Somente colaboradores internos autorizados à empresa/obra conseguem ler e editar. Contas cliente são recusadas.

## Integridade
- Conteúdo: etapa, situação, percentual informado, responsável, datas, observações e até 80 itens do diário.
- Não envia fotos, PDFs, assinaturas ou documentos dos trabalhadores.
- O JSON é dividido em até três células de 28 mil caracteres; capacidade total até 84 mil caracteres.
- Atualizações usam uma revisão incremental. Um conflito retorna WORKSITE_CONFLICT sem sobrescrever dados.
- A aplicação mantém seus dados locais e solicita confirmação antes de aceitar uma versão da Central.
- Antes de aceitar uma versão remota, salva cópia local recuperável pelo botão Restaurar cópia local.

## Ativação SOMENTE em ambiente de homologação
1. Faça backup e registre a versão atual dos arquivos Apps Script e da planilha.
2. Acrescente feature_sources/WorksiteFollowupCloud_v1.gs à Central de teste sob o nome WorksiteFollowupCloud.gs; não substitua os arquivos existentes.
3. No doPost existente, antes do caso offline_knowledge_sync_v1, acrescente somente o ramo abaixo:
   if (request.action === 'worksite_followup_sync_v1') {
     return jsonResponse_(worksiteFollowupCloudV1_(request));
   }
4. Não execute rotinas gerais de inicialização que recriem usuários, chaves ou dados.
5. Execute node tools/test_worksite_followup_cloud_v1.js e confira permissões, conflitos, tamanho e integridade dos dados.
6. Teste com duas contas internas e uma conta cliente sem acesso. Teste obra Quality A e Quality B separadamente.
7. Publique em produção SOMENTE após autorização expressa.

## Aceitação Android/Windows
- Enviar uma obra e receber a mesma em outro aparelho autorizado.
- Editar simultaneamente a mesma revisão; o segundo envio deve acusar conflito.
- Restaurar a versão local após receber dados remotos.
- Trabalhar sem internet, fechar e reabrir: diário, etapa e dados continuam locais; envio é manual.
- Confirmar a estabilidade dos fluxos preexistentes de fotos, PDFs, login, histórico e sincronização SST.
- O compartilhamento da biblioteca técnica online exige outra rota separada, offline_knowledge_sync_v1.

Este pacote não está ativo em produção sem homologação do Apps Script.