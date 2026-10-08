# Auditar SST — versão atual

## Linha vigente

| Plataforma | Versão | CI |
|---|---|---|
| Android | **v3.29.173** | run `37756842635` — success |
| Windows | **v3.30.96** | run `37756842584` — success |

Branch: `feature/client-panel-permissions-v329106`. PR #15 permanece **Draft**, sem merge.
Commit compilado e validado: `77d3f6f95ca06f195fb6cb466c488788b04db085`.
Conferência de CI e artefatos: 08/10/2026.

## Grupos de empresas

- Cadastro com vínculo opcional a grupo; empresas sem grupo continuam disponíveis.
- Criação, movimentação, renomeação, união e remoção de grupos, preservando empresas e registros SST.
- Nome curto de unidade, busca, favoritos, recentes e memória de filtros.
- Resumo gerencial por grupo no PC.
- Canal separado para compartilhar grupos, tipo e nome curto entre Android e Windows.
- Favoritos, recentes e filtros permanecem pessoais por aparelho/usuário.
- **Compartilhamento depende da implantação autorizada de CompanyGroupsSync.gs e da rota na Central. Essa implantação NÃO foi realizada.**
- Instruções: `docs/GRUPOS_COMPARTILHADOS_IMPLANTACAO.md`.

## Pacotes conferidos

- APK: `Auditar-SST-v3.29.173-Android.apk`, artefato `11541077753`.
- Instalador: `Auditar-SST-Setup-v3.30.96.exe`.
- Portátil: `Auditar-SST-Windows-v3.30.96-PORTATIL.zip`, artefato Windows `11541741652`.
- Testes, análise, regressões e compilação concluídos nos dois pipelines.
- Android compilado com verificação da chave permanente e do identificador do pacote.
- SHA-256 dos ZIPs de artefatos conferido contra o GitHub; integridade dos ZIPs verificada.
- **Pendente:** validação física no Android e Windows e homologação do compartilhamento na Central real.
- Não publicar a Central ou fazer merge automaticamente.

## Registro anterior

O conteúdo abaixo é histórico da base v3.29.170 / v3.30.90, não o estado vigente.


## Linha vigente

| Plataforma | Versão |
|---|---|
| Android | **v3.29.170+312** |
| Windows | **v3.30.90+277** |

**Branch de trabalho:** `feature/client-panel-permissions-v329106`  
**Pull Request:** `#15`  
**Estado:** ✅ CI final validada em 05/10/2026.

## Validação final

- Android: workflow run `37338538591` — **success**.
- Windows: workflow run `37379804638` — **success**.
- APK: `Auditar-SST-v3.29.170-Android.apk` — contido no artefato `Auditar-SST-v3.29.170-Android-Mobile-360-412`.
- Windows instalador: `Auditar-SST-Setup-v3.30.90.exe` — contido no artefato `Auditar-SST-v3.30.90-Windows-Central-Gestao-Desktop`.
- Windows portátil: `Auditar-SST-Windows-v3.30.90-PORTATIL.zip` — contido no artefato `Auditar-SST-v3.30.90-Windows-Central-Gestao-Desktop`.
- Padrão Auditar 3 validado como modelo principal; na Ronda, o renderer final foi refinado para o PDF técnico de referência, com até dois achados por página, fotos maiores, títulos compactos, conclusão e referências enxutas.
- Logo da direita exclusiva da empresa vistoriada e carregada dinamicamente do cadastro; se não houver logo, o espaço fica vazio. Vale do Leite é apenas empresa de exemplo/referência e não está fixada no modelo.
- `Padrão Auditar` e `Padrão Auditar 2` preservados.
- Biblioteca técnica offline adicionada de forma isolada, com modelos reutilizáveis e memória local de conteúdo aprovado.
- Ao digitar a primeira irregularidade, o app sugere até três modelos semelhantes do histórico/base local e pode preencher os campos técnicos sem internet.
- Relevância das sugestões offline refinada: “Botão de emergência não funcionou” prioriza o modelo de botão/parada de emergência e evita sugestões sem relação, como extintores; o bloco visual mostra as sugestões mais próximas de forma compacta.
- Biblioteca SST offline ampliada para mais de 30 modelos recorrentes, cobrindo máquinas, elétrica, incêndio, EPI, trabalho em altura, andaimes, escadas, inflamáveis, químicos, ruído, calor, poeira, ergonomia, movimentação/empilhamento, circulação, condições sanitárias, sinalização, espaços confinados e equipamentos pressurizados.
- O assistente sem IA agora apresenta categoria técnica, risco, consequência possível, NRs sugeridas com descrição, matriz P×S editável, ação corretiva, responsável, prazo e evidência recomendada. Risco e consequência podem preencher os campos existentes somente quando ainda estão vazios, preservando o texto do técnico.
- A mesma biblioteca local passou a funcionar também no modo Ronda: a descrição digitada pode sugerir modelos do histórico e reaproveitar título, risco, consequência, recomendação e prioridade sem depender da IA.
- Conclusão local sem IA adicionada de forma complementar na Ronda e na Vistoria: o app monta um texto a partir dos registros já preenchidos, permite revisão/edição humana e salva para uso no relatório sem chamada de internet ou IA.
- As rotas existentes de conclusão/revisão por IA permanecem disponíveis separadamente e não foram alteradas.
- No resumo visual curto do checklist, Risco e Classificação/Prioridade permanecem ocultos; os campos e dados técnicos continuam preservados no registro.
- Conteúdo manual ou vindo da IA somente vira conhecimento reutilizável quando aprovado/salvo; dados de empresa, CNPJ, fotos e localização não entram no modelo geral.
- Núcleo protegido preservado pelas regressões do pipeline; IA, sincronização, banco, autenticação, HTTP, mídia/Drive, Apps Script e renderizadores de relatório permaneceram sem alteração nessa implementação.
- Histórico anual da inspeção mensal de extintores ajustado para telas estreitas: 3 colunas até 412 px e 4 colunas acima disso, preservando os dados e o fluxo existente.
- Windows ganhou uma Central de Gestão desktop específica para larguras a partir de 1000 px, reaproveitando a tela de controle operacional e os dados já existentes.
- A Central desktop reúne empresa selecionada, indicadores, tabela somente leitura de pendências com atrasos primeiro, prioridades de acompanhamento, resumo local para decisão, evidências Antes × Depois, recorrências e atalhos para plano de ação, NCs, treinamentos e nova vistoria.
- A experiência compacta abaixo de 1000 px foi preservada; banco, sincronização, autenticação, HTTP, mídia/Drive, IA, Apps Script e renderizadores PDF não foram alterados por esta etapa.
- A validação de CI não substitui o teste físico do APK e do executável em aparelho/PC real.

