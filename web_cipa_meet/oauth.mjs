// Server-only OAuth utilities. No public route or token store is supplied.
// The authenticated organizer's account and authorized meeting scope must be
// established by the host application before calling these functions.
import {randomBytes,createHash} from 'node:crypto';
export const MEET_SCOPE='https://www.googleapis.com/auth/meetings.space.readonly';
function config(c){
  if(!c||typeof c.clientId!=='string'||!c.clientId.endsWith('.apps.googleusercontent.com'))
    throw Error('OAUTH_CONFIG_REQUIRED');
  const uri=new URL(c.redirectUri);
  if(uri.protocol!=='https:'||uri.username||uri.password||uri.search||uri.hash)
    throw Error('INVALID_CALLBACK');
  return c;
}
export function startAuthorization(c){
  config(c);
  const state=randomBytes(32).toString('base64url'),verifier=randomBytes(48).toString('base64url');
  const challenge=createHash('sha256').update(verifier).digest('base64url');
  const u=new URL('https://accounts.google.com/o/oauth2/v2/auth');
  for(const [k,v] of Object.entries({client_id:c.clientId,redirect_uri:c.redirectUri,response_type:'code',
    scope:MEET_SCOPE,access_type:'offline',prompt:'consent',state,code_challenge:challenge,code_challenge_method:'S256'}))
    u.searchParams.set(k,v);
  // Store state and verifier server-side for <=10 minutes, bound to the
  // existing authenticated organizer, company and one-time browser session.
  return {url:u.toString(),state,verifier,expiresAt:Date.now()+600000};
}
export async function exchangeAuthorization({config:c,code,verifier,fetcher=fetch}){
  config(c);
  if(!c.clientSecret||typeof code!=='string'||!code||typeof verifier!=='string'||!/^[-A-Za-z0-9_]{43,128}$/.test(verifier))
    throw Error('INVALID_OAUTH_EXCHANGE');
  // Call only AFTER atomically consuming verified state and rechecking the
  // organizer and tenant. The host must encrypt refresh tokens at rest.
  const r=await fetcher('https://oauth2.googleapis.com/token',{
    method:'POST',redirect:'error',signal:AbortSignal.timeout(15000),
    headers:{'Content-Type':'application/x-www-form-urlencoded'},
    body:new URLSearchParams({client_id:c.clientId,client_secret:c.clientSecret,code,
      code_verifier:verifier,grant_type:'authorization_code',redirect_uri:c.redirectUri})
  });
  if(!r.ok)throw Error('GOOGLE_AUTH_FAILED');
  const data=await r.json();
  if(typeof data.access_token!=='string'||!data.access_token||
    !String(data.scope??'').split(/\s+/).includes(MEET_SCOPE))
    throw Error('MEET_SCOPE_NOT_GRANTED');
  return data; // private server-only result; never send to browser or logs
}
