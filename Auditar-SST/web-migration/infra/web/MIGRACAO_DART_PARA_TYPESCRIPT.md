# Rastreabilidade da primeira migração de regras SST

> Migração incremental de módulos **puros**, sem modificar o armazenamento, a Central Online ou as versões instaladas. Os registros exibidos na interface são fictícios.

| Fonte Flutter / Dart | Destino TypeScript | Regra e cobertura |
| --- | --- | --- |
| `feature_sources/offline_field_rules_service_v329165.dart` · `matrixScore` | `src/domain/nc.ts` · `matrixScore` | Entradas inteiras, probabilidade/severidade limitadas a 1..5, recorrência +2, teto de 25 |
| Mesmo arquivo · `priorityFromMatrix` | `src/domain/nc.ts` · `priorityFromMatrix` | Faixas Baixa até 4, Média até 9, Alta até 16, Crítica acima de 16 |
| `feature_sources/nc_title_store_v1.dart` · `save` (parte pura) | `src/domain/nc.ts` · `normalizeFriendlyName` | Normalização de espaços e limite de 80 caracteres; SEM implementação de `AppDatabase` |
| Mesmo arquivo · `displayTitle` | `src/domain/nc.ts` · `displayNcTitle` | Alias prioritário; fallback descrição/pergunta; primeira frase até 76; corte com reticências |
| Regras anteriores | `src/domain/nc.test.ts` | Testes com dados sintéticos; nenhuma conexão externa |

## Interface

`src/App.tsx` oferece:
- Resumo ilustrativo e simulador com resultado calculado pelo módulo migrado.
- Busca e filtro de exemplos identificados como `DEMO-NC-...`.
- Edição dos nomes amigáveis com limite de 80 caracteres em memória, sem modificar ID e descrição.

Não existe login, persistência de nomes, upload, CRUD de NC real, segregação multiempresa, agenda, PDF ou fluxo de validação de correção. Não considerar este protótipo adequado para operação SST real.

## Testes e deploy

```bash
cd Auditar-SST/web-migration/infra/web
npm install --no-audit --no-fund
npm run test
npm run build
```

A imagem Docker tem build multiestágio e serve `dist` com Nginx, isolada pelo Compose e sem publicação de portas. A API Node expõe exclusivamente um endpoint de saúde. A CI repete os testes e a compilação, **sem deploy**.

### Próximas regras a portar

1. Sugerir NRs e suas fontes técnicas, comparar saídas Dart×TypeScript com corpus validado pelo TST.
2. Serviços de NC/agenda e tratamento antes×depois com controle de acesso por empresa.
3. Relatórios/PDF e fotos com proteção de dados e assinatura válida.
4. Integração por API segura com dados após autorização, estratégia de backup e homologação com Júlio.

A lógica de decisão da matriz foi copiada fielmente do Dart. A lógica de título foi portada; a implementação original persiste em `AppDatabase` com chave por usuário, **não migrada** nem acessada.