## Padrão Auditar 3 — modelo principal

- Modelo principal dos relatórios de vistoria técnica.
- Layout fiel ao PDF aprovado: logo Auditar à esquerda, empresa/título ao centro e somente a logo cadastrada do cliente à direita.
- Se a empresa não tiver logo cadastrada, o lado direito permanece vazio; não há logo fixa de cliente e a logo da empresa não é repetida.
- Identificação com razão social, CNPJ, localidade, data e endereço completo.
- Achados em duas colunas: evidência fotográfica à esquerda; Local, Situação, Risco, Correção e Prioridade à direita.
- Fechamento com conclusão, referências gerais e Técnico em Segurança do Trabalho.
- `Padrão Auditar` e `Padrão Auditar 2` permanecem disponíveis como alternativas.

## Escopo acumulado da linha atual

- Central Inteligente de Campo e busca global.
- Evidências Antes × Depois e alerta conservador de recorrências.
- Relatórios com progresso de geração e modelos gerenciais.
- Ronda com IA, rascunhos, fotos e recuperação.
- Treinamentos com fotos, fichas físicas, assinaturas sequenciais, pesquisa e filtros.
- Visão unificada de DDS, treinamentos e integrações.
- CIPA com mandato, membros, reuniões, atas, ações, eleição, treinamentos, documentos, histórico e atalhos de pendências.
- Central Administrativa Auditar para conta ADM.
- Painel do Cliente com múltiplos acessos individuais e permissões.
- Inspeção mensal de extintores.
- Android com chave permanente de assinatura.
- Windows com instalador e versão portátil.
- Biblioteca de conhecimento técnico offline e sugestões automáticas por irregularidade digitada.

## Builds validados

- Android: workflow run `37338538591` — **success**
- Artefato: `Auditar-SST-v3.29.170-Android-Mobile-360-412` (ID `11359050056`)
- Windows: workflow run `37379804638` — **success**
- Artefato: `Auditar-SST-v3.30.90-Windows-Central-Gestao-Desktop` (ID `11375302019`)
- Commit da integração da Ronda offline: `544e490d2c82342e6d839b74a1ddb5fa9bf41f1b`
- Workflow Android v3.29.160 validado no commit: `df1007e22a47705cf0d58f169f9dea1a2b08554d`
- Workflow Windows v3.30.79 validado no commit: `82b61f5b1b2af61cfe46e275139dd9ca23562776`
- Commit final da biblioteca SST offline completa: `b54412d1678a31c5375d9cab2188e9b640240b94`.
- Alterações posteriores nesses arquivos de versão/README são somente documentação.

## Núcleo protegido

**Regra permanente do projeto:** não alterar, substituir ou refatorar funcionalidades que já estejam funcionando sem autorização expressa. Toda melhoria nova deve ser aditiva, isolada e de mínimo impacto.

Não alterar sem autorização expressa:

```text
lib/database.dart
lib/services/device_sync_service.dart
lib/services/apps_script_http.dart
lib/services/sync_coordinator.dart
lib/services/auth_service.dart
lib/services/drive_service.dart
lib/services/media_sync_service.dart
lib/services/ai_assistant_service.dart
painel_web_google_apps_script/Code.gs
painel_web_google_apps_script/MultiUser.gs
painel_web_google_apps_script/ClientPortal.gs
painel_web_google_apps_script/ClientPortal.html
painel_web_google_apps_script/ReportEmail.gs
```

As melhorias devem ser aditivas, isoladas e validadas por regressão antes do build.

## Workflows oficiais desta linha

- Android: `.github/workflows/build-v329106-client-portal.yml`
- Windows: `.github/workflows/build-v33030-client-portal.yml`

> Este arquivo deve ser atualizado sempre que a versão oficial da branch mudar.
