# Auditar SST v3.24.1 — Qualidade e segurança

## Checklist de campo

- NC Alta: exige descrição e pelo menos uma foto de evidência antes da finalização.
- NC Crítica: exige descrição, foto, risco identificado e recomendação técnica.
- Ocorrências adicionais seguem as mesmas regras da prioridade selecionada.
- O comando **Marcar todos como Conforme** exige confirmação e avisa quando já existem itens NC/Parcial.
- As regras de validação foram extraídas para `ChecklistValidationService`, reduzindo regra de negócio dentro da tela principal.

## Testes automatizados

- Foi criado teste unitário das regras críticas do checklist.
- Android e Windows executam `flutter test` obrigatoriamente antes da compilação.
- A ausência de testes não é mais tratada como sucesso silencioso.

## Segurança

- O token de sessão local passa a ser salvo com `flutter_secure_storage` em Android e Windows.
- Sessões antigas armazenadas no JSON local são migradas automaticamente e o token é removido do arquivo comum.
- No Apps Script, novas senhas usam derivação iterativa de SHA-256 com salt e hashes antigos são migrados após login válido.
- Novas sessões são armazenadas na planilha como hash do token, mantendo compatibilidade temporária com sessões antigas já emitidas.
- `AUDITAR_SYNC_KEY` continua temporariamente disponível apenas para compatibilidade da migração e bootstrap inicial; não remover nesta etapa.

## Implantação da Central Online

Como `MultiUser.gs` foi reforçado, a Central Online deve receber o `MultiUser.gs` gerado pela v3.24.1 e a implantação atual deve ser atualizada como **Nova versão**, mantendo a mesma URL `/exec`.

## Versão

`3.24.1+101`
