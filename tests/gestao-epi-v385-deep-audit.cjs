// Gestão EPI Android v3.8.5 — regressões e proteção do núcleo do app.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),assert=require('node:assert/strict'),vm=require('node:vm');
const root=path.resolve(__dirname,'..','auditar-epi');
const read=p=>fs.readFileSync(path.join(root,p),'utf8');
const index=read('index.html'),fichas=read('worker-sheets-v382.js'),link=read('worker-link.js'),restore=read('restore-worker-actions-v385.js');
const imports=[...index.matchAll(/<script[^>]*src=["']([^"']+)/g)].map(x=>x[1]).filter(x=>!/^https?:/.test(x));
for(const file of imports)assert.ok(fs.existsSync(path.join(root,file)) || file==='qrcode-generator.js',
 'Script da tela não disponível: '+file);
for(const required of ['worker-link.js','worker-sheets-v382.js','restore-worker-actions-v385.js','biometric-face.js','worker-portal-share-v1.js','advanced-operations-v380.js','adaptive-modules-v380.js','receipt-print-fix-v380.js','mobile-smart-tables-v384.js']){
 assert.ok(imports.includes(required),'Função não carregada no Android: '+required);
}
assert.ok(imports.indexOf('auth.js')<imports.indexOf('worker-link.js'),'Vínculo deve ser carregado depois da autenticação');
assert.ok(imports.indexOf('worker-sheets-v382.js')<imports.indexOf('restore-worker-actions-v385.js'),'Restaurador deve ser carregado depois das fichas');
for(const s of ['worker-link.js','worker-sheets-v382.js','restore-worker-actions-v385.js','operation-quality-v381.js','worker-portal-share-v1.js'])new Function(read(s));
assert.ok(!fichas.includes("$('.view').forEach("),'Fichas contém querySelector().forEach() que derruba a navegação');
assert.ok(!fichas.includes("$('button',nav).forEach("),'Fichas contém querySelector().forEach() na barra inferior');
assert.ok(fichas.includes("$$('.view').forEach("),'Abrir ficha deve navegar entre telas');
assert.ok(fichas.includes("$$('button',nav).forEach("),'Aba Fichas precisa de lista de botões');
assert.ok(fichas.includes("data-ficha382-pdf") && fichas.includes('f382-show-detail'),'Ficha deve apresentar PDF e detalhe');
assert.ok(link.includes('Alterar vínculo') && link.includes('existingIds') && link.includes('cardId'),'Vínculo deve ter edição e identificação segura');
assert.ok(restore.includes('[data-bio-worker]')&&restore.includes('[data-worker-portal-share]')&&restore.includes('[data-ux-worker]')&&restore.includes('[data-ficha382-worker]'),'Botões principais não podem desaparecer dos cartões');
assert.ok(read('sw.js').includes("gestao-epi-v385-shell"),'Cache offline antigo pode ocultar versões de JS');
assert.ok(!/localStorage\s*\.\s*(?:setItem|removeItem|clear)\s*\(/.test(restore),'Restaurador não deve alterar dados');
assert.ok(!/\.movements\s*\.\s*(?:push|unshift|splice)\s*\(/.test(restore),'Restaurador não pode mexer no estoque');
assert.ok(!fs.existsSync(path.join(root,'CommercialExtensions.gs')),'Não reintroduzir CommercialExtensions.gs');
// Guardas de integridade: comparação do conteúdo ao blob Git verificado da base anterior.
const hashes={
 'app.js':'4c584df7b7698ff33cd39fd4a78215550fe70af8',
 'auth.js':'7717b5409d9fcaa8410daa83a3fd056ee91e7d09',
 'cloud-sync.js':'93ddc2d9e85ff0c7eb2a5ce4f9eed8ea314e453e',
 'biometric-face.js':'9868ee5bbed868a46eec1da47df48a9c3422616a',
 'biometric-crypto-v1.js':'937ce4aee9b77694532cc48427731d1b52720b88',
 'company-branding.js':'96993f66e7bb02e7c4bf4d0d1edfed82390a5df3',
 'ca-center-v330.js':'b1da8b1a572e339fd224d74370beed69e26e7b2e'
};
for(const [file,expected] of Object.entries(hashes)){
 const bytes=fs.readFileSync(path.join(root,file));
 const current=crypto.createHash('sha1').update('blob '+bytes.length+'\0').update(bytes).digest('hex');
 assert.equal(current,expected,'Mudança imprevista em função crítica: '+file);
}
// Teste simulado sem dados de trabalhador/tenant, sem acesso ao armazenamento.
let clickHandler=null;
const domHandler={};
const createButton=(name)=>({textContent:name,setAttribute(){},closest(){return {};}});
const fiche=createButton('Ficha'),summary=createButton('Abrir'),face=createButton('Cadastrar rosto'),portal=createButton('Portal');
const del=createButton('Excluir');
const actions={querySelector(){return null;}};
const card={querySelector(q){return {'[data-del-worker]':del,'.list-actions':actions,'[data-bio-worker]':face,'[data-worker-portal-share]':portal,'[data-ficha382-worker]':fiche,'[data-ux-worker]':summary}[q]||null}};
const list={querySelectorAll(q){return q==='.list-item'?[card]:[]}};
const document={
 readyState:'loading',
 head:{appendChild(){}},
 querySelector(q){if(q==='#workerList')return list;return null},
 createElement(){return {id:'',textContent:'',appendChild(){}};},
 addEventListener(name,callback){domHandler[name]=callback;}
};
const sandbox={document,MutationObserver:class{observe(){}},requestAnimationFrame(){},setTimeout(){},window:{},console};
vm.runInNewContext(restore,sandbox,{timeout:1500});
assert.equal(typeof domHandler.DOMContentLoaded,'function');
domHandler.DOMContentLoaded();
assert.equal(summary.textContent,'Resumo 360°');
assert.equal(fiche.textContent,'📑 Ficha completa');
console.log('PASSOU v3.8.5: atalhos, fichas, vínculo, cache, simulação de cartões e 7 módulos críticos intactos.');
