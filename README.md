# Auditar — Sistemas SST e EPI

> ## 🚧 VERSÃO ATUAL DO AUDITAR SST
> **Android:** `v3.29.158+300`  
> **Windows:** `v3.30.77+264`  
> **Branch:** `feature/client-panel-permissions-v329106`  
> **PR:** `#15` — permanece em rascunho para revisão; não publicar a Central automaticamente.  
> **Status:** ✅ CI validada — Android e Windows concluídos com sucesso em 03/10/2026. A linha atual mantém a **Ronda** no **Padrão Auditar 3** e a **biblioteca técnica offline** agora também sugere modelos diretamente no modo Ronda a partir da descrição digitada. O recurso é local e complementar: não substitui IA, preenchimento manual nem funções existentes.
>
> O código final é montado pelos workflows atuais a partir da base + patches incrementais.  
> **Regra permanente:** não alterar, substituir ou refatorar funcionalidades que já estejam funcionando sem autorização expressa. Toda melhoria deve ser aditiva, isolada e de mínimo impacto. Preservar especialmente sincronização, banco, autenticação, IA, mídia/fotos, Drive e Central.
>
> Consulte [CURRENT_VERSION.md](CURRENT_VERSION.md) antes de iniciar qualquer alteração. Estado validado atual: integração da Ronda offline no commit `544e490d2c82342e6d839b74a1ddb5fa9bf41f1b`, Android run `37167428008`, Windows run `37167429861`.


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
