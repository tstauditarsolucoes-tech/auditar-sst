# Auditar SST — Portal do membro da CIPA: uso fácil (09/11/2026)

Escopo restrito ao **cliente Android individual da CIPA**, integrado futuramente à gestão do **Auditar SST Android e Windows existentes**. Não é a versão Web/VPS pendente.

## Experiência de três ações
Ao abrir uma sessão autorizada o membro vê primeiro:
1. **Fazer vistoria** (botão principal e grande)
2. **Minhas tarefas**
3. **Ver reuniões**

"**Avisar uma situação**" permanece disponível em "Mais informações", preservando o fluxo existente sem disputar espaço com a vistoria. O histórico de "Minhas vistorias orientadas" continua separado de "Outras observações", filtrado por pessoa/empresa/mandato.

## Vistoria sem complicação
- O membro escolhe o **setor/tema** e informa o local observado.
- São apenas **três perguntas**, respondidas com **Sim / Não / Não sei/não verifiquei**.
- Temas gerais preservados: organização e circulação; máquinas e equipamentos; incêndio e emergência; ambiente e proteção.
- Acrescentados sete setores: **panificação, cerâmica, construção civil, laticínios, logística e depósitos, limpeza urbana, comércio e escritórios**.
- Dica rápida "Como observar com segurança?" muda conforme o setor.
- Contador mostra quantas perguntas faltam; nenhuma resposta vem marcada.
- Se o membro assinalar situação a conferir, o sistema orienta a afastar-se, não realizar testes ou correções e avisar a empresa se houver perigo imediato.
- O formulário deixa claro que é uma **observação visual**, não laudo técnico, avaliação de conformidade ou encerramento de NC.

## Segurança e dados
- Continua usando a mesma callback de relato autorizado já existente (`onObserve`), sem novas rotas ou permissões.
- Aplicar limite de 1.200 caracteres do backend em homologação e mínimo de dois caracteres no local.
- Não habilitar foto, voz, rascunho persistente offline, notificações push ou estados de atendimento não presentes no backend.
- Não compartilhar credenciais técnicas; manter login de membros desabilitado sem validação segura pela Central e testes contra acesso cruzado.
- Nenhum registro real foi enviado, nenhum APK foi distribuído, nenhuma alteração no cliente/servidor em produção.

## Validação
Workflow Flutter isolado: `.github/workflows/validate-cipa-portal-simple.yml`.
Testes cobrindo os sete setores, 3 perguntas, limites do envio, mensagens conservadoras, formulário, tela pequena, histórico e ausência de sessão. **O resultado do CI precisa ser conferido** antes de aceitar a PR. Mesmo com sucesso, testes com usuários reais, backend e APK Android completo ainda serão necessários.

## Fases posteriores, não incluídas
- **Fotos**: requer upload privado autenticado, autorizações e revisão da retenção de dados.
- **Devolutiva e acompanhamento pelo TST**: exige transição de estados e trilha de auditoria no servidor; o membro consulta, mas não altera.
- **Rascunho offline**: depende de armazenamento cifrado e revogação efetiva.
- **Áudio/digitação por voz**: somente após controles de consentimento, privacidade e revisão textual.

A experiência deve ser testada com usuários pouco familiarizados com smartphone e fontes ampliadas antes de liberação.
