AUDITAR SST v3.8.0

CORREÇÃO: o cadastro de uma nova eleição da CIPA agora fecha o formulário
antes de gravar os dados, evitando a tela vermelha do Flutter durante a
desmontagem dos campos. A inclusão de candidatos recebeu a mesma proteção.

NOVIDADES: Treinamento em lote, matriz ligada aos cargos importados do RH,
atualização de periódicos por PDF, painel externo com situação individual de
cada funcionário e envio de e-mail de teste diretamente pelo aplicativo.

NOVIDADES: Importação da lista atualizada de funcionários enviada pelo RH.
Dentro da empresa, o técnico pode selecionar um PDF com Nome e Cargo, conferir
quem será incluído, atualizado ou retirado da lista ativa e confirmar tudo de
uma vez. O histórico de treinamentos dos desligados permanece preservado.

NOVIDADES: Assistente IA exclusivo do técnico, integrado às fotos do checklist
para sugerir descrição da NC, risco, recomendação e prioridade, além de ajudar
na conclusão do relatório. A integração atual usa o Gemini 3 Flash no nível
gratuito. As fotos são reduzidas e recodificadas sem metadados antes do envio.
Toda sugestão precisa ser revisada pelo técnico.

# Auditar SST v3.8.0

Aplicativo Android offline para inspeções, checklists, não conformidades, planos de ação e relatórios de Segurança do Trabalho.

## O que está implementado

- Cadastro e edição de empresas.
- CNPJ, cidade, UF, contato e telefone.
- Logo da empresa opcional.
- Cadastro, edição, ativação e exclusão segura de obras/unidades.
- Checklists personalizados.
- Criar, editar, duplicar, ativar/desativar e excluir modelos.
- Criar, editar, excluir e reordenar perguntas.
- Checklist padrão de Inspeção Geral SST.
- Conforme / Parcial / Não Conforme / Não se aplica.
- Até 10 fotos por não conformidade.
- Fotos pela câmera ou galeria.
- Risco identificado e recomendação técnica.
- Plano de ação com responsável, prioridade, prazo e status.
- Ações pendentes, em andamento, vencidas e concluídas.
- Evidências de correção com fotos ANTES / DEPOIS.
- Reabrir ação concluída.
- Assinatura do técnico na tela.
- Assinatura do responsável da empresa opcional.
- Observações gerais e conclusão do relatório.
- Número automático do relatório.
- Relatório PDF com paginação e rodapé.
- Logo opcional no canto superior esquerdo.
- Todas as fotos das não conformidades no relatório.
- Fotos Antes/Depois das ações concluídas no relatório.
- Dashboard de conformidade, vistorias e ações.
- Histórico de relatórios.
- Editar uma vistoria antiga SEM apagar tudo.
- Preservação das perguntas originais da vistoria no histórico.
- Exclusão de registros feitos por engano.
- Técnico padrão salvo no aplicativo.
- Funcionamento offline com SQLite.

## Google Drive

O aplicativo usa a mesma Central Online do painel gerencial para arquivar PDFs em:

Auditar SST / Nome da empresa / Relatório.pdf

Recursos previstos no código:

- Conectar/desconectar Google Drive.
- Envio manual do relatório.
- Envio automático opcional.
- Se estiver sem conexão, o PDF continua salvo no celular e entra em uma fila.
- Quando a conexão volta com o aplicativo aberto, a fila tenta sincronizar automaticamente.
- Ao voltar para o aplicativo, ele também tenta sincronizar pendências.
- Botão manual “Sincronizar pendentes”.

Não é necessário entrar com uma Conta Google no celular nem cadastrar OAuth Android. A URL permanente e a chave do Google Apps Script já configuradas no aplicativo autorizam o envio. O Apps Script cria a pasta no Drive da conta que publicou a Central Online.

## Backup completo v2

O backup agora é um arquivo ZIP e inclui:

- banco SQLite;
- logos das empresas;
- fotos das vistorias;
- fotos de correção;
- assinaturas;
- PDFs salvos localmente.

Na restauração, o aplicativo corrige os caminhos internos das imagens. Isso permite levar o backup para outro aparelho sem depender do caminho antigo do armazenamento.

## Edição de vistoria

Em Relatórios e histórico, a opção de corrigir/refazer não apaga mais a vistoria antes de abrir.

O aplicativo recupera:

- situação de cada item;
- observações;
- fotos;
- risco identificado;
- recomendação;
- ação corretiva;
- responsável;
- prioridade;
- prazo;
- status da ação;
- assinaturas existentes;
- observações gerais;
- conclusão.

Você altera somente o que precisa e gera novamente o relatório.

## Compilação Android

Este pacote é o código-fonte funcional, mas o ambiente em que ele foi criado não contém o Flutter/Android SDK completo para gerar e testar o APK nesta etapa.

Para a compilação final serão necessários:

1. Flutter compatível com Dart 3.7+.
2. Android Studio / Android SDK.
3. Configuração da câmera.
4. Assinatura do APK/AAB de produção.
5. Teste em aparelho Android real.

Depois disso, o fluxo de validação será:

