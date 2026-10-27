# Auditar — Sistemas SST e EPI

> **Organização SST (27/10/2026):** fontes, bases, integrações e documentos do Auditar SST estão em [`Auditar-SST/`](Auditar-SST/README.md). O Gestão EPI permanece em seus diretórios próprios. Os workflows ativos ficam em `.github/workflows/` por exigência do GitHub e remontam o layout temporariamente somente durante a compilação.
>
> **Para implantação web/servidor próprio:** leia o [guia para o programador](Auditar-SST/docs/GUIA_PROGRAMADOR_WEB_SERVIDOR_PROPRIO_20261027.md). O aplicativo Android/Windows e o Painel Apps Script não são automaticamente uma aplicação web pronta.


> ## Versões, CI e regras de segurança
> A fonte de verdade para as versões **Android e Windows**, commits e estado de validação é [CURRENT_VERSION.md](Auditar-SST/CURRENT_VERSION.md). Não use versões antigas copiadas deste README.
>
> **Auditar SST:** Flutter Android e Windows. Código final montado por workflows a partir da base e dos patches incrementais; consultar o CI da branch antes de instalar.
>
> **PR #15:** permanece em **Draft**, sem merge; não fazer deploy/publicação da Central, GS ou Painel do Cliente sem autorização expressa.
>
> **Regra de segurança:** preservar login, banco, sincronização, mídia/fotos, Drive, IA, históricos, acesso multiempresa e recursos já existentes. Corrigir de modo aditivo, testado e isolado. Compilação aprovada não substitui homologação em aparelhos reais.
>
> **CI da branch:** [Android](https://github.com/tstauditarsolucoes-tech/auditar-sst/actions/workflows/build-v329106-client-portal.yml) • [Windows](https://github.com/tstauditarsolucoes-tech/auditar-sst/actions/workflows/build-v33030-client-portal.yml).
>
> **Auditoria de navegação e duplicidades:** [critérios e pendências](Auditar-SST/docs/AUDITORIA_SST_SEGURANCA_E_NAVEGACAO_20261013.md).

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

1. `Auditar-SST/Auditar_SST_v1.5_dashboard_completo.zip` — base legada temporária;
2. `Auditar-SST/source_overrides/Auditar_SST_v1_5_dashboard/` — fonte atualizado e correções permanentes;
3. `Auditar-SST/tools/` — transformações determinísticas usadas enquanto a base legada é eliminada.

Não criar novos arquivos `completo (1).zip`, `completo (2).zip`, `CORRIGIDO_FINAL.zip` ou semelhantes. A versão do produto deve ser alterada somente em `pubspec.yaml`.

## Builds oficiais

- Android SST da branch: `.github/workflows/build-v329106-client-portal.yml`
- Windows SST da branch: `.github/workflows/build-v33030-client-portal.yml`
- Os workflows legados continuam no histórico e não representam necessariamente os últimos builds do Auditar SST.

Os dois pipelines executam análise estática antes de compilar.

O Android gera APK release universal e APKs separados por arquitetura. Para distribuição comercial/Play Store, deve ser configurada uma chave Android permanente nos segredos do repositório.

O Windows gera pacote portátil e instalador `Setup.exe`.

## Regra de publicação

Toda mudança estrutural deve passar por branch/PR e pelos builds de validação antes de entrar em `main`.

Consulte `docs/AUDITAR_SST_V3_22.md` para o escopo da estabilização profissional.
