# Gestão EPI — Auditoria de regressões v3.8.5 (22/10/2026)

## Escopo e evidência
Comparação de código das branches `feature/gestao-epi-worker-portal-v450` e `feature/gestao-epi-android-restore-audit-v385`, inspeção dos módulos JavaScript/HTML do Android e validações do CI. A auditoria **não** equivale a teste físico, verificação de dados em produção ou fiscalização de conformidade jurídica.

## Defeitos confirmados e corrigidos nesta candidata
1. **Ficha não abre:** `worker-sheets-v382.js` fazia `querySelector(...).forEach()` em mais de um ponto (navegação entre telas e marcação da aba). Corrigido para `querySelectorAll`, mantendo Ficha e Histórico 360° separados.
2. **Alterar vínculo desapareceu:** `worker-link.js` existia mas não estava referenciado em `index.html`. Reintegrado com badge de vínculo, edição e cadastro rápido. Para evitar atribuir alteração a homônimo, vincula pelo ID e, ao criar trabalhador, identifica novo ID em vez de selecionar por nome existente.
3. **Cartões sem ações acessíveis:** módulo visual `restore-worker-actions-v385.js` destaca e mantém acessíveis Ficha completa, Resumo 360°, biometria e Portal; Excluir permanece em Mais opções. Não executa exclusão, cadastro nem gravação por conta própria.
4. **Cache offline potencialmente antigo:** Service Worker ainda usava `gestao-epi-v322-shell` e sua lista não incluía os módulos de Fichas e outros introduzidos depois. Atualizado para v385 com recursos novos. O fetch same-origin continua network-first.
5. **Permissões de edição de vínculo:** botões de edição e cadastro rápido agora são condicionados aos papéis `admin` e `campo`. Isso é defesa na interface, **não** substitui autorização no backend.

## Verificações de preservação do núcleo (comparação de SHA de blob Git)
Sem alteração frente à base v4.5: `app.js`, `auth.js`, `cloud-sync.js`, `biometric-face.js`, `biometric-crypto-v1.js`, `company-branding.js` (incluindo `logoSig`), `ca-center-v330.js`, `worker-portal-ops-v370.js` e `epi-flow-v350.js`. O CI v385 inclui verificações rígidas de integridade para sete arquivos críticos. Isso prova igualdade de código desses arquivos, **não** funcionamento físico.

## Atenção / não alterar automaticamente
- **Estoque negativo** observado nas fotos do usuário: conferir movimentos, compras, almoxarifado e entregas antes de correção. Nenhuma baixa, ajuste, transferência ou recálculo foi realizado nesta branch.
- `stock.js`, `invoice-epi-ai-v350.js` e `epi-flow-enhancements-v360.js` mudaram em relação à base v4.5. As mudanças de rastreabilidade/estoque/NF devem ser testadas separadamente.
- Alguns arquivos adicionais existentes (como `facial-assist.js`, `return-epi.js` e `holdings-replacements.js`) não são importados diretamente pela página atual; **não** foram adicionados indiscriminadamente, pois poderiam duplicar fluxos já assumidos pelos módulos de biometria e entregas.
- Perfis adaptativos ocultam módulos no cliente, mas autorização sensível deve ser checada no backend. Não afirmar que ocultar um botão é controle de acesso no servidor.
- A assinatura APK de depuração gerada pelo CI pode diferir da versão instalada. Não desinstalar o Android atual sem backup verificável e sincronização confirmada.

## Roteiro mínimo de teste no dispositivo
1. Com sessão ADM: Colaboradores → cartão apresenta Ficha completa, Resumo 360°, Rosto cadastrado/Cadastrar rosto, Portal, e Alterar vínculo; botão Excluir apenas em Mais opções.
2. Abrir ficha completa; conferir nome/empresa/CPF, histórico, voltar à lista, imprimir, compartilhar PDF; conferir PDF sem páginas vazias.
3. Abrir Resumo 360°, depois Ficha completa, sem trocar de trabalhador.
4. Portal → abrir navegador / compartilhar / copiar link, com GS efetivamente instalado e token válido.
5. Em usuário com papel restrito, confirmar que a interface não libera alteração indevida de vínculo; conferir também autorização no servidor.
6. Conferir manutenção de assinaturas/biometria e o histórico em aparelho e PC; sincronização em ambos os sentidos.
7. Verificar estoque negativo e almoxarifado, sem ajustar automaticamente.
8. Conferir modo offline e online, CA/NF, comprovantes de entregas antigas, QR e atualizações de perfil adaptativo.

## Publicação
Somente branch isolada; sem merge na `main`, sem GS implantado e sem `CommercialExtensions.gs`. A v3.8.5 não pode ser declarada estável antes de teste físico e assinatura compatível.
