# Auditar SST — investigação guiada de acidentes e incidentes

## Objetivo
Aproveitar o modelo de investigação que já existia na Central de Relatórios SST
e oferecer ao Técnico de Segurança do Trabalho um roteiro compreensível.

**Não é outro banco, outra tela de cadastro, nem automação de CAT.**

## Onde abrir
Android e Windows, após homologação:
Empresa > Central de Relatórios SST > Investigação guiada de acidente/incidente.

## Implementação na branch experimental
- Guia de seis etapas: atendimento/segurança, dados e cronologia, fontes e
  entrevistas, ambiente e organização, fatores/cinco porquês, medidas e eficácia.
- Botões abrem as nove perguntas correspondentes no formulário existente.
- Rascunhos são os existentes, locais e separados por conta/empresa.
- Fotografias, PDF e assinatura usam os recursos já existentes.
- A instalação acrescenta um novo arquivo de tela ao patch da Central de
  Relatórios, sem alterar sync, banco, autenticação, GS ou PDF.
- O assistente é orientativo: não usa IA generativa nem inventa fatos.
- A navegação entre etapas é temporária; os dados digitados são salvos pelos
  controles do formulário original.

## Proteções e limites
1. Atendimento à vítima e controle de riscos têm prioridade.
2. Distinguir relato, observação e hipótese; não atribuir culpa/nexo.
3. CAT/eSocial são obrigações separadas; o aplicativo NÃO as transmite.
4. Não coletar CPF, prontuário ou dados clínicos desnecessários no rascunho.
5. O armazenamento local atual precisa de avaliação de privacidade antes de
   uso com dados pessoais sensíveis.
6. Registrar ações, responsáveis, prazos, evidências e eficácia; avaliar revisão
   do PGR de acordo com a NR-1.
7. Não marcar relatório como definitivo sem conferência técnica.
8. Instalação bloqueada até CI integral, teste físico e backup.
9. PR em rascunho; sem publicação automática.

## Plano de testes
- Preflight Python verifica as seis etapas e os nove links do formulário.
- Rodar integração Android e Windows, Dart format, flutter analyze e flutter test.
- No Android: testar janela 360px, scroll, rascunho, fotos e PDF sem internet.
- No Windows: testar janela reduzida, PDF e contas/empresas distintas.
- Utilizar dados fictícios.
- Conferir compatibilidade com a PR #75 antes de solicitar merge.

Referências: NR-1 1.5.5.5 (análise de acidentes), eSocial S-2210 (CAT).
