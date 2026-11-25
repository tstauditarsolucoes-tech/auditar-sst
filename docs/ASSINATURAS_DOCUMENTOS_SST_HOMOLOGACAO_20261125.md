# Auditar SST — assinatura na tela em APR, AR, PT e PET (homologação)

## O que foi acrescentado
- Componente reutilizável de **assinatura manuscrita na tela** por dedo
  (Android) ou mouse (Windows), aproveitando a dependência Flutter
  signature já utilizada na Central de Relatórios SST.
- Campos de **nome completo e função declarados** pelo signatário,
  consentimento explícito de que se trata de **ciência / revisão da MINUTA**,
  imagem do traço, data/hora registradas em UTC e papel da ciência.
- APR e AR: elaborador e responsável pela revisão técnica.
- PT: elaborador e responsável pela conferência (NÃO autorizadora).
- PET NR-33: supervisor de entrada e vigia, ambos como mera rubrica
  de ciência da minuta (NÃO certificados / NÃO liberam entrada).
- Inclusão opcional das assinaturas de ciência no PDF A4 da versão
  correspondente, sem modificar PDF de vistoria tradicional.
- Permite substituir uma rubrica do mesmo papel, após nova declaração.
- Persistência de PNG em base64 no settings local existente, por
  **usuário + empresa + tipo + identificador do documento**.
  Não há envio automático de assinatura, nuvem, Apps Script ou criação
  de nova tabela/banco neste estágio.

## Proteção contra documentos alterados
Cada registro de assinatura armazena cópia textual do JSON do documento
que estava exibido no instante da rubrica. Se qualquer campo for editado,
a comparação exata falha: a rubrica antiga é marcada como desatualizada
e **não entra no novo PDF**. É necessário assinar novamente.
Isto é apenas bloqueio local de uso indevido, NÃO assinatura criptográfica,
não garante integridade contra adulteração de banco ou do dispositivo
e NÃO autentica o signatário.
O histórico arquivado pode continuar exibindo a ciência da versão
antiga se corresponder ao seu próprio conteúdo.

## O que não foi implementado
- Assinatura digital qualificada (ICP-Brasil), PAdES, certificação de
  assinatura, autenticação forte de cada signatário ou trilha confiável.
- Aprovação/emissão/revalidação/encerramento efetivo de PT ou PET.
- Controle de assinatura por supervisor/vigia autenticados individualmente.
- Retenção obrigatória e acesso permanente ao vigia para PET digital.
- Sincronização ou validação criptográfica do documento.
- A rubrica manuscrita pode ter utilidade documental de ciência,
  mas **não equivale a autorização de trabalho nem atende, por si só,
  os requisitos de certificação da PET digital**.

## Referências normativas públicas
- NR-33, itens 33.5.5–33.5.9: PET antes da entrada; assinatura de
  supervisor/vigia; emissão física/digital; PET digital acessível
  permanentemente ao vigia e certificação de assinatura conforme NR-01.
  PDF oficial:
  https://www.gov.br/trabalho-e-emprego/pt-br/acesso-a-informacao/participacao-social/conselhos-e-orgaos-colegiados/comissao-tripartite-partitaria-permanente/arquivos/normas-regulamentadoras/nr-33-atualizada-2022-_retificada.pdf
- NR-35, item 35.5.8: PT necessita aprovação por responsável definido;
  acesso no local, encerramento e arquivamento.

## Homologação
- Rodar preflight: python3 tools/test_sst_document_signatures_v1.py
- Rodar regressões anteriores APR/AR/PT/PET.
- Testes Dart: test/sst_document_signature_test.dart
- Flutter format/analyze, builds completos Android/Windows.
- Conferir gesto, câmera/trackpad/mouse, nome/cargo, PNG e PDF impresso.
- Simular texto alterado após assinar (assinatura deve ficar desatualizada);
  troca de empresa/conta/tipo; assinatura vazia, cancelada, inválida;
  rascunho antigo, PDFs arquivados e falha de armazenamento local.
- Analisar requisitos de LGPD, proteção de dados, backup, autenticação
  e eventual integração futura com prestador de assinatura certificada.
- Não publicar, instalar ou mesclar sem revisão, testes e aprovação.
