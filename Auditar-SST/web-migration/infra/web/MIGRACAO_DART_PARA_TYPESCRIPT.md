# Rastreabilidade da primeira migração de regras SST

> Migração incremental de módulos **puros**, sem modificar o armazenamento, a Central Online ou as versões instaladas. Os registros exibidos na interface são fictícios.

| Fonte Flutter / Dart | Destino TypeScript | Regra e cobertura |
| --- | --- | --- |
| `feature_sources/offline_field_rules_service_v329165.dart` · `matrixScore` | `src/domain/nc.ts` · `matrixScore` | Entradas inteiras, probabilidade/severidade limitadas a 1..5, recorrência +2, teto de 25 |
| Mesmo arquivo · `priorityFromMatrix` | `src/domain/nc.ts` · `priorityFromMatrix` | Faixas Baixa até 4, Média até 9, Alta até 16, Crítica acima de 16 |
| `feature_sources/nc_title_store_v1.dart` · `save` (parte pura) | `src/domain/nc.ts` · `normalizeFriendlyName` | Normalização de espaços e limite de 80 caracteres; SEM implementação de `AppDatabase` |
| Mesmo arquivo · `displayTitle` | `src/domain/nc.ts` · `displayNcTitle` | Alias prioritário; fallback descrição/pergunta; primeira frase até 76; corte com reticências |
| Regras anteriores | `src/domain/nc.test.ts` | Testes com dados sintéticos; nenhuma conexão externa |

## Assistente Offline migrado (regras puras)

Fonte: `feature_sources/offline_field_rules_service_v329165.dart` (análise, _generic, _profiles, suggestNrs, sugerir responsável/prazo, motivo, evidências, NR detalhes). Destino: `src/domain/offlineRules.ts`.

- 21 perfis técnicos + perfil genérico convertidos integralmente do Dart sem dependências remotas.
- Regras textuais para 15 NRs com normalização de acentos igual à fonte, pontuação ponderada por termos, desempate pela primeira regra e organização numérica.
- Cálculo de prioridade continua vindo do módulo `nc.ts`, com bônus de recorrência.
- Saída: categoria, risco/consequência, recomendação, responsável, prazo, evidência, justificativa, NR sugerida e probabilidade/severidade orientativas.
- `src/domain/offlineRules.test.ts` verifica correspondência com exemplos controlados de máquinas, incêndio, altura, EPI, perfil genérico e prazos.

**Limite:** sugestões técnicas baseadas em texto NÃO substituem análise do TST; a biblioteca textual não é uma validação normativa oficial e deve ser revisada antes de uso operacional. Nenhum dado de cliente, banco ou sincronização foi acessado.

## Interface

`src/App.tsx` oferece:
- Resumo ilustrativo e simulador com resultado calculado pelo módulo migrado.
- Busca e filtro de exemplos identificados como `DEMO-NC-...`.
- Edição dos nomes amigáveis com limite de 80 caracteres em memória, sem modificar ID e descrição.\n- Aba Assistente Offline para testar descrições fictícias com NR sugerida, risco, plano de ação, responsável e prazo, com seleção de probabilidade/severidade.

Não existe login, persistência de nomes, upload, CRUD de NC real, segregação multiempresa, agenda, PDF ou fluxo de validação de correção. Não considerar este protótipo adequado para operação SST real.

## Testes e deploy

```bash
cd Auditar-SST/web-migration/infra/web
npm install --no-audit --no-fund
npm run test
npm run build
```

A imagem Docker tem build multiestágio e serve `dist` com Nginx, isolada pelo Compose e sem publicação de portas. A API Node expõe exclusivamente um endpoint de saúde. A CI repete os testes e a compilação, **sem deploy**.

### Próximas etapas

1. Comparar o assistente Dart×TypeScript com corpus técnico revisado pelo TST e complementar testes de regressão.\n2. Serviços de NC/agenda e tratamento antes×depois com controle de acesso por empresa.\n3. Relatórios/PDF e fotos com proteção de dados e assinatura válida.\n4. Integração por API segura com dados após autorização, estratégia de backup e homologação com Júlio.

A lógica de decisão da matriz foi copiada fielmente do Dart. A lógica de título foi portada; a implementação original persiste em `AppDatabase` com chave por usuário, **não migrada** nem acessada.
