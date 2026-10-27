/**
 * Sessões NATIVAS de homologação, separadas do cookie Web.
 * Somente login/consulta/logout; NUNCA usar bearer para endpoints de negocio
 * antes de implementar um protocolo novo, isolado do Apps Script/Flutter atual.
 */
import {createHash,randomBytes} from 'node:crypto';
import {ApiError} from './ncService.mjs';
import {verifyPassword} from './authService.mjs';
const TOKEN=/^[A-Za-z0-9_-]{43}$/;
const AUTH_PREFIX='Bearer ';
const TTL_MINUTES=30;
const LOGIN_MESSAGE='Credenciais invalidas ou conta sem acesso';
// Mesmo verificador sintético do authService: impede caminho mais rápido em emails inexistentes.
const DUMMY='scrypt$131072$8$1$8ee14d963363a557534aaeee01e41a11$9341afbb464041474db2f3c691b19572efb22a62c5df3b0936a826982c052627bc7b7c3398738a44de51ced864541685a0f186b61f09a68cec5b2589d099d7ec';
const hash=v=>createHash('sha256').update(v,'utf8').digest('hex');

async function withAuth(pool,fn){
  if(!pool||typeof pool.connect!=='function')
    throw new ApiError(503,'AUTH_UNAVAILABLE','Autenticacao nativa indisponivel');
  const db=await pool.connect();
  let active=false;
  try{
    await db.query('BEGIN');active=true;
    await db.query('SET LOCAL ROLE sst_auth_runtime');
    const r=await fn(db);
    await db.query('COMMIT');return r;
  }catch(err){
    if(active){try{await db.query('ROLLBACK');}catch{}}
    throw err;
  }finally{db.release();}
}
function rejectBrowser(req){
  // Esta rota nao pertence ao login Web: recusa navegadores com Origin/Cookie.
  // Apps nativos HTTPS nao precisam de cookie, CSRF nem permissao de CORS.
  if(req.headers.origin||req.headers.cookie)
    throw new ApiError(403,'NATIVE_ONLY','Utilize a sessao Web no navegador');
}
function tokenOf(req){
  const raw=req?.headers?.authorization;
  if(typeof raw!=='string'||!raw.startsWith(AUTH_PREFIX))return null;
  const token=raw.slice(AUTH_PREFIX.length);
  return TOKEN.test(token)?token:null;
}
export function createNativeAuthService({pool}={}){
  return {
    async login(req,body={}){
      rejectBrowser(req);
      // Nao receber outras informacoes como deviceId, companyId, syncKey ou registros.
      if(!body||typeof body!=='object'||Array.isArray(body)||
          Object.keys(body).some(x=>!['email','password'].includes(x)))
        throw new ApiError(400,'INVALID_INPUT','Apenas email e senha novos');
      const {email,password}=body;
      if(typeof email!=='string'||email.length<5||email.length>254||
         typeof password!=='string'||password.length<1||password.length>256)
        throw new ApiError(401,'LOGIN_FAILED',LOGIN_MESSAGE);
      const normalized=email.trim().toLowerCase();
      const identityHash=hash(normalized);
      const attempts=await withAuth(pool,async db=>{
        const r=await db.query(
          'INSERT INTO sst.auth_login_counter(identity_hash,attempt_count,window_start,updated_at) '+
          'VALUES($1,1,now(),now()) ON CONFLICT(identity_hash) DO UPDATE SET '+
          "attempt_count=CASE WHEN sst.auth_login_counter.window_start < now()-interval '15 minutes' "+
          'THEN 1 ELSE least(sst.auth_login_counter.attempt_count+1,1000) END, '+
          "window_start=CASE WHEN sst.auth_login_counter.window_start < now()-interval '15 minutes' "+
          'THEN now() ELSE sst.auth_login_counter.window_start END,updated_at=now() '+
          'RETURNING attempt_count',[identityHash]);
        return r.rows[0].attempt_count;
      });
      if(attempts>10)throw new ApiError(429,'LOGIN_THROTTLED','Aguarde para tentar novamente');
      const found=await withAuth(pool,async db=>{
        const r=await db.query(
          'SELECT u.id,u.display_name,u.active,a.password_verifier FROM sst.app_user u '+
          'JOIN sst.auth_credential a ON a.user_id=u.id '+
          'WHERE lower(u.email)=$1 LIMIT 1',[normalized]);
        return r.rows[0]||null;
      });
      const valid=await verifyPassword(password,found?.password_verifier||DUMMY);
      if(!found?.active||!valid)throw new ApiError(401,'LOGIN_FAILED',LOGIN_MESSAGE);
      const membership=await withAuth(pool,async db=>{
        const r=await db.query(
          'SELECT m.company_id,m.role FROM sst.user_company_role m '+
          'JOIN sst.company c ON c.id=m.company_id '+
          "WHERE m.user_id=$1 AND m.active AND c.status='ativa' "+
          'ORDER BY m.company_id LIMIT 1',[found.id]);
        return r.rows[0]||null;
      });
      if(!membership)throw new ApiError(401,'LOGIN_FAILED',LOGIN_MESSAGE);
      const token=randomBytes(32).toString('base64url');
      await withAuth(pool,db=>db.query(
        'INSERT INTO sst.native_session(token_hash,user_id,company_id,expires_at) '+
        "VALUES($1,$2,$3,now()+interval '30 minutes')",
        [hash(token),found.id,membership.company_id],
      ));
      await withAuth(pool,db=>db.query(
        'DELETE FROM sst.auth_login_counter WHERE identity_hash=$1',[identityHash]));
      return {
        ok:true,token,tokenType:'Bearer',expiresInSeconds:TTL_MINUTES*60,
        user:{id:found.id,name:found.display_name},
        companyId:membership.company_id,role:membership.role,
        syncEnabled:false,writesEnabled:false,
      };
    },
    async session(req){
      rejectBrowser(req);
      const token=tokenOf(req);
      if(!token)throw new ApiError(401,'UNAUTHENTICATED','Token nativo ausente');
      const item=await withAuth(pool,async db=>{
        const r=await db.query(
          'SELECT s.user_id,s.company_id,u.display_name,m.role,s.expires_at '+
          'FROM sst.native_session s '+
          'JOIN sst.app_user u ON u.id=s.user_id '+
          'JOIN sst.auth_credential a ON a.user_id=s.user_id '+
          'JOIN sst.user_company_role m ON m.company_id=s.company_id AND m.user_id=s.user_id '+
          'JOIN sst.company c ON c.id=s.company_id '+
          'WHERE s.token_hash=$1 AND s.revoked_at IS NULL AND s.expires_at>now() '+
          "AND s.issued_at>=a.changed_at AND u.active AND m.active AND c.status='ativa' "+
          'LIMIT 1',[hash(token)]);
        return r.rows[0]||null;
      });
      if(!item)throw new ApiError(401,'UNAUTHENTICATED','Sessao expirada ou revogada');
      return {ok:true,user:{id:item.user_id,name:item.display_name},
        companyId:item.company_id,role:item.role,
        expiresAt:item.expires_at,syncEnabled:false,writesEnabled:false};
    },
    async logout(req){
      rejectBrowser(req);
      const token=tokenOf(req);
      if(!token)throw new ApiError(401,'UNAUTHENTICATED','Token nativo ausente');
      const result=await withAuth(pool,async db=>{
        const r=await db.query(
          'UPDATE sst.native_session SET revoked_at=now() '+
          'WHERE token_hash=$1 AND revoked_at IS NULL AND expires_at>now() '+
          'RETURNING id',[hash(token)]);
        return r.rowCount;
      });
      if(!result)throw new ApiError(401,'UNAUTHENTICATED','Sessao expirada ou revogada');
      return {ok:true};
    },
  };
}
