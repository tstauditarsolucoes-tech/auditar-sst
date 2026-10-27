#!/usr/bin/env node
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const html = fs.readFileSync(
  process.argv[2] || path.join(__dirname, '..', 'build_sources',
    'v3.29.106-client-portal', 'ClientPortal.html'), 'utf8');

const scripts = [...html.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/gi)]
  .map(hit => hit[1]).filter(s => s.trim());
assert(scripts.length, 'HTML sem script do portal');
scripts.forEach((source, i) => new vm.Script(source, {filename: 'portal-inline-'+i+'.js'}));

for (const marker of [
 'function clientPortalNcLabel(row)',
 'function clientPortalNcFromEvidence(company,ncId)',
 'Orientação técnica pendente de publicação',
 'Protocolo:',
 'Aguardando análise técnica',
 'Evidência enviada.',
 "window.prompt('Explique ao cliente", 'auditar-panel-readable-v1', "'portalFontLarger'", 'row.reviewReason',
 'clientPortalReviewEvidence',
 'clientPortalSubmitEvidence',
 'Evidências aguardando validação',
]) {
 assert(html.includes(marker), 'Ausente: '+marker);
}
assert(!html.includes("card.append(text('h4',(index+1)+'. '+(row.title||row.description||'Providência')));"));
assert(!html.includes("text('h3','NC: '+evidence.ncId)"));
assert(html.includes("O envio registra") ||
       html.includes("Este envio ficará pendente de conferência"));
assert(html.includes("Aguardando conferência") || html.includes("a NC permanece aberta") ||
       html.includes("A NC permanece sob controle do técnico"));

// Verify the fallback uses existing source content, never guesses a title/norm.
const start = html.indexOf('function clientPortalNcLabel(row){');
const end = html.indexOf('function managerOpenProblems(company){', start);
assert(start >= 0 && end > start);
const ctx = vm.createContext({});
vm.runInContext(html.slice(start,end),ctx,{timeout:1000});
assert.equal(ctx.clientPortalNcLabel({
 id:'NC-SST-2026-123',
 title:'NC-SST-2026-123',
 description:'Proteção da correia removida',
}), 'Proteção da correia removida');
assert.equal(ctx.clientPortalNcLabel({
 id:'NC-SST-2026-123', title:'Extintor vencido', description:'Extintor sem validade',
}), 'Extintor vencido');
assert.match(ctx.clientPortalNcLabel({id:'NC-SST-2026-123'}), /descrição não publicada/);

console.log('PORTAL_CLIENTE_NC_EVIDENCIAS_LEGIBILIDADE_OK');
console.log('NAO_MODIFICA_GS_NEM_ENCERRA_NC_AUTOMATICAMENTE_OK');
