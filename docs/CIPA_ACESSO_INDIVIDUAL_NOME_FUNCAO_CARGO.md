# CIPA — Identificação individual por nome, função na CIPA e cargo na empresa

## Escopo implementado no código Android de homologação

- Na aba **Membros** da gestão existente, o título passa a usar a função
  `CipaMemberIdentityLabel.displayName`, reaproveitando o campo persistido
  `cipaRole`, **sem criar outro cadastro ou alterar o registro original**.
- Exemplo: `Maria Silva — Vice-presidente da CIPA`.
- Funções reconhecidas pelo modelo existente: Presidente, Vice-presidente,
  Titular, Suplente, Secretário e Membro designado.
- O cabeçalho `CipaMemberAccessHeader`, preparado para o acesso pessoal futuro,
  apresenta o nome e a função, seguido de `Cargo na empresa` (se conhecido) e
  `Representação` (Empregador, Empregados ou Designado).
- O cargo profissional é um campo **opcional e separado** da função na CIPA.
  O registro atual `CIPA_MEMBRO` não persiste cargo profissional; o futuro
  endpoint só poderá fornecê-lo após verificar o cadastro do trabalhador.
  Ausência não deve ser completada com exemplo fictício.
- Nome e função devem ser obtidos do vínculo de membro ativo no mandato,
  **não de textos enviados pela interface de login**.

## O que foi validado por testes isolados

- Título com função da CIPA, sem misturar com cargo profissional.
- Nenhum rótulo de função arbitrária é aceito como cargo da comissão.
- Contrato de perfil verifica igualdade de IDs de conta, empresa, mandato e
  membro; exige cadastro, conta e mandato ativos.
- Testes para revogação e tentativas de usar registro de outra pessoa,
  outra empresa e outro mandato.
- Instalador só modifica o título da tela CIPA e adiciona componentes locais;
  verificação SHA-256 de todos os outros arquivos em lib e Apps Script.
- Reinstalação duplicada bloqueada.

## Pendência bloqueante: login individual real

Não houve mudança no backend protegido: `auth_service.dart`, `MultiUser.gs`,
`Code.gs`, `device_sync_service.dart`, banco, mídia e Central Online.
Atualmente esses componentes **não têm papel `membro_cipa` com autorização
servidor-side para dados individuais**. Não criar conta improvisada no perfil
`tecnico`, `admin` ou `cliente`.

Antes de tornar o cabeçalho de acesso uma tela de login utilizável:

1. Autorizar e revisar separadamente o backend **real implantado**, com backup,
   controle de versão e plano de reversão.
2. Implementar papel `membro_cipa`, vínculo por `authUserId`,
   `companyId`, `mandateId`, `memberId` e `workerId`, sessão própria,
   revogação imediata, trilha de auditoria e validação a cada requisição.
3. Expor somente convocações e ações permitidas, observações, pedidos de
   apoio e informes. Impedir acesso a outras empresas, mudança de mandato
   sem nova autorização, relatórios médicos, dados administrativos, alteração
   de atas assinadas e validação técnica de NC.
4. Definir tratamento offline seguro: sem sincronização geral do banco,
   sem reaproveitar cache de técnico/ADM e sem expor a chave de sincronização.
5. Homologar em duas empresas, dois mandatos e com dois membros distintos;
   testar revogação de acesso, dispositivos antigos e transferência de função.
6. Só então instalar APK assinado com a chave já usada em produção.

**Situação:** apresentação local preparada e testes isolados aprovados.
Acesso individual real ainda não habilitado.
