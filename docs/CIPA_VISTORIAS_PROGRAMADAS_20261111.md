# Programação simples de vistorias da CIPA — 11/11/2026

## Entrega experimental
A Central administrativa escolhe **integrante, setor/tema e data** para programar uma vistoria, com orientação opcional. O membro vê suas vistorias em **Vistorias programadas**, na tela Minha CIPA, e pode usar o botão Fazer vistoria já existente.

São 11 roteiros permitidos: quatro temas gerais e sete setores (panificação, cerâmica, construção civil, laticínios, logística, limpeza urbana, comércio/escritórios). O preenchimento continua com três perguntas simples por roteiro e orientação para observação visual segura.

A agenda é **individual** e não autoriza o membro a subir em andaimes, entrar em fornos, manipular instalações ou operar máquinas. Não há marcação automática de conclusão ou de conformidade; o registro posterior continua sujeito à análise técnica.

## Segurança
- Só ADM autenticado pode criar/cancelar agendamento; valida mandato e membro ativos no servidor, sob lock e com request ID idempotente.
- A agenda é append-only. Cancelar cria nova linha e retira a programação da consulta do integrante.
- O membro vê somente empresa, mandato e identidade pessoal autorizados. A UI também rejeita registros alheios.
- Data futura em formato ISO válida e dentro do horizonte de 185 dias. Orientação limitada a 180 caracteres; rejeição de fórmulas em Sheets.
- Nenhuma notificação push, geolocalização, foto, rascunho offline persistente ou novo APK foi publicada.

## Bloqueios da homologação
Conferir integração do servidor Apps Script real, compatibilidade da seleção de usuários, fuso de data e calendário em Android, autorização revogável e teste em duas empresas. O vínculo entre um relato posterior e o agendamento ainda não é confirmado por backend; a seção é uma agenda e não uma lista de serviços concluídos.

Arquivos: `CipaMemberInspectionSchedulesV1.gs`, alterações no Gateway, DTO do membro, painel ADM, API e testes. **Não ativar em produção antes de homologar.**
