# Auditar — Sistemas SST e EPI

Repositório de desenvolvimento dos sistemas da Auditar Soluções.

## Produtos

### Auditar SST
Aplicativo Flutter para Android e Windows, com operação offline-first e sincronização pela Central Online.

Principais módulos: empresas, vistorias, não conformidades, planos de ação, trabalhadores, treinamentos, alertas, CIPA, checklists, Rotina SST, Agenda SST, melhorias e indicadores.

**Versão em estabilização:** `3.22.0+80`

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
