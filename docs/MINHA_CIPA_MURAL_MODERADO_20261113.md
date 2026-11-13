# Minha CIPA — Mural de ocorrências (piloto)

**Data:** 13/11/2026. **Branch:** `feature/minha-cipa-mural-moderado-20261113`. **PR:** #67, draft.

## Objetivo
Oferecer uma linha do tempo de ocorrências de prevenção parecida com uma conversa, mas **sem chat público nem grupo de WhatsApp**. Participação educativa e informações limitadas à mesma empresa e ao mesmo mandato ativo da CIPA.

## Experiência do integrante
1. Entrar pelo acesso individual verificado pela Central, abrir **Mural da CIPA** e tocar **Registrar ocorrência**.
2. Informar **local** e **descrição objetiva** e, se desejar, usar **Tirar foto** ou **Galeria**. A imagem é normalizada para JPEG de até **250 KB**. O app alerta para não registrar rostos, documentos, dados de saúde ou se aproximar de perigos.
3. Enviar. O registro fica **Pendente** e visível apenas a quem o enviou e aos moderadores. É possível acompanhar o status e atualizar manualmente a linha do tempo.
4. Após aprovação, membros autorizados da mesma empresa e mandato podem ler e comentar. Cada comentário aguarda moderação; orientações da equipe SST são identificadas de modo distinto.
5. Fotos só são carregadas ao tocar **Ver foto**. Não há URL pública, acesso anônimo nem exportação das imagens para listas de membros.

O mural não é enviado ou consultável offline; não salva em cache local as fotos e mensagens dos colegas. Também não oferece WhatsApp, chat em tempo real, likes nem rankings.

## Moderação e segurança
- **Admin Auditar** ou **TST com delegação específica** para a empresa e o mandato podem revisar posts, fotografias e comentários.
- Podem aprovar, ocultar, orientar, responder e alterar o estado da ocorrência.
- **Resolvido** requer confirmação explícita do responsável; o estado não encerra automaticamente NC, plano de ação, CAT ou documentos.
- As publicações ocultadas deixam de aparecer para colegas, permanecendo disponíveis ao próprio autor e à equipe de moderação.
- O backend valida autenticação, mandato ativo e escopo em cada chamada, com IDs únicos de envio, limites de tamanho, pasta Drive privada e conferência do hash da foto.
- Requer configurar `CIPA_MEMBER_V1_ENABLED=true` e `CIPA_MEMBER_PHOTO_FOLDER_ID` de armazenamento privado **em homologação autorizada**, sem alterar o servidor em uso.

## Delimitações e pendências
- Nesta primeira versão, **uma foto por ocorrência**. O fluxo de fotos **antes/depois vinculadas a uma única ocorrência** ainda não está implementado.
- Não há mensagens WhatsApp nem notificações push.
- A foto serve como referência para avaliação técnica; não é prova de que uma NC foi resolvida ou que a atividade é segura.
- Não publicar sem revisão de privacidade/LGPD, política de retenção e exclusão, regras de moderação, teste de permissões em duas empresas, testagem em Android físico e instalação controlada do backend Apps Script.
- A função está **somente em PR draft de homologação**; nenhuma atualização foi distribuída ou aplicada ao app SST instalado.

## Arquivos principais
- `feature_sources/CipaMemberMuralV1.gs` — autorização, armazenamento privado, moderação e filtro do feed.
- `feature_sources/CipaMemberGatewayV1.gs` — roteamento das novas ações do mural.
- `feature_sources/cipa_member_mural_model_v1.dart` — imagem e dados limitados.
- `feature_sources/cipa_member_mural_panel_v1.dart` — publicação/comentários no app.
- `feature_sources/cipa_mural_moderation_panel_v1.dart` — moderação por ADM e TST delegado.
- `tools/test_cipa_member_gateway_v1.cjs` — testes de isolamento, aprovação, comentários e foto privada.
