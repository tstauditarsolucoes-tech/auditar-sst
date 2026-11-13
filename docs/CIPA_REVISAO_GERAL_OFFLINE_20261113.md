# Minha CIPA — revisão geral do app opcional (13/11/2026)

**Escopo:** PR #63 sobre PR #62, sem alterar o aplicativo técnico Auditar SST instalado, nem publicar o portal da Central. Os recursos descritos são experimentais e precisam de homologação em aparelhos reais.

## Experiência do integrante
- A consulta pessoal e as vistorias continuam com botões simples, três perguntas guiadas, até duas fotografias e linguagem acessível.
- A tela **Vistorias salvas no celular** agora exibe a quantidade de perguntas respondidas, fotos protegidas, data e hora do último salvamento, além das categorias de prontas, incompletas e bloqueadas.
- Ao tocar em **Enviar vistorias salvas**, o integrante recebe uma prévia clara das vistorias prontas, incompletas e bloqueadas e da quantidade de fotos. O envio só começa após confirmação expressa.
- Antes de cada transmissão, o aplicativo revalida identidade, empresa, mandato e integrante com a Central. Rascunhos incompletos ou agendas retiradas não são enviados automaticamente.
- Erro ao atualizar o histórico depois de uma ação não aparece como erro de transmissão, evitando induzir o membro a enviar a mesma ocorrência novamente.

## Proteção e recuperação
- Arquivos de vistoria usam AES-256-GCM com chave separada no armazenamento seguro do Android, por usuário/empresa/mandato/membro.
- Caso o aplicativo seja interrompido depois de terminar de escrever o arquivo temporário, mas antes de renomeá-lo, a próxima abertura/listagem tenta recuperar o conteúdo **somente se a autenticação do arquivo e os metadados estiverem válidos**.
- Se houver arquivo principal e temporário, o arquivo principal permanece a referência: um temporário parcial não substitui o arquivo já confirmado em disco.
- Arquivos inválidos, vencidos ou de agendamentos retirados aparecem como pendentes de suporte e não são silenciosamente destruídos pela rotina de sincronização.
- A expiração de rascunhos usa uma diferença de tempo precisa de 7 dias e rejeita datas de salvamento excessivamente futuras.
- O modo de consulta offline mantém o limite de **24 horas** após a última atualização autenticada. Um marcador de data protegido no armazenamento seguro detecta retrocesso abrupto do relógio e pede nova validação online. **Isso não impede toda manipulação de tempo do aparelho**.

## Testes adicionados
- Recuperação de arquivo após renomeação interrompida; preservação de múltiplos registros.
- Recusa de rascunhos com vencimento ou data futura indevida.
- Rejeição de relógio retrocedido e recuperação após autenticação online.
- Prévia de envio com contagem de pendências prontas, incompletas, bloqueadas e fotos.
- Validação existente de duas empresas, mudanças de mandato, foto privada, envio idempotente e acesso por PIN.

## Critérios antes da liberação
1. Integração autenticada com Central CIPA real, permissões de membros e armazenamento de fotos realmente privado.
2. Testes em Android físico, incluindo reinicialização, baixa bateria, rede intermitente, upload incompleto de fotos e relógio alterado.
3. Revisão LGPD: consentimento/base legal aplicável, retenção, exclusão, compartilhamento do aparelho e procedimento de suporte para registros bloqueados.
4. Validação de acessibilidade com cipeiros que não têm facilidade com smartphone.
5. Aprovação de piloto, build Android separado e distribuição controlada. A compilação automatizada de homologação não implica aprovação de produção.

**Situação:** recursos em PR draft. Nenhum merge, deploy real ou APK distribuído.
