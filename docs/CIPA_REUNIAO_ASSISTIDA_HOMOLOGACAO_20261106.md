# Auditar SST — CIPA: Reunião assistida | Homologação

Data: 06/11/2026. **Esta etapa é no app operacional Android/Windows; não é o projeto Web do Júlio.**

## Melhoria para integrantes e gestores iniciantes

No painel de gestão da CIPA, logo abaixo de **Sua CIPA, passo a passo**,
foi preparado o cartão expansível **Reunião assistida: antes e depois**.
O aplicativo **lê dados do mandato ativo** e mostra o que deve ser conferido,
com botão para abrir o editor existente. Nenhuma informação é preenchida ou
aprovada automaticamente.

As orientações específicas incluem:
- Mandato ativo e integrantes localizados.
- Reunião futura: confirmar data, horário, local, pauta e convidados.
- Data anterior ainda agendada: verificar realização, cancelamento ou remarcação.
- Reunião realizada: confirmar presenças efetivas, assuntos e decisões.
- Ata inexistente ou em rascunho: orientar revisão e documentação.
- Mesmo ata finalizada: orientar conferência das assinaturas dos presentes
  e da divulgação/disponibilização dos encaminhamentos.
- Ações da CIPA: prazos vencidos e responsáveis não informados.

A tela disponibiliza ações de **Abrir reunião**, **Preparar reunião**,
**Abrir atas**, **Ver integrantes** e **Abrir ações**, todas encaminhando
para os formulários e abas já existentes. Não cria reunião ou ata sem uma
ação explícita do usuário. Não atribui presença ou assinaturas automaticamente.

## Segurança do dado

- A seleção considera **somente registros do mandato ativo e empresa atual**.
- Se não há mandato, não usa reuniões de outros mandatos como se estivessem
  ativas.
- **Ciência de convocação não é registro de presença.**
- **Rascunho ou finalização de ata não é assinatura.**
- A ausência no aplicativo não prova descumprimento normativo.
- A lista de verificações não substitui conferência humana ou requisitos
  específicos de dimensionamento, calendário ou documentação.
- Não modifica login, dados, sincronização, PDFs, Central Online e versões
  anteriores de atas. O canal de denúncias continua fora do escopo.

## Implementação

- `feature_sources/cipa_meeting_coach_rules_v1.dart` — motor de orientação
  puramente local, sem escrita no banco.
- `feature_sources/cipa_meeting_coach_home_v1.dart` — cartão de interface
  integrado à tela original da CIPA.
- `tools/patch_cipa_meeting_coach_v1.py` — instalador aditivo e
  verificação de integridade fora do escopo.
- `feature_sources/cipa_meeting_coach_rules_test_v1.dart` — cenários
  de reunião agendada, realizada, atrasada, ata, ausências e ações.
- `tools/test_cipa_meeting_coach_patch_v1.py` — teste de segurança da
  inserção, com servidor e autenticação preservados.
- `tools/stage_cipa_meeting_coach_flutter_v1.py` — fixture da UI real,
  sem acesso ao banco nem servidor.
- `.github/workflows/validate-cipa-meeting-coach.yml` — validação Dart,
  Flutter e teste de patch.

## Limite de implantação

O recurso está em uma branch dependente do projeto CIPA da PR #32.
O portal individual dos membros ainda está em homologação e **não pode
usar a chave operacional nem o login dos técnicos**. O novo cartão de
reuniões não ativa o portal nem publica dados.

As montagens **Android** e **Windows** contêm as etapas de instalação do
roteiro em código, mas a compilação completa e a utilização nos aparelhos
reais ainda não foram verificadas. A versão Windows instala também a camada
de guia existente; a montagem falhará com segurança se alguma etapa não
corresponder ao código atual.

Para liberar no app instalado: compilar a versão operacional e realizar
testes de interface, dados de mandato, histórico e permissões em
dispositivos reais. **Nenhuma versão instalada foi substituída** nesta etapa.

Referência técnica para conferência: [NR-05 vigente — MTE](https://www.gov.br/trabalho-e-emprego/pt-br/acesso-a-informacao/participacao-social/conselhos-e-orgaos-colegiados/comissao-tripartite-partitaria-permanente/normas-regulamentadora/normas-regulamentadoras-vigentes/norma-regulamentadora-no-5-nr-5).

Validação isolada aprovada: [regras Dart](https://github.com/tstauditarsolucoes-tech/auditar-sst/actions/runs/42219983700) e [tela Flutter](https://github.com/tstauditarsolucoes-tech/auditar-sst/actions/runs/42220147732).
