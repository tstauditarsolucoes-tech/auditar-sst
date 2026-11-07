# Auditar SST — Plano de integração e homologação Android/Windows (06/11/2026)

> Escopo obrigatório: **aplicativo Flutter Android e Windows existente**. Não integrar com o projeto Web/VPS do Júlio, não publicar clientes de CIPA, não alterar dados de produção e não distribuir builds com chave operacional em dispositivo de membro.

## Estado de entrada confirmado

| Entrega em PR draft | Dependências/critério |
|---|---|
| #29, #30 e #36 — triagem, roteiro de oito etapas e reunião assistida | aplicar patches na ordem declarada pelos próprios scripts e conferir hashes; testar ambos os sistemas |
| #31, #32 e #37 — nome/função, cliente CIPA separado e tela simplificada | **não liberar login** sem backend de sessão individual validado; nunca distribuir APK do técnico a membros |
| #33, #34 — sugestão offline e biblioteca de 204 situações | preservar descrições existentes, conferir NRs como referências e validar falso positivo |
| #35 — seis modelos de relatório SST | testar isolamento de empresa/usuário, várias visitas, backup, assinatura e PDF offline |

Os PRs são **propostas separadas**; sucesso de testes isolados não significa compilação integrada nem release homologada.

## Sequência obrigatória

1. Registrar SHA do branch-base de produção e das PRs; conferir modificações concorrentes e dependências de scripts de patch.
2. Criar branch de integração Android/Windows **separada da produção**; aplicar alterações em ordem determinística, abortando se houver arquivo/hash divergente.
3. Rodar format, analyze e testes Flutter/Dart dos módulos existentes, testes de regressão das telas e verificações específicas de CIPA, relatórios, catálogo e login.
4. Compilar Android e Windows completos **sem assinatura/chaves reais no CI de homologação**; não publicar artefatos de produção.
5. Em cópia de dados fictícios, testar upgrade de versão anterior, operação offline, retomada, fotos, PDFs e reconexão sem duplicar registros; também app minimizado e reaberto para conferir cache.
6. Testar em dispositivos Android e computador Windows reais, com usuário técnico, gestor, cliente e membro CIPA *somente quando houver backend seguro*.
7. Conferir contagem das vistorias por empresa e técnico após sincronização e persistência, corrigindo contagens sem alterar históricos.
8. Conferir atualização da biblioteca local e a origem dos modelos, inclusive panificação NR-12 e demais NRs. Não prometer sincronização automática quando catálogo for empacotado com aplicativo.
9. Registrar evidências dos testes (captura de telas, logs expurgados, hashes dos instaladores, versões e resultado por cenário).
10. Exigir autorização expressa antes de mesclar/publicar a versão que será distribuída.

## Casos críticos de homologação

| ID | Cenário | Resultado esperado |
|---|---|---|
| A01 | Criar vistoria offline com duas fotos; fechar e reabrir aplicativo | Rascunho e fotos permanecem íntegros; não duplicar |
| A02 | Sincronizar a mesma vistoria duas vezes | Uma vistoria contabilizada; histórico preservado |
| A03 | Consultar vistoria de empresa distinta | Nenhum registro cruzado |
| A04 | Pesquisar NR-12 panificação offline | Catálogo completo e sugestões relacionadas; nenhuma NC automática |
| A05 | Negação/incerteza no relato (“não verificado”, “já corrigido”) | Sem transformar hipótese em não conformidade |
| A06 | Criar, arquivar, reabrir e exportar relatório de campo | Histórico imutável e PDF coerente; observações/fotos corretas |
| A07 | Simular falha ao salvar relatório | Não perder rascunho nem emitir PDF inválido |
| A08 | Reunião CIPA com mandato ativo e data vencida ainda agendada | Alerta para conferência, sem presumir realização |
| A09 | Reunião CIPA finalizada sem assinatura | Não marcar como assinada ou legalmente concluída |
| A10 | Membro CIPA acessando somente registros autorizados | Nenhum acesso a cliente diferente, chave master ou telas técnicas |
| A11 | Portal CIPA em fonte ampliada e tela pequena | Botões grandes e texto legível sem cortes |
| A12 | Tentativa de acesso CIPA sem sessão individual autorizada | Acesso bloqueado |
| A13 | Fechar/abrir Windows e Android com dados já sincronizados | Carregar cache permitido e buscar só atualização; sem apagamento |
| A14 | Consultar treinamentos, arquivos e registros antigos | Dados anteriores permanecem visíveis |

## Critérios de liberação (todos obrigatórios)

- [ ] Dependências dos PRs resolvidas, sem sobrescrever código em produção.
- [ ] Todas as compilações Android e Windows completas aprovadas.
- [ ] Testes automatizados e cenários A01–A14 executados com evidências.
- [ ] Contagem de vistorias e biblioteca automática verificadas com casos reais sanitizados.
- [ ] Isolamento de empresas/usuários e proteção das credenciais conferidos.
- [ ] Teste de atualização e recuperação de dados concluído.
- [ ] Portal individual ativado **apenas após** homologação do backend seguro.
- [ ] APK/EXE e versão identificados; autorização de publicação registrada.

## Bloqueios conhecidos

A execução de testes de interface isolados **não prova** segurança do backend, instalação em aparelho real ou que as mudanças já estejam presentes nas versões distribuídas. Enquanto os critérios acima não forem concluídos, manter PRs em draft, sem merge na produção e sem APK/EXE novo aos clientes.

**Canal de denúncias:** permanece fora do escopo, conforme decisão do projeto.
