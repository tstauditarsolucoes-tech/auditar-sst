# Gestão EPI — v3.8.1 (candidata) — 21/10/2026

## Escopo efetivamente implementado
- Central de comprovantes filtrável no Android e Windows, abrindo os comprovantes já persistidos.
- Entrega Expressa que pré-seleciona trabalhador e delega a entrega ao fluxo existente.
- Pré-conferência não bloqueante de EPIs repetidos, CA ausente, quantidade e seleção de trabalhador.
- Informação prudente de conectividade; não apresenta internet ativa como confirmação de sincronização.
- Windows: evitar menu duplicado; corrigir texto da versão e comprovante de biometria (sem imagem inválida).
- Teste automático somente de sintaxe, bootstrap e ausência de gravação direta no novo módulo.

## Testes físicos obrigatórios antes de aprovar
1. Backup/sincronização confirmada dos registros atuais; não desinstalar Android.
2. Conferir assinatura do APK: versão candidata precisa compartilhar a assinatura da instalada para atualização por cima. Se não coincidir, NÃO substituir ou desinstalar app em produção.
3. Android: abrir uma entrega antiga com assinatura e uma biométrica; validar CA, empresa, foto/assinatura quando aplicável, ID/hash, rastreabilidade e PDF não branco.
4. Android: Imprimir/Salvar PDF e Compartilhar PDF pelo WhatsApp; abrir documento compartilhado e validar todas as páginas.
5. Android: leitura QR pela câmera e fallback manual sem acionar exclusão.
6. Android e PC: Entrega Expressa pré-seleciona empresa/trabalhador corretos e só baixa estoque após salvar pelo fluxo convencional.
7. Android e PC: Central consulta comprovantes do mesmo tenant, filtra empresa/período/evidência e abre documento correto.
8. Confirmar biometria, assinatura, login offline e online sem regressão; a UI nova não os substitui.
9. Multiestoque: transferência entre almoxarifados não altera saldo total; entrega baixa uma única vez.
10. PC: instalador e portátil com UI própria; checar resolução 1366x768 e 1920x1080, modo Confortável e Grande.
11. Portal do Trabalhador: solicitações e comprovantes; não implantar GS 4.6 sem validação do efetivamente instalado.
12. Sincronização Android → backend → Windows → Android: conferir mesmo registro, ID, evidência e movimentação, sem duplicação.

## Ainda NÃO considerado concluído
- Autorização de módulos/permissões no servidor (atualmente a v3.8 esconde/limita funcionalidades pela UI; não é autorização de backend).
- Testes físicos reais em aparelhos Android e PC, assinaturas dos binários e testes de integração com GS efetivamente publicado.
- Novos bloqueios transacionais para recolhimentos/lotes vencidos: devem ser implementados em versão própria e submetidos a ensaios de saldo histórico.

## Restrições
Não fazer merge em main, não publicar GS, não reintroduzir CommercialExtensions.gs, não alterar login/sincronização/biometria/estoque legado sem testes autorizados.
