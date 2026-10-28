import {randomBytes,createHash} from 'node:crypto';
import {ApiError} from './ncService.mjs';
import {hashPassword,verifyPassword,requireOrigin,requireCsrf,csrfForToken} from './authService.mjs';
export const CIPA_COOKIE='__Host-auditar-cipa';
const TOKEN=/^[A-Za-z0-9_-]{43}$/;
const UUID=/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const DUMMY='scrypt$131072$8$1$8ee14d963363a557534aaeee01e41a11$9341afbb464041474db2f3c691b19572efb22a62c5df3b0936a826982c052627bc7b7c3398738a44de51ced864541685a0f186b61f09a68cec5b2589d099d7ec';
const digest=x=>createHash('sha256').update(x).digest('hex');
export function cipaToken(req){
  const raw=req?.headers?.cookie;
  if(typeof raw!=='string'||raw.length>4096)return null;
  const matches=raw.split(';').map(s=>s.trim().split('=')).filter(p=>p[0]===CIPA_COOKIE);
  return matches.length===1&&matches[0].length===2&&TOKEN.test(matches[0][1]||'')?matches[0][1]:null;
}
function cookie(token,clear=false){return `${CIPA_COOKIE}=${token}; Path=/; HttpOnly; Secure; SameSite=Strict; Max-Age=${clear?0:7200}`;}
async function authTx(pool,fn){
  if(!pool)throw new ApiError(503,'CIPA_PORTAL_DISABLED','Portal indisponivel');
  const db=await pool.connect();
  try{await db.query('BEGIN');await db.query('SET LOCAL ROLE sst_auth_runtime');
    const result=await fn(db);await db.query('COMMIT');return result;
  }catch(e){await db.query('ROLLBACK').catch(()=>{});throw e;}finally{db.release();}
}
async function issue(db,account){
  const token=randomBytes(32).toString('base64url');
  await db.query('INSERT INTO sst.cipa_portal_session(token_hash,company_id,account_id) VALUES($1,$2,$3)',
    [digest(token),account.company_id,account.id]);
  return {cookie:cookie(token),body:{ok:true,name:account.display_name,companyId:account.company_id,
    mustChangePassword:account.must_change_password,csrfToken:csrfForToken(token)}};
}
export function createCipaPortalAuth({pool,allowedOrigin}){
  if(!allowedOrigin?.startsWith('https://')||new URL(allowedOrigin).origin!==allowedOrigin)throw new Error('CIPA requires fixed HTTPS origin');
  return {
    async login(req,body={}){
      requireOrigin(req,allowedOrigin);
      const {companyId,email,password}=body;
      if(!UUID.test(companyId||'')||typeof email!=='string'||email.length>254||
        typeof password!=='string'||password.length>256)throw new ApiError(401,'LOGIN_FAILED','Acesso nao confirmado');
      const normalized=email.trim().toLowerCase();
      const key=digest('cipa:'+companyId.toLowerCase()+':'+normalized);
      const attempts=await authTx(pool,async db=>(await db.query(
        "INSERT INTO sst.auth_login_counter(identity_hash,attempt_count,window_start,updated_at) VALUES($1,1,now(),now()) "+
        "ON CONFLICT(identity_hash) DO UPDATE SET attempt_count=CASE WHEN sst.auth_login_counter.window_start<now()-interval '15 minutes' "+
        "THEN 1 ELSE least(sst.auth_login_counter.attempt_count+1,1000) END, window_start=CASE WHEN "+
        "sst.auth_login_counter.window_start<now()-interval '15 minutes' THEN now() ELSE sst.auth_login_counter.window_start END, updated_at=now() RETURNING attempt_count",[key])).rows[0].attempt_count);
      if(attempts>10)throw new ApiError(429,'LOGIN_THROTTLED','Aguarde para tentar novamente');
      const found=await authTx(pool,async db=>(await db.query(
        "SELECT a.* FROM sst.cipa_portal_account a JOIN sst.company c ON c.id=a.company_id "+
        "WHERE a.company_id=$1 AND a.email=$2 AND c.status='ativa'",[companyId,normalized])).rows[0]);
      const valid=await verifyPassword(password,found?.password_verifier||DUMMY);
      if(!found?.active||!valid)throw new ApiError(401,'LOGIN_FAILED','Acesso nao confirmado');
      return authTx(pool,async db=>{
        // Lock and recheck after expensive password verification (reset/revocation race).
        const row=(await db.query('SELECT * FROM sst.cipa_portal_account WHERE company_id=$1 AND id=$2 FOR UPDATE',
          [found.company_id,found.id])).rows[0];
        if(!row?.active||row.password_verifier!==found.password_verifier)throw new ApiError(401,'LOGIN_FAILED','Acesso nao confirmado');
        const grants=await db.query('SELECT 1 FROM sst.cipa_portal_grant WHERE company_id=$1 AND account_id=$2 AND active LIMIT 1',[row.company_id,row.id]);
        if(!grants.rowCount)throw new ApiError(401,'LOGIN_FAILED','Acesso nao confirmado');
        await db.query('DELETE FROM sst.auth_login_counter WHERE identity_hash=$1',[key]);
        return issue(db,row);
      });
    },
    async principal(req){
      const token=cipaToken(req);if(!token)return null;
      const row=await authTx(pool,async db=>(await db.query(
        "SELECT a.id,a.company_id,a.display_name,a.must_change_password FROM sst.cipa_portal_session s "+
        "JOIN sst.cipa_portal_account a ON a.company_id=s.company_id AND a.id=s.account_id "+
        "JOIN sst.company c ON c.id=a.company_id WHERE s.token_hash=$1 AND s.revoked_at IS NULL "+
        "AND s.expires_at>now() AND s.issued_at>=a.credential_changed_at AND a.active AND c.status='ativa' "+
        "AND EXISTS(SELECT 1 FROM sst.cipa_portal_grant g WHERE g.company_id=a.company_id AND g.account_id=a.id AND g.active)",[digest(token)])).rows[0]);
      return row?{portal:'cipa',accountId:row.id,companyId:row.company_id,name:row.display_name,mustChangePassword:row.must_change_password}:null;
    },
    mutation(req){requireOrigin(req,allowedOrigin);requireCsrf(req,cipaToken(req));},
    async session(req){const p=await this.principal(req);if(!p)throw new ApiError(401,'UNAUTHENTICATED','Sessao expirada');
      return {ok:true,name:p.name,companyId:p.companyId,mustChangePassword:p.mustChangePassword,csrfToken:csrfForToken(cipaToken(req))};},
    async logout(req){this.mutation(req);const token=cipaToken(req);
      if(token)await authTx(pool,db=>db.query('UPDATE sst.cipa_portal_session SET revoked_at=now() WHERE token_hash=$1',[digest(token)]));
      return {cookie:cookie('',true),body:{ok:true}};},
    async password(req,body={}){
      this.mutation(req);const p=await this.principal(req);if(!p)throw new ApiError(401,'UNAUTHENTICATED','Sessao expirada');
      if(body.password===body.currentPassword)throw new ApiError(400,'WEAK_PASSWORD','Escolha uma senha diferente');
      const verifier=await hashPassword(body.password);
      return authTx(pool,async db=>{
        const account=(await db.query('SELECT * FROM sst.cipa_portal_account WHERE company_id=$1 AND id=$2 AND active FOR UPDATE',[p.companyId,p.accountId])).rows[0];
        const session=await db.query('SELECT 1 FROM sst.cipa_portal_session WHERE token_hash=$1 AND revoked_at IS NULL AND expires_at>now() AND issued_at>=$2',[digest(cipaToken(req)),account?.credential_changed_at]);
        if(!account||!session.rowCount||!await verifyPassword(body.currentPassword,account.password_verifier))throw new ApiError(401,'LOGIN_FAILED','Senha atual nao confirmada');
        await db.query('UPDATE sst.cipa_portal_account SET password_verifier=$3,must_change_password=false,credential_changed_at=clock_timestamp() WHERE company_id=$1 AND id=$2',[p.companyId,p.accountId,verifier]);
        await db.query('UPDATE sst.cipa_portal_session SET revoked_at=now() WHERE company_id=$1 AND account_id=$2 AND revoked_at IS NULL',[p.companyId,p.accountId]);
        return issue(db,{...account,must_change_password:false});
      });
    },
  };
}
