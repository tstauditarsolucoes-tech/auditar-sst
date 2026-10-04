# Auditar — Sistemas SST e EPI

> ## 🚧 VERSÃO ATUAL DO AUDITAR SST
> **Android:** `v3.29.157+299`  
> **Windows:** `v3.30.76+263`  
> **Branch:** `feature/client-panel-permissions-v329106`  
> **PR:** `#15` — permanece em rascunho para revisão; não publicar a Central automaticamente.  
> **Status:** ✅ CI validada — Android e Windows concluídos com sucesso em 03/10/2026. A linha atual mantém a **Ronda** no **Padrão Auditar 3** e acrescenta uma **biblioteca técnica offline** com sugestões automáticas a partir da primeira irregularidade digitada. O recurso é local e complementar: não substitui IA, preenchimento manual nem funções existentes.
>
> O código final é montado pelos workflows atuais a partir da base + patches incrementais.  
> **Regra permanente:** não alterar, substituir ou refatorar funcionalidades que já estejam funcionando sem autorização expressa. Toda melhoria deve ser aditiva, isolada e de mínimo impacto. Preservar especialmente sincronização, banco, autenticação, IA, mídia/fotos, Drive e Central.
>
> Consulte [CURRENT_VERSION.md](CURRENT_VERSION.md) antes de iniciar qualquer alteração. Estado validado atual: recurso no commit `2a7b087a295f958a09123798e88b175d3de46637`, correção isolada de empacotamento Android no commit `6d6c098c0eda23da4c5b8f2adf2da935dd884730`, Android run `37163748477`, Windows run `37162831904`.


Repositório de desenvolvimento dos sistemas da Auditar Soluções.

## Produtos

### Auditar SST
Aplicativo Flutter para Android e Windows, com operação offline-first e sincronização pela Central Online.

Principais módulos: empresas, vistorias, não conformidades, planos de ação, trabalhadores, treinamentos, alertas, CIPA, checklists, Rotina SST, Agenda SST, melhorias e indicadores.

**Linha histórica de estabilização:** `3.22.0+80` (não representa a versão atual)

### Gestão EPI
Os módulos EPI permanecem isolados nas pastas `auditar-epi*` e `gestao-epi-master*`. Alterações nesses módulos não devem modificar o build do Auditar SST.

## Fonte canônica do Auditar SST

Durante a estabilização 3.22, o build ainda é montado em três etapas:

1. `Auditar_SST_v1.5_dashboard_completo.zip` — base legada temporária;
2. `source_overrides/Auditar_SST_v1_5_dashboard/` — fonte atualizado e correções permanentes;
3. `tools/` — transformações determinísticas usadas enquanto a base legada é eliminada.

Não criar novos arquivos `completo (1).zip`, `completo (2).zip`, `CORRIGIDO_FINAL.zip` ou semelhantes. A versão do produto deve ser alterada somente em `pubspec.yaml`.

## Builds oficiais

- Android: `.github/workflows/build-apk.yml`
- Windows: `.github/workflows/build-windows.yml`

Os dois pipelines executam análise estática antes de compilar.

O Android gera APK release universal e APKs separados por arquitetura. Para distribuição comercial/Play Store, deve ser configurada uma chave Android permanente nos segredos do repositório.

O Windows gera pacote portátil e instalador `Setup.exe`.

## Regra de publicação

Toda mudança estrutural deve passar por branch/PR e pelos builds de validação antes de entrar em `main`.

Consulte `docs/AUDITAR_SST_V3_22.md` para o escopo da estabilização profissional.
