# Pré-conferência de NC semelhante — homologação Android (18/11/2026)

## O que foi acrescentado
Uma tela de conferência opcional, acessível pelo Modo Visita Inteligente
após selecionar empresa: **Conferir NC antes de registrar outra**.

O técnico informa descrição e setor; o app compara o texto apenas com
as NCs abertas disponíveis **localmente** para a empresa selecionada.
Apresenta até cinco hipóteses de correspondência. A opção
**Acompanhar esta NC** abre o histórico da NC original (PR #70) para
documentar nova visita, foto ou correção informada.

A opção **Não é a mesma situação • Nova Ronda** exige confirmação
explícita antes de abrir a Ronda Expressa existente.

## Critérios de segurança
- Escopo obrigatório por empresa, com ID existente da NC.
- Com setor definido nos dois lados, setores diferentes são excluídos.
- Requer pelo menos dois termos relevantes compartilhados e pontuação
  mínima para sugerir, mas **não decide identidade da ocorrência**.
- Normalização básica de acentos, hífens e espaços.
- Status explícito corrigido, resolvido ou validado não é apresentado
  como pendência; status "Concluída" de vistoria, isoladamente, não
  comprova correção da NC.
- Não agrupa, remove, cria, encerra ou modifica NC automaticamente.
- Falha de leitura é exibida; ausência de correspondência não significa
  ausência de problema ou de cadastro em outro aparelho.
- Sem alteração de modelos, banco, autenticação, GS, sincronização ou
  aplicativos instalados.

## Limite importante
**Esta primeira etapa é uma checagem antes de iniciar nova Ronda**, não
um interceptor do botão Salvar dentro da Ronda Expressa. O fluxo de
gravação original permanece intacto. O vínculo entre registros só ocorre
quando o técnico escolhe uma NC existente e anota o acompanhamento local.

Não inclui identificação de duplicatas antigas, edição de plano oficial,
status técnico, fotos compartilhadas ou atualizações no Portal do Cliente.

## Antes de publicar
1. Verificar os nomes reais dos campos de NC, empresa e setor e a API
   getNonConformityRows na fonte efetiva Android.
2. Testar a experiência com dados fictícios e autorizados em aparelho real,
   incluindo setor ausente, descrição genérica e mesma situação em máquinas
   distintas. Avaliar necessidade de identificador de equipamento.
3. Testar abertura do histórico, câmera, conta e permissões,
   navegação/retorno e operação offline.
4. Decidir integração posterior no formulário de Ronda, apenas após
   inspeção do código efetivo e revisão de risco de duplicação.
5. Fazer backup e manter app/GS instalados sem alteração até autorização.

## Testes
- Regras puras: nc_duplicate_advisor_test_v1.dart.
- Widgets Flutter isolados: nc_duplicate_review_widget_test_v1.dart.
- Compatibilidade pré-instalação: test_android_unified_visits_preflight_v1.py.

Este trabalho é uma PR de homologação, não um APK distribuído.
