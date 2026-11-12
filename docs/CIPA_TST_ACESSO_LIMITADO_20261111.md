# Delegação do TST — Central CIPA (11/11/2026)

Implementação experimental sobre PR #43. **Não implantado em produção.**

## Experiência simples
- ADM na gestão Auditar SST informa o ID da conta técnica e seleciona **Autorizar** ou **Revogar**, exclusivamente para a empresa e mandato abertos.
- O técnico acessa uma tela própria, **Vistorias da CIPA**, com leitura de relatos, botão **Responder ao membro**, duas situações (**Em análise**, **Orientação enviada**) e orientação curta.
- O membro recebe a devolutiva no próprio histórico de vistorias, sem poder alterar o parecer.

## Controles obrigatórios
- Rota TST é separada da administrativa. Não concede gestão de contas, eleições, publicações ou documentos.
- O servidor valida sessão ativa, perfil explicitamente `tst` ou `tecnico`, concessão ativa por **usuário+empresa+mandato** em cada leitura e escrita, inclusive sob lock na gravação.
- Apenas administrador concede ou revoga. Revogação impede acesso na chamada seguinte.
- Um retorno do TST nunca encerra uma NC nem certifica resolução da pendência.
- A autorização deve apontar para ID real da conta TST; a tela não valida existência/role na concessão: a Central nega leitura e escrita se a conta técnica real não atender aos requisitos.
- A interface TST ainda é um arquivo de fonte isolado, **não está conectada à navegação instalada**.
- Ainda requer backup do Apps Script real, teste com IDs reais de homologação, teste com duas empresas/mandatos e revisão de LGPD.
- Fotos, anexos, alertas push, rascunhos offline e criação de vistoria agendada ainda dependem de infraestruturas e validações próprias. Não habilitar antes da proteção de acesso, armazenamento e idempotência.

## Testes
`tools/test_cipa_member_gateway_v1.cjs` e workflow `validate-cipa-central-reviews.yml` adicionam casos de TST sem autorização, concessão ADM, revogação, escopo cruzado e idempotência, além de smoke test da tela Flutter. Acompanhar o estado do CI antes de concluir.

## Publicação
Manter PR draft e login de membros desabilitado; não modificar versões Android/Windows instaladas nem a versão Web do Júlio.
