# Auditar — Sistemas SST e EPI

> ## 🚧 VERSÃO ATUAL DO AUDITAR SST
> **Android:** `v3.29.155+297`  
> **Windows:** `v3.30.74+261`  
> **Branch:** `feature/client-panel-permissions-v329106`  
> **PR:** `#15` — permanece em rascunho para revisão; não publicar a Central automaticamente.  
> **Status:** ✅ CI validada — Android e Windows concluídos com sucesso em 03/10/2026. A **Ronda** usa o **Padrão Auditar 3** refinado para ficar o mais próximo possível do PDF técnico de referência, com logo Auditar à esquerda, título/empresa centralizados e somente a logo cadastrada da empresa vistoriada à direita. Não existe logo fixa do Vale do Leite nem repetição da logo do cliente.
>
> O código final é montado pelos workflows atuais a partir da base + patches incrementais.  
> **Não alterar sincronização, banco, autenticação, mídia/fotos ou Central sem autorização expressa.**
>
> Consulte [CURRENT_VERSION.md](CURRENT_VERSION.md) antes de iniciar qualquer alteração. Estado validado atual: commit `f0ae0458f961fd0506fcc303b0972dda3abde22e`, Android run `37135205634`, Windows run `37135205632`.


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
