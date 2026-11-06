'use strict';
const assert=require('assert');
const policy=require('../feature_sources/cipa_member_server_policy_v1.js');
const future=Date.now()+3600000;
const user={id:'u1',role:'membro_cipa',status:'Ativo',
  companyId:'c1',mandateId:'m1',memberId:'p1'};
const sess={accountId:'u1',revoked:false,expiresAt:future};
const mandate={id:'m1',companyId:'c1',status:'Ativo'};
const member={id:'p1',companyId:'c1',mandateId:'m1',
  workerId:'w1',status:'Ativo',
  name:'Maria Silva',cipaRole:'Vice-presidente'};
const meeting={id:'re1',type:'CIPA_REUNIAO',
  companyId:'c1',mandateId:'m1',memberIds:['p1'],
  status:'Agendada'};
const action={id:'a1',type:'CIPA_ACAO',companyId:'c1',
  mandateId:'m1',assignedMemberId:'p1',status:'Pendente'};
const doc={type:'CIPA_DOCUMENTO',companyId:'c1',mandateId:'m1',
  publishedToMembers:true,containsPersonalData:false,signedRestricted:false};
const can=(verb,record)=>policy.can(user,sess,mandate,member,verb,record);
assert(policy.authorized(user,sess,mandate,member));
assert.strictEqual(policy.memberName(member),
  'Maria Silva — Vice-presidente da CIPA');
assert(can('view_dashboard'));
assert(can('submit_observation'));
assert(can('acknowledge_meeting',meeting));
assert(can('report_own_progress',action));
assert(can('request_own_support',action));
assert(can('view_published_documents',doc));
for(const cap of ['manage_users','sync_full_database','sign_minutes',
 'close_nc','finalize_minutes','edit_election','download_medical_record']) {
  assert(!can(cap),cap);
}
assert(!policy.can(user,{...sess,expiresAt:'2099-01-01'},mandate,
  member,'view_dashboard'),'Invalid date type bypass');
assert(!policy.can(user,{...sess,revoked:'false'},mandate,
  member,'view_dashboard'),'Unknown revoked status is denied');
assert(!policy.can(user,{...sess,revoked:true},mandate,member,
  'view_dashboard'),'Revocation immediate');
assert(!policy.can({...user,companyId:'c2'},sess,mandate,member,
  'view_dashboard'),'Company mismatch denied');
assert(!policy.can(user,sess,{...mandate,id:'m2'},member,
  'view_dashboard'),'Mandate mismatch denied');
assert(!policy.can(user,sess,mandate,{...member,status:'Encerrado'},
  'view_dashboard'),'Inactive member denied');
assert(!policy.can(user,sess,mandate,member,'view_own_actions',
  {...action,assignedMemberId:'p2'}),'Other persons action');
assert(!policy.can(user,sess,mandate,member,'view_meetings',
  {...meeting,memberIds:['p2']}),'Other persons meeting');
assert(!policy.can(user,sess,mandate,member,'view_published_documents',
  {...doc,containsPersonalData:true}),'Personal data excluded');
assert(!policy.can(user,sess,mandate,member,'view_published_documents',
  {...doc,publishedToMembers:false}),'Unpublished docs denied');
assert.strictEqual(policy.filter(user,sess,mandate,member,
  'view_own_actions',[action,{...action,companyId:'c2'}]).length,1);
console.log('CIPA_MEMBER_SERVER_DENY_BY_DEFAULT_OK');
