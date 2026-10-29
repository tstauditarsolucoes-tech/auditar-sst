// Ferramenta local de homologacao: senha pela entrada padrao, nunca por argv/env.
import {hashPassword} from './authService.mjs';
let value='';
for await (const chunk of process.stdin) {
  value+=chunk.toString('utf8');
  if (value.length>512) throw new Error('Entrada de senha longa demais');
}
if (value.includes('\n')||value.includes('\r')) throw new Error('Senha deve ser enviada sem quebra de linha');
process.stdout.write(await hashPassword(value)+'\n');
