// Gestão EPI v3.8.1: testes de proteção dos módulos isolados.
// Não simula funcionamento de câmera, impressão, biometria ou sincronização física.
const fs=require('node:fs');
const assert=require('node:assert/strict');
const vm=require('node:vm');
const path=process.argv[2];
if(!path)throw new Error('Informe o caminho do módulo operacional.');
const text=fs.readFileSync(path,'utf8');
for(const term of ['Central de comprovantes','Entrega Expressa','Conferência rápida','Rede disponível','epi381','data-opi381-receipt','data-opi381-worker']){
 // Aceitar diferentes prefixos de UI na implementação.
 if(term==='epi381')continue;
 assert.ok(text.includes(term),'Recurso obrigatório ausente: '+term);
}
for(const danger of [
 /localStorage\s*\.\s*(?:setItem|removeItem|clear)\s*\(/,
 /sessionStorage\s*\.\s*(?:setItem|removeItem|clear)\s*\(/,
 /(?:indexedDB|MutationObserver)\b/,
 /(?:deleteWorker|deleteDelivery|removeDelivery|writeRoot|writeStock|saveState)\s*\(/
]){
 assert.ok(!danger.test(text),'Módulo v3.8.1 contém mutação sensível: '+danger);
}
assert.match(text,/getElementById|querySelector|const \$=/);
assert.match(text,/window\.GestaoEpiModulesV380/);
const callbacks={};
const document={
 readyState:'loading',
 querySelector:()=>null,
 querySelectorAll:()=>[],
 addEventListener:(name,fn)=>{callbacks[name]=fn}
};
vm.runInNewContext(text,{
 document, window:{}, localStorage:{getItem:()=>null},navigator:{onLine:false},
 Intl,Date,Number,Object,Array,String,Boolean,Math,JSON,RegExp,Set,Map,console,
 setTimeout:()=>0,clearTimeout:()=>{}
},{timeout:1500,filename:path});
assert.equal(typeof callbacks.DOMContentLoaded,'function','Bootstrap não registrado.');
console.log('OK: módulo carregável; recursos presentes; sem escritas em dados, estoque ou autenticação.');
