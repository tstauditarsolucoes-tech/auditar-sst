# Auditar SST — Ampliação da biblioteca de sugestões offline por setor (v3)

Referência: 06/11/2026. Desenvolvimento em branch isolada, **sem publicação** no aplicativo instalado.

## Escopo

A biblioteca existente de **145 modelos detalhados** continua disponível. Esta atualização
adiciona **59 modelos de campo** e chega a **204 modelos** no acervo detalhado
(`OfflineSstDeepCatalog.entries`). Outras bibliotecas e conteúdos do sistema continuam
separados e não entram nessa contagem.

| Setor | Novos modelos |
|---|---:|
| Cerâmica | 12 |
| Construção civil | 15 |
| Panificação | 8 |
| Laticínios | 7 |
| Logística | 4 |
| Limpeza urbana | 7 |
| Gerais / transversais | 6 |
| **Total** | **59** |

## Como o técnico usa

A interface atual permanece: campo de descrição, sugestão principal, **Aplicar**,
**Ajustar**, **Outras opções**, biblioteca por NR, atalhos rápidos e **Não corresponde**
(recurso da branch anterior). Ao digitar um relato, o acervo usa regras locais
de **tema/equipamento + falha explícita**, sem internet ou IA.

Exemplos incluídos:
- "Secador de pó com proteção removida": proteção de transmissão, referência temática NR-12.
- "Andaime com sapata ausente": estabilidade do andaime, NR-18.
- "Empacotadora com sensor inoperante": proteção de máquina, NR-12.
- "Roçadeira com protetor removido": atividade de limpeza urbana, NR-38.
- "Poda de árvore sem isolamento": proteção de terceiros, NR-38.
- "Betoneira com cabo danificado": segurança elétrica, NR-10.
- "Câmara fria sem destravamento interno": aprisionamento, NR-01.

A consulta também pesquisa pelo **nome do setor** (ex.: "Cerâmica", "Panificação")
e aumenta o limite padrão de resultados de 150 para 250, permitindo percorrer
os 204 modelos mesmo sem termo de busca.

## Condições de segurança

- O relato do técnico deve confirmar uma situação observada; **não inventar fatos,
  medições, testes, pessoas nem irregularidades**.
- Referências NR são temáticas e devem ser conferidas na edição aplicável;
  não implicam enquadramento jurídico automático, insalubridade, periculosidade,
  risco quantificado ou determinação de paralisação.
- O módulo reconhece frases de situação normal, corrigida ou incerta e não
  recomenda abrir uma falha ativa nesses casos.
- A entrada em forno industrial é tratada como situação que exige avaliação
  das condições e da **aplicabilidade** da NR-33, sem presumir sua classificação
  como espaço confinado nem autorizar qualquer entrada.
- Os textos novos sugerem ações e consequências **possíveis**, sempre sob
  revisão do Técnico de Segurança do Trabalho.
- A biblioteca não afeta formulários, banco, sincronização, autenticação,
  fotos, relatórios PDF, Central Online ou IA.

## Arquivos

- `feature_sources/offline_sst_field_catalog_v3.dart` — conteúdo local.
- `tools/patch_offline_field_catalog_v3.py` — instalação aditiva na biblioteca
  v2 já montada, verificando integridade de outros arquivos.
- `feature_sources/offline_sst_field_catalog_v3_test.dart` — testes com
  integração da interface existente, executados na montagem completa do app.
- `feature_sources/offline_sst_field_catalog_v3_pure_test.dart` — testes de
  conteúdo e filtros para uma fixture Flutter isolada.
- `.github/workflows/validate-offline-field-catalog-v3.yml` — integração
  e regressão isoladas.

## Referências para revisão normativa

- Ministério do Trabalho e Emprego — [Normas Regulamentadoras Vigentes](https://www.gov.br/trabalho-e-emprego/pt-br/acesso-a-informacao/participacao-social/conselhos-e-orgaos-colegiados/comissao-tripartite-partitaria-permanente/normas-regulamentadora/normas-regulamentadoras-vigentes).
- NR-12 e NR-18 são referências temáticas para máquinas e construção civil.
- Atualização periódica das NRs deve ser revisada antes de divulgar enquadramentos
  específicos ou publicar um relatório com fundamentação normativa.

**Situação:** somente código em branch de homologação, sem APK novo instalado
e sem atualização da Central de produção.

## Ampliação complementar em 06/11/2026 — +24 casos

Foram adicionadas 24 situações com descrição, risco, consequência possível, recomendação, prioridade inicial, referência temática de NR e regras de correspondência tema + falha. **O total desta linha de catálogo detalhado é agora 228 (145 + 59 + 24)**. Não somar esse número com o catálogo de 345 modelos da PR #28: são branches independentes e exigem integração/deduplicação antes de divulgar total consolidado.

Distribuição dos novos casos: panificação 6, construção civil 4, cerâmica 3, laticínios 3, limpeza urbana 3, logística 2 e gerais 3.

Casos exemplares: cilindro com emergência inacessível, masseira com grade removida, fatiadora com lâmina exposta, andaime com piso incompleto, painel com inflamável próximo, empacotadora com emergência inoperante, frente de varrição sem sinalização e extintor com lacre rompido.

Foram atualizados os dois conjuntos de testes do catálogo para 228 entradas e suas contagens setoriais. **Não foi executada compilação completa Android/Windows ou homologação em dispositivo real neste passo.** A regra de correspondência não dispensa revisão do TST, não mede exposição e não cria NC automaticamente.
