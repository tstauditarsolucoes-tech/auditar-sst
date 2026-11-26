# Auditar SST — Fechamento da homologação dos novos módulos
Data: 26/11/2026

## Resultado confirmado
- PR #83: APR/AR/PT/PET guiados, rubricas manuscritas de ciência, segregação por conta e empresa e impressão SHA-256 da versão assinada.
- GitHub Actions 45802603283: **SUCCESS nos três jobs**: static-check, flutter-fixture (analyze/test e build APK debug) e windows-flutter (analyze/test e build Windows debug).
- As compilações aprovadas são de projetos de testes com autenticação e banco fictícios. NÃO são instaladores do aplicativo comercial.

## Bloqueio ao montar app integral
- Fonte do repositório: Auditar_SST_v1.5_dashboard_completo.zip com tools/assemble_v3290.py.
- A montagem recompõe versão **3.29.0** e não contém, entre outros, lib/screens/quick_visit_screen.dart e lib/screens/express_round_screen.dart.
- Referências operacionais: Android v3.29.195 e Windows v3.30.123. A base 3.29.0 é muito antiga para receber esses patches com segurança.
- O verificador tools/test_sst_full_integration_probe_v1.py bloqueia explicitamente bases desatualizadas para evitar distribuição acidental.

## Pendências para APK e EXE reais de homologação
1. Obter o código-fonte **integral e atual** correspondente às versões 3.29.195 (Android) e 3.30.123 (Windows), incluindo pubspec.yaml, lib, assets e estruturas de plataforma, sem tokens ou dados reais.
2. Conferir versão e hash da origem e usar cópias isoladas por plataforma.
3. Integrar as melhorias das PRs #75–#83 sem modificar banco, sincronização, autenticação, GS e relatórios anteriores.
4. Executar flutter analyze/test e compilações Android/Windows integrais.
5. Homologar com aparelhos reais, backup e plano de reversão: instalações sem desinstalar, login, dados, fotos, sync, PDF, assinaturas, offline, multiempresa.
6. Revisar segurança/LGPD/SST antes de autorizar a distribuição.

## Limites SST
Rubrica manuscrita de ciência NÃO autoriza PT/PET, não certifica identidade nem atende isoladamente às regras de PET digital da NR-33. O hash SHA-256 é controle local de versão, não assinatura digital certificada.

## Evidências
- Código e testes: https://github.com/tstauditarsolucoes-tech/auditar-sst/pull/83
- CI dos módulos aprovada: https://github.com/tstauditarsolucoes-tech/auditar-sst/actions/runs/45802603283
- Tentativa de integração integral: branch feature/auditar-sst-integracao-real-app-20261126

**Estado:** melhorias prontas em ambiente isolado; aplicativo comercial NÃO liberado devido à ausência da origem integral atual.