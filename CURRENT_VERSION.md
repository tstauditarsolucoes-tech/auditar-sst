# Auditar SST — versão atual

## Linha vigente

| Plataforma | Versão |
|---|---|
| Android | **v3.29.157+299** |
| Windows | **v3.30.76+263** |

**Branch de trabalho:** `feature/client-panel-permissions-v329106`  
**Pull Request:** `#15`  
**Estado:** ✅ CI final validada em 03/10/2026.

## Validação final

- Android: workflow run `37163748477` — **success**.
- Windows: workflow run `37162831904` — **success**.
- APK: `Auditar-SST-v3.29.157-Android.apk` — contido no artefato `Auditar-SST-v3.29.157-Android-Sugestoes-Offline`.
- Windows instalador: `Auditar-SST-Setup-v3.30.76.exe` — contido no artefato `Auditar-SST-v3.30.76-Windows-Sugestoes-Offline`.
- Windows portátil: `Auditar-SST-Windows-v3.30.76-PORTATIL.zip` — contido no artefato `Auditar-SST-v3.30.76-Windows-Sugestoes-Offline`.
- Padrão Auditar 3 validado como modelo principal; na Ronda, o renderer final foi refinado para o PDF técnico de referência, com até dois achados por página, fotos maiores, títulos compactos, conclusão e referências enxutas.
- Logo da direita exclusiva da empresa vistoriada e carregada dinamicamente do cadastro; se não houver logo, o espaço fica vazio. Vale do Leite é apenas empresa de exemplo/referência e não está fixada no modelo.
- `Padrão Auditar` e `Padrão Auditar 2` preservados.
- Biblioteca técnica offline adicionada de forma isolada, com modelos reutilizáveis e memória local de conteúdo aprovado.
- Ao digitar a primeira irregularidade, o app sugere até três modelos semelhantes do histórico/base local e pode preencher os campos técnicos sem internet.
- Conteúdo manual ou vindo da IA somente vira conhecimento reutilizável quando aprovado/salvo; dados de empresa, CNPJ, fotos e localização não entram no modelo geral.
- Núcleo protegido preservado pelas regressões do pipeline; IA, sincronização, banco, autenticação, HTTP, mídia/Drive, Apps Script e renderizadores de relatório permaneceram sem alteração nessa implementação.
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

- Android: workflow run `37163748477` — **success**
- Artefato: `Auditar-SST-v3.29.157-Android-Sugestoes-Offline` (ID `11288857157`)
- Windows: workflow run `37162831904` — **success**
- Artefato: `Auditar-SST-v3.30.76-Windows-Sugestoes-Offline` (ID `11289080276`)
- Commit do recurso validado: `2a7b087a295f958a09123798e88b175d3de46637`
- Correção isolada de empacotamento Android: `6d6c098c0eda23da4c5b8f2adf2da935dd884730`
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
