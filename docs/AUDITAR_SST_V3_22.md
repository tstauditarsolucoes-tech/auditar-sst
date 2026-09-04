# Auditar SST v3.22 — Estabilização profissional

## Objetivo

Consolidar Android, Windows, sincronização e painel gerencial antes de adicionar novos módulos grandes.

## Mudanças da 3.22

- versão centralizada em `pubspec.yaml` (`3.22.0+80`);
- Android compilado em modo release, com APK universal e opções por arquitetura;
- validação com `flutter analyze` antes dos builds;
- Windows em release com pacote portátil e instalador Setup.exe;
- status de sincronização visível no aplicativo e no computador;
- modo offline permanece ativo, sem impedir registros de campo;
- acesso direto para continuar vistoria em andamento;
- Agenda SST integrada ao snapshot do painel gerencial;
- painel da gerência com resumo semanal recolhível e aba Agenda SST;
- cadastro da Agenda permanece dentro do app/PC; o link gerencial continua somente para acompanhamento;
- documentação da fonte canônica e regra para não criar novos ZIPs duplicados.

## O que foi preservado

Nenhum módulo existente deve ser removido: empresas, obras, setores, trabalhadores, treinamentos, CIPA, checklists, vistorias, não conformidades, planos de ação, Rotina SST, extintores, atos e condições, melhorias, indicadores, relatórios, Drive e IA permanecem no produto.

## Segurança

A 3.22 mantém compatibilidade com a chave de sincronização atual para não interromper celular, PC, CIPA, Drive, IA e painel. A chave continua fora do código-fonte público e é injetada pelo segredo `AUDITAR_SYNC_KEY` no build.

Para uma distribuição comercial para terceiros, a etapa seguinte será trocar a credencial compartilhada por autorização individual de dispositivo/usuário. Essa migração deve ser feita com compatibilidade e revogação de dispositivos, e não como uma troca brusca que possa bloquear instalações atuais.

## Assinatura Android

`--release` otimiza o aplicativo, porém distribuição comercial exige uma chave de assinatura Android permanente. Essa chave não deve ser adicionada ao repositório. Ela deve ficar em GitHub Secrets ou em um serviço de assinatura seguro.

## Migração futura da base legada

O arquivo `Auditar_SST_v1.5_dashboard_completo.zip` ainda é usado como base temporária. A remoção só deve ocorrer depois que todos os arquivos necessários forem promovidos para uma árvore fonte normal no repositório e os builds Android/Windows passarem usando exclusivamente essa árvore.

Até lá, `source_overrides/` e `tools/` representam a camada oficial de atualização.
