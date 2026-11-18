# Acompanhamento de NC Persistente — homologação Android

## Objetivo
Registrar sucessivas verificações na MESMA não conformidade já cadastrada.
A nova verificação não cria outra NC e não encerra a pendência existente.

## Navegação
Selecionar empresa → Preparar Visita Inteligente → Acompanhar NC existente.
Selecionar uma pendência válida da empresa.

## Ações disponíveis
- Registrar acompanhamento: nova observação e data no histórico local.
- Anexar foto: câmera, máximo de 2 MB, armazenamento privado local.
- Ver plano de ação: leitura dos campos já existentes, sem modificá-los.
- Informar correção para validação: registra a informação, mas a NC só
  pode ser encerrada no fluxo oficial de validação técnica.

## Salvaguardas
- Isolamento por usuário, empresa e identificador existente da NC;
  exige ID e vínculo explícito à empresa.
- Histórico aditivo em settings locais, sem alteração da NC original.
- Eventos idempotentes por identificador; erros são exibidos sem
  afirmar que os registros foram gravados.
- Não mistura dados de empresas e não assume ausência de riscos
  quando não encontra registros locais.
- Não sincroniza com GS/Central/Windows/Painel do Cliente e não corrige
  automaticamente duplicatas históricas. Fotos não saem do aparelho.
- Não altera database.dart, models.dart, serviços de sync ou Code.gs.

## Homologação pendente
1. Revisar os contratos reais de getNonConformityRows, getSetting,
   setSetting, activeUserId e AuthService nas fontes efetivas do Android.
2. Testar dados reais autorizados em ambiente de homologação e
   confirmar os nomes de campos de empresa, NC, setor e plano.
3. Testar aparelho físico, câmera, permissão, sessão e uso offline.
4. Validar backup e compatibilidade da versão antes de gerar APK.
5. Definir integração segura posterior com Central, Windows e cliente,
   sem atualizar GS por iniciativa própria e sem merge automático.

## Testes
Testes puros: escopo por empresa/usuário/NC, idempotência, colisão,
payload inválido e falha de gravação. Testes Flutter isolados: lista,
registro, status não encerrado e segregação de clientes.

A PR é draft. Não representa build ou implantação concluída.
