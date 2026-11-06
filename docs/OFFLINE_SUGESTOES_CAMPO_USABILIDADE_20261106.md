# Auditar SST — Sugestões de relatório offline mais práticas no campo

Data: 06/11/2026. Escopo: acabamento aditivo sobre a interface atual.

## O que não muda
- Botões originais **Aplicar**, **Ajustar**, **Outras opções** e **Consultar biblioteca por NR** continuam disponíveis.
- Mesmos formulários de vistoria, Ronda Expressa e campos do relatório.
- O sistema não confirma automaticamente uma NC, norma aplicável, medição, risco ou status de ação.
- Nenhuma mudança no banco, identidade dos registros, login, sincronização, fotos, IA online, PDFs, Central Online ou aprendizado persistido.
- Nenhuma atualização é enviada ao aplicativo instalado enquanto não for compilada e homologada.

## Melhoria 1 — Atalhos quando o campo ainda está vazio
Ao iniciar o preenchimento, a consulta por NR continua aparecendo e ganha quatro chips compactos:
- **Extintor**: abre a biblioteca com `extintor` preenchido na pesquisa.
- **Máquinas**: abre a biblioteca filtrada por **NR-12**.
- **Altura**: abre a biblioteca filtrada por **NR-35**.
- **EPI**: abre a biblioteca filtrada por **NR-06**.

Os atalhos levam à mesma biblioteca já instalada e não geram uma não conformidade sozinhos. Ao digitar uma descrição normal, o comportamento de sugestão atual permanece.

## Melhoria 2 — “Não corresponde” em um toque
- No cartão da sugestão principal, um pequeno botão com X e dica **Não corresponde à situação** retira a opção inadequada da lista para aquela descrição.
- A próxima sugestão ainda disponível pode aparecer sem a necessidade de refazer o relatório.
- A opção também aparece dentro da janela **Revisar sugestão sem IA**.
- **O texto digitado e os campos do relatório permanecem intactos.**
- O item não é apagado do acervo, não é tratado como fato provado e não vira erro global para outras empresas.
- Ao mudar a descrição ou contexto do registro, as opções ignoradas nesta busca voltam a ser pesquisáveis normalmente.
- Nunca executar `onSelected` ao ignorar. Não chamar `learnApplied` ao ignorar.

## Por que a intervenção é deliberadamente pequena
A tela atual já possui busca por palavras, triagem segura, modelos da biblioteca técnica, revisão de texto e inserção consciente da sugestão. Alterar o mecanismo ou criar outra tela poderia gerar regressões em campo. Esta melhoria é exclusivamente uma camada de **usabilidade**.

## Validação
- Patch `tools/patch_offline_field_usability_v1.py` é aplicado **depois** da biblioteca aprofundada `patch_sst_deep_catalog_v2.py`.
- Verifica hashes SHA-256 de todos os demais arquivos `lib` e Apps Script; falha se detectar mudança externa ao widget.
- Bloqueia aplicação duplicada do patch.
- Fixture Flutter com regras reais de sugestão local e biblioteca de navegação simulada verifica os botões, o X de descarte, o diálogo, a ausência de aplicação automática e o retorno das opções depois de editar o texto.
- A integração à montagem Android será testada após o conjunto de patches atual, sem substituição da versão instalada.

**Estado:** implementação de homologação em branch isolada; ainda não instalada nem publicada.
