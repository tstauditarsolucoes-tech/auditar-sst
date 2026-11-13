# Minha CIPA — rascunho protegido e envio idempotente

**Somente desenvolvimento e homologação**, sem merge, APK distribuído ou mudanças no aplicativo operacional Auditar SST. A base é a PR #57 (fotos privadas), que depende das PRs #56, #47, #46 e anteriores.

## No aparelho Android

- O roteiro guiado conserva tema, setor/local informado, três respostas, observação livre e até duas fotos previamente reduzidas.
- O conteúdo vai para arquivo no **diretório interno do aplicativo**, cifrado em **AES-256-GCM**, autenticado contra adulteração. A chave de 256 bits é armazenada separadamente no cofre seguro do sistema operacional. O arquivo nunca contém token de login nem chave técnica do Auditar SST.
- Rascunhos são separados por **conta, empresa, mandato, membro e agendamento**. O app só tenta abrir um rascunho quando a sessão individual já foi validada pelo servidor.
- Há autosave com janela curta, salvamento na ida para segundo plano e botão **Guardar e sair**, e recuperação após reiniciar o app e entrar com a mesma conta. O salvamento no último instante antes de encerramento forçado pelo sistema depende das garantias do SO e deve ser testado fisicamente.
- O ID estável de envio é gravado junto com o rascunho **antes** da primeira tentativa. Caso o servidor grave o relato e ocorra falha na transferência das fotos, uma nova tentativa utiliza o mesmo ID; o backend rejeita duplicações e substituições conflitantes.
- O envio posterior é **manual ao recuperar conexão e login**; não existe envio de fotos em background ou fila automática sem sessão. Nenhum membro consegue enviar sem autenticação válida.
- A saída intencional e a revogação detectada da sessão apagam os rascunhos locais do vínculo. Conteúdo antigo (acima de sete dias) não é restaurado. Revogação não pode ser detectada pelo aparelho enquanto está totalmente offline.

## Riscos e restrições ainda a homologar

1. Falhas de energia e interrupção do app durante gravação ou câmera, inclusive enquanto outro rascunho é sobrescrito. Validar atomicidade do rename no Android-alvo.
2. Migração de chaves do KeyStore, cópias de segurança e reinstalação; se o cofre perder a chave, o ciphertext deve falhar fechado, não aparecer para outra pessoa.
3. Teste manual em duas empresas e em membro revogado. Verificar isolamento, retenção de fotos e exclusão.
4. Teste de rede intermitente em duas etapas (relato registrado / foto 1 enviada / foto 2 pendente), mantendo o mesmo requestId.
5. Revisão de LGPD, política de retenção, backups e autorização explícita do responsável antes de ativar o portal.

**Os testes automatizados não substituem a homologação em celular físico.**
