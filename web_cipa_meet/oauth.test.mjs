import test from 'node:test';import assert from 'node:assert/strict';
import {startAuthorization,exchangeAuthorization,MEET_SCOPE} from './oauth.mjs';
const c={clientId:'demo.apps.googleusercontent.com',clientSecret:'fake',redirectUri:'https://example.test/callback'};
test('authorization is Google-only, read-only scope and PKCE',()=>{
 const a=startAuthorization(c),b=startAuthorization(c),u=new URL(a.url);
 assert.equal(u.origin,'https://accounts.google.com');
 assert.equal(u.searchParams.get('scope'),MEET_SCOPE);
 assert.equal(u.searchParams.get('code_challenge_method'),'S256');
 assert.notEqual(a.state,b.state);assert.notEqual(a.verifier,b.verifier);
 assert.ok(!a.url.includes(c.clientSecret));assert.ok(!a.url.includes(a.verifier));
 assert.throws(()=>startAuthorization({...c,redirectUri:'http://example.test/callback'}));
});
test('exchange validates scopes and uses fixed Google token endpoint',async()=>{
 const a=startAuthorization(c);
 const response=await exchangeAuthorization({config:c,code:'example',verifier:a.verifier,fetcher:async(url,opts)=>{
 assert.equal(url,'https://oauth2.googleapis.com/token');assert.equal(opts.redirect,'error');
 assert.equal(opts.body.get('code_verifier'),a.verifier);
 return {ok:true,json:async()=>({access_token:'fixture',scope:MEET_SCOPE})};
 }});assert.equal(response.access_token,'fixture');
 await assert.rejects(exchangeAuthorization({config:c,code:'example',verifier:a.verifier,
 fetcher:async()=>({ok:true,json:async()=>({access_token:'fixture',scope:'wrong'})})}),/MEET_SCOPE_NOT_GRANTED/);
});
