/**
 * ATIVACAO OPT-IN SOMENTE HOMOLOGACAO PRIVADA.
 * Container padrao permanece sem auth e sem acesso a dados.
 */
import { readFile } from 'node:fs/promises';
import pg from 'pg';
import { createApp } from './server.mjs';
import { createAuthService } from './authService.mjs';
import { createNativeAuthService } from './nativeAuthService.mjs';

function configuration() {
  if (typeof process.getuid==='function' && process.getuid()===0) {
    throw new Error('Servidor Node nao pode rodar como root');
  }
  if (process.env.AUDITAR_ENABLE_PRIVATE_AUTH !== 'PRIVATE_STAGING_CONFIRMED') {
    throw new Error('A ativacao privada exige confirmacao explicita');
  }
  const allowedOrigin=process.env.AUDITAR_ALLOWED_ORIGIN || '';
  let origin;
  try {origin=new URL(allowedOrigin);} catch {throw new Error('Origin HTTPS invalido');}
  if (origin.protocol !== 'https:' || origin.origin !== allowedOrigin ||
      origin.username || origin.password || origin.pathname !== '/' ||
      origin.search || origin.hash ||
      origin.hostname.toLowerCase() === 'tst.auditarsolucoes.com.br') {
    throw new Error('Use URL HTTPS exclusiva de HOMOLOGACAO, diferente do dominio final');
  }
  const port=Number(process.env.PORT||3000);
  if (!Number.isInteger(port)||port<1||port>65535) throw new Error('PORT invalida');
  if (process.env.PGHOST !== 'db' ||
      process.env.PGDATABASE !== 'auditar_web_hml') {
    throw new Error('Banco diferente do projeto dedicado de homologacao');
  }
  const dataUser=process.env.AUDITAR_DATA_DB_USER||'';
  const authUser=process.env.AUDITAR_AUTH_DB_USER||'';
  const validName=/^[a-z][a-z0-9_]{2,45}$/;
  if (!validName.test(dataUser)||!validName.test(authUser)||dataUser===authUser) {
    throw new Error('Usuarios DB restritos distintos obrigatorios');
  }
  const evidenceDir=process.env.AUDITAR_EVIDENCE_DIR;
  if(evidenceDir!=='/var/lib/auditar-staging/evidence'){
    throw new Error('Volume dedicado de fotos da homologacao obrigatorio');
  }
  return {allowedOrigin,port,dataUser,authUser,evidenceDir};
}
async function secret(path) {
  if (!/^\/run\/auditar-private\/(data_db_password|auth_db_password)$/.test(path||'')) {
    throw new Error('Secret deve estar em tmpfs privado');
  }
  const value=(await readFile(path,'utf8')).trim();
  if (value.length<24) throw new Error('Secret de DB curto ou ausente');
  return value;
}
async function verifyPool(pool,role) {
  const client=await pool.connect();
  try {
    const result=await client.query(
      'SELECT rolname,rolsuper,rolbypassrls,rolcreaterole,rolcreatedb '+
      'FROM pg_roles WHERE rolname=current_user',
    );
    const current=result.rows[0];
    if (!current || current.rolsuper || current.rolbypassrls ||
        current.rolcreaterole || current.rolcreatedb) {
      throw new Error('Conexao privilegiada rejeitada; somente role limitado');
    }
    await client.query('BEGIN');
    try {
      // Testa se a identidade tem somente a funcao para a qual foi provisionada.
      await client.query('SET LOCAL ROLE '+role);
      await client.query('SELECT 1');
      await client.query('ROLLBACK');
    } catch (error) {
      await client.query('ROLLBACK');
      throw error;
    }
  } finally {client.release();}
}

const config=configuration();
const [dataPassword,authPassword]=await Promise.all([
  secret(process.env.AUDITAR_DATA_DB_PASSWORD_FILE||'/run/auditar-private/data_db_password'),
  secret(process.env.AUDITAR_AUTH_DB_PASSWORD_FILE||'/run/auditar-private/auth_db_password'),
]);
const base={host:'db',port:5432,database:'auditar_web_hml',
  max:4,connectionTimeoutMillis:6000,idleTimeoutMillis:10000};
const dataPool=new pg.Pool({...base,user:config.dataUser,password:dataPassword});
const authPool=new pg.Pool({...base,user:config.authUser,password:authPassword});
try {
  await Promise.all([
    verifyPool(dataPool,'sst_app_runtime'),
    verifyPool(authPool,'sst_auth_runtime'),
  ]);
} catch (error) {
  await Promise.all([dataPool.end(),authPool.end()]);
  throw error;
}
const authService=createAuthService({pool:authPool,allowedOrigin:config.allowedOrigin});
// Opt-in separado e explicito, por padrão INATIVO até na VPS privada.
const nativeAuthService=process.env.AUDITAR_ENABLE_NATIVE_AUTH==='PRIVATE_STAGING_NATIVE_ONLY'
  ?createNativeAuthService({pool:authPool}):undefined;
// Escritas de rascunhos NOVOS requerem um segundo opt-in independente.
const nativeDraftsEnabled=Boolean(nativeAuthService) &&
  process.env.AUDITAR_ENABLE_NATIVE_DRAFTS==='PRIVATE_STAGING_NATIVE_DRAFTS_ONLY';
const server=createApp({pool:dataPool,authService,nativeAuthService,nativeDraftsEnabled,
  evidenceDir:config.evidenceDir});
let closing=false;
async function close() {
  if (closing) return;
  closing=true;
  await new Promise(resolve=>server.close(()=>resolve()));
  await Promise.all([dataPool.end(),authPool.end()]);
}
process.on('SIGTERM',()=>{void close();});
process.on('SIGINT',()=>{void close();});
dataPool.on('error',()=>{ /* nao imprimir segredos/conexao */ });
authPool.on('error',()=>{ /* nao imprimir segredos/conexao */ });
server.listen(config.port,'0.0.0.0');
