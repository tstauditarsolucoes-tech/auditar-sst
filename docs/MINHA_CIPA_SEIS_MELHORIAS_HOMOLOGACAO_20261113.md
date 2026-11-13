# Minha CIPA — seis melhorias integradas (homologação)

**Emissão:** 13/11/2026. **PR draft:** #68, em sequência às PRs anteriores de Minha CIPA. **Público:** equipe interna de SST, Auditar Soluções e desenvolvedores. Nenhum arquivo instalado foi modificado, mesclado ou distribuído.

## 1. Perfil com foto
- A pessoa entra com o e-mail e código validado pela Central; a foto é opcional.
- Pode escolher foto pela câmera ou galeria, trocar, ou remover após confirmação.
- Foto pessoal é guardada em pasta Drive **privada**, separada das fotos de inspeção, vinculada a conta, empresa, mandato e membro. Resposta binária só à conta autorizada ou administrador validado; jamais adicionada às listagens públicas.
- Imagem é convertida para JPG até **150 KB**, recorte central quadrado, sem metadados de origem. Não faz reconhecimento facial, crachá, confirmação de presença ou controle de ponto.
- Depende da pasta privada `CIPA_MEMBER_PHOTO_FOLDER_ID` em ambiente de homologação e política de retenção/LGPD.

## 2. O que preciso fazer hoje?
- Agenda personalizada calculada dos dados devolvidos ao membro: próxima reunião, tarefas com prazo próximo ou vencido, vistorias programadas e resposta técnica ainda não lida.
- Itens direcionam à seção correspondente. Os dados recebidos são filtrados por empresa, mandato, membro e situação, inclusive no app.
- Em modo offline exibe alerta de desatualização; o cache do sistema fica protegido pela regra existente de **PIN e validade de 24 h**.

## 3. Foto antes/depois no mural
- Autor do relato aprovado pode acrescentar **uma foto posterior**. O arquivo é enviado como JPEG de até **250 KB** à pasta privada.
- Foto posterior fica pendente até moderação ADM ou TST delegado. Outros membros não podem vê-la antes da aprovação.
- A aprovação da foto não altera automaticamente o status do registro; **Resolvido** continua exigindo confirmação explícita do responsável, sem finalizar não conformidade ou CAT.
- Sem transmissão de URL pública, lista com base64 ou acesso de outro mandato.

## 4. Minutas de ata na Central
- Guia de reunião produz **RASCUNHO EDUCATIVO — NÃO É ATA OFICIAL** e permite, quando online, selecionar uma reunião realmente vinculada ao integrante.
- O usuário confirma antes de encaminhar à Central; o sistema valida sessão, empresa, mandato, reunião e identificador para evitar duplicidade.
- Central ADM e TST autorizado podem marcar **Em revisão**, **Devolvida**, **Pronta para formalização** e escrever orientação. O integrante consulta apenas suas próprias minutas e resultados.
- **Não gera ata oficial, assinaturas, lista de presença, publicação ou cumprimento automático da NR-5**. Formalização e assinaturas reais continuam sendo procedimento próprio e devem ser validados antes de publicar.

## 5. Avisos internos
- Melhorados os avisos da tela inicial: **reunião hoje**, reunião amanhã, ações vencidas e a vencer em três dias, vistorias programadas e respostas técnicas pendentes de leitura.
- Nenhuma notificação push do Android, WhatsApp, dados sensíveis no bloqueio de tela ou alertas externos foram implementados nesta etapa.
- Avisos não certificam leitura oficial ou presença.

## 6. Offline e segurança
- O mural dos colegas continua **indisponível offline**. Só a própria ocorrência não enviada pode ser salva no dispositivo.
- Até **10 rascunhos** cifrados AES-GCM em diretório privado; chave independente via `flutter_secure_storage`; identificador/empresa/mandato/membro definem escopo do arquivo e chave.
- Cada rascunho guarda local, relato, horário e até uma foto JPEG reduzida, com validade de leitura de até **7 dias**. Arquivos temporários cifrados são recuperáveis após interrupção; corrupção não é silenciosamente descartada.
- Botão de sincronização exige sessão autenticada, consulta novamente a identidade do servidor, exibe resumo e pede **confirmação manual**. Cada registro mantém ID persistente para reenvio idempotente; arquivo é excluído **somente após resposta confirmada**.
- Na saída da conta o usuário é avisado se há rascunhos e pode cancelar; logout confirmado apaga rascunhos e chave local do vínculo. Revogação de sessão força limpeza.

## Segurança, implantação e pendências

1. Manter feature flag `CIPA_MEMBER_V1_ENABLED` **desativada em produção** até implantação formal autorizada.
2. Aplicar `tools/patch_cipa_member_gateway_experimental_v1.py` **somente em cópia de homologação** com backend Apps Script e backup. O instalador agora inclui módulos específicos de perfil, mural depois e minutas.
3. Validar armazenamento Drive, escopos de ADM/TST, LGPD, consentimento, exclusão e retenção, limites de tamanho, comportamento sem rede, revogação e troca de mandato.
4. Testar em aparelho Android real câmera/galeria, desempenho, gravação de rascunhos, retomada do app, PIN e sincronização.
5. Conferir a interoperabilidade da revisão da minuta com a documentação e o procedimento oficial de assinaturas da comissão; **esta PR não implementa assinatura**.
6. Somente depois destes controles decidir sobre merge e publicação da versão instalável.

**Verificação automática:** pipeline `.github/workflows/validate-cipa-central-reviews.yml` com jobs backend Apps Script, UI de gestão, API do membro, UI do membro e app Android isolado. Não testar com dados reais neste MVP.