Empresa → checklist → fotos → plano de ação → assinatura → PDF → Drive → ação corretiva → Antes/Depois → relatório atualizado.

## Checklists editáveis — v1.2

A área de checklists foi ampliada para uso direto no celular.

Agora é possível:
- criar um checklist do zero;
- pesquisar checklists por nome, categoria ou NR;
- editar nome, categoria e norma/referência;
- ativar ou desativar o modelo;
- duplicar um checklist inteiro;
- excluir modelos que não serão mais usados;
- ver quantas perguntas estão ativas e desativadas;
- adicionar uma pergunta;
- adicionar várias perguntas de uma vez, usando uma pergunta por linha;
- editar cada pergunta;
- duplicar uma pergunta;
- excluir uma pergunta;
- ativar/desativar uma pergunta sem excluí-la;
- alterar categoria, referência e prioridade padrão;
- mudar a ordem arrastando;
- mover para cima/baixo pelo menu, sem precisar arrastar;
- visualizar o checklist antes de iniciar uma vistoria.

As vistorias antigas continuam protegidas: a pergunta, categoria e referência usadas no dia ficam gravadas junto da resposta. Alterar o modelo depois não altera o conteúdo histórico do relatório.

### Fluxo no aplicativo

Início
→ Checklists editáveis
→ Criar checklist
→ Adicionar perguntas
→ Organizar
→ Visualizar
→ Nova vistoria
→ Escolher o checklist criado
→ Realizar a inspeção


## Marcação rápida no checklist — v1.3

Durante a vistoria, cada pergunta agora mostra três botões grandes:

- ✅ CONFORME
- ❌ NÃO CONFORME
- ➖ N/A

O botão tocado fica destacado.

Ao marcar **Não Conforme**, aparecem imediatamente os campos de descrição, fotos, risco, recomendação e plano de ação.

No topo da vistoria também existem:
- barra de progresso;
- contador “X de Y itens respondidos”;
- percentual preenchido;
- botão **MARCAR TODOS COMO CONFORME**.

O botão “Marcar todos como Conforme” é útil para inspeções grandes: o técnico pode marcar tudo e depois alterar somente os itens que realmente apresentarem problema.

Os itens marcados como **N/A** continuam fora do cálculo da porcentagem de conformidade.


## APK de teste — build automático

Esta versão inclui GitHub Actions para gerar automaticamente:
- `Auditar_SST_TESTE.apk`
- `Auditar_SST_RELEASE.apk`

O APK de teste deve ser usado primeiro para validar o aplicativo em um aparelho Android real.


## Dashboard completo — v1.5

O painel de Indicadores agora permite filtrar por:

- Empresa;
- Obra / Unidade;
- Período:
  - Todos;
  - Hoje;
  - Últimos 7 dias;
  - Este mês;
  - Últimos 30 dias;
  - Personalizado;
- Prioridade:
  - Todas;
  - Baixa;
  - Média;
  - Alta;
  - Crítica.

O Dashboard mostra:

- quantidade de vistorias;
- percentual de conformidade;
- itens conformes;
- itens não conformes;
- itens N/A;
- ações pendentes;
- ações vencidas;
- ações concluídas;
- ações em andamento;
- distribuição das não conformidades por prioridade.

Observação: empresa, obra e período afetam todos os indicadores. O filtro de prioridade é aplicado aos indicadores do plano de ação (pendentes, vencidas, concluídas e em andamento), pois itens conformes não possuem prioridade de ação corretiva.


## Versão 2.0 - Empresas e Setores

Esta etapa adiciona cadastro de setores por empresa, vinculação obrigatória de novas vistorias ao setor, painel individual da empresa e filtro de indicadores por setor. A migração do banco local preserva as vistorias anteriores.

## v2.1 — NC separada do Plano de Ação
A partir desta versão, uma Não Conformidade é um registro próprio. O Plano de Ação é criado depois, quando necessário, e uma mesma NC pode possuir várias ações corretivas. Também foi adicionada a resposta "Parcial" no checklist e um PDF individual para cada NC.

## v2.2 — Biblioteca de Checklists Prontos + Identidade Auditar

Esta versão adiciona uma biblioteca inicial de checklists prontos para uso diário, organizada por categoria e totalmente editável.

Categorias iniciais:
- Construção Civil;
- Panificação;
- Cerâmica;
- Máquinas e Equipamentos;
- Incêndio e Emergência;
- Elétrica;
- Ergonomia;
- Produtos Químicos;
- Espaço Confinado;
- Geral.

Foram incluídos modelos prontos como andaime fachadeiro, escavação, betoneira, instalações elétricas provisórias, trabalho em altura, máquinas de panificação, esteiras, prensas, forno/secador, roçadeira, empilhadeira, extintores, rotas de emergência e outros.

Na Nova Vistoria, o checklist agora é escolhido em uma biblioteca com pesquisa e filtro por categoria. Os modelos continuam editáveis, duplicáveis e personalizáveis.

A identidade visual foi atualizada para seguir a Auditar: azul-marinho, verde e o ícone circular azul/verde escolhido para o aplicativo.
