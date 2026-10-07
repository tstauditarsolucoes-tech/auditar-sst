'use strict';
const assert=require('assert');
const core=require("./pc-epi-flow-core-v360.js");
const now=Date.parse('2026-10-07T17:00:00Z');
const auth={id:'a1',type:'epi_authorization',companyId:'c1',workerId:'w1',createdAt:'2026-10-07T10:00:00Z',authorizedAt:'2026-10-07T10:00:00Z',expiresAt:'2026-10-08T10:00:00Z',items:[{epiId:'e1',qty:2,deliveredQty:0}]};
assert.equal(core.statusOf(auth,now),'pending');
auth.items[0].deliveredQty=1;assert.equal(core.statusOf(auth,now),'partial');
assert.equal(core.deliveryFitsAuthorization(auth,{companyId:'c1',workerId:'w1',items:[{epiId:'e1',qty:1}]},now).ok,true);
assert.equal(core.deliveryFitsAuthorization(auth,{companyId:'c1',workerId:'w1',items:[{epiId:'e1',qty:2}]},now).reason,'QUANTIDADE_ACIMA_LIBERADA');
const movements=[{companyId:'c1',epiId:'e1',delta:10},{companyId:'c1',epiId:'e1',delta:-2}];
const other={id:'a2',type:'epi_authorization',companyId:'c1',workerId:'w2',expiresAt:'2026-10-08T10:00:00Z',items:[{epiId:'e1',qty:3,deliveredQty:0}]};
assert.equal(core.stockBalance(movements,'c1','e1'),8);
assert.equal(core.available(movements,[auth,other],'c1','e1','a1',now),5);
const claims=[
 {id:'claim_b',type:'epi_authorization_claim',authorizationId:'a1',status:'claiming',createdAt:'2026-10-07T17:00:01Z',expiresAt:'2026-10-07T17:01:00Z'},
 {id:'claim_a',type:'epi_authorization_claim',authorizationId:'a1',status:'claiming',createdAt:'2026-10-07T17:00:01Z',expiresAt:'2026-10-07T17:01:00Z'}
];
assert.equal(core.chooseClaimWinner(claims,'a1',now).id,'claim_a');
const expired={...auth,id:'a3',status:'pending',expiresAt:'2026-10-06T10:00:00Z'};assert.equal(core.statusOf(expired,now),'expired');
const delivered={...auth,id:'a4',items:[{epiId:'e1',qty:1,deliveredQty:1}],lastDeliveredAt:'2026-10-07T12:00:00Z'};assert.equal(core.statusOf(delivered,now),'delivered');
const stats=core.reportStats({app:{auditLog:[auth,other,expired,delivered,{id:'d1',type:'epi_direct_delivery',reviewStatus:'pending',createdAt:'2026-10-07T11:00:00Z'}]}},0,now);
assert.equal(stats.direct,1);assert.equal(stats.directPendingReview,1);assert.equal(stats.authorizations,4);
console.log('epi-flow-core-v360: OK');
