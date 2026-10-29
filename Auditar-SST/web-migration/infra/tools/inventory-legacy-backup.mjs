/**
 * Auditoria LOCAL/READ-ONLY de copia de backup feita pelo proprietario.
 * Nao le Drive/Sheets/Apps Script nem envia arquivos para nenhum destino.
 * Nao imprime nomes/conteudos/IDs de clientes: so contagens, tamanhos e duplicatas.
 */
import {createReadStream} from 'node:fs';
import {readdir,lstat,realpath} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {basename,extname,resolve,join} from 'node:path';
import {homedir} from 'node:os';
const MAX_FILES=100000;
const MAX_DEPTH=15;
const types=new Set(['.json','.csv','.tsv','.txt','.pdf','.jpg','.jpeg','.png','.webp','.zip','.xlsx','.docx']);
function permitted(root){
  if(typeof root!=='string'||!root.startsWith('/'))throw new Error('Informe caminho absoluto de copia local');
  const path=resolve(root);
  if(path==='/'||path===homedir()||path===process.cwd()||
      !basename(path).startsWith('auditar-sst-backup-')) {
    throw new Error('Caminho negado: use pasta exclusiva auditar-sst-backup-NOME, fora do repositorio');
  }
  return path;
}
async function shaFile(path){
  const hasher=createHash('sha256');
  for await(const chunk of createReadStream(path,{highWaterMark:65536}))hasher.update(chunk);
  return hasher.digest('hex');
}
export async function inventory(path){
  const root=permitted(path);
  const real=await realpath(root);
  if(root!==real)throw new Error('Raiz nao pode ser link simbolico');
  const st=await lstat(root);
  if(!st.isDirectory()||st.isSymbolicLink())throw new Error('Origem deve ser pasta real');
  const result={mode:'readonly',source:'backup local copiado previamente',files:0,bytes:0,
    skippedSymlinks:0,duplicateCount:0,duplicateBytes:0,byType:{}};
  const seen=new Set();
  const stack=[{path:root,depth:0}];
  while(stack.length){
    const item=stack.pop();
    if(item.depth>MAX_DEPTH)throw new Error('Profundidade acima de limite, inspecione manualmente');
    const dir=await readdir(item.path,{withFileTypes:true});
    for(const entry of dir){
      if(entry.name.startsWith('.'))continue;
      const child=join(item.path,entry.name);
      if(entry.isSymbolicLink()){result.skippedSymlinks++;continue;}
      if(entry.isDirectory()){stack.push({path:child,depth:item.depth+1});continue;}
      const s=await lstat(child);
      if(!s.isFile()||s.isSymbolicLink())continue;
      if(++result.files>MAX_FILES)throw new Error('Limite de arquivos excedido');
      const ext=extname(entry.name).toLowerCase();
      const kind=types.has(ext)?ext:'outro';
      if(!result.byType[kind])result.byType[kind]={files:0,bytes:0};
      result.byType[kind].files++;
      result.byType[kind].bytes+=s.size;
      result.bytes+=s.size;
      const hash=await shaFile(child);
      const digest=hash+' '+s.size;
      if(seen.has(digest)){result.duplicateCount++;result.duplicateBytes+=s.size;}
      else seen.add(digest);
    }
  }
  return result;
}
if(process.argv[1]&&new URL(import.meta.url).pathname===resolve(process.argv[1])){
  const value=process.argv[2];
  if(process.argv.length!==3)throw new Error('Uso: node inventory-legacy-backup.mjs /local/auditar-sst-backup-NOME');
  try{
    const result=await inventory(value);
    process.stdout.write(JSON.stringify(result,null,2)+'\n');
  }catch(e){
    process.stderr.write('INVENTARIO NAO REALIZADO: '+(e instanceof Error?e.message:'erro')+'\n');
    process.exitCode=1;
  }
}
