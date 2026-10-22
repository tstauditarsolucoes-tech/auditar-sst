// Regressões de navegação Fichas e indicador de rede Android.
const assert=require('node:assert/strict'),fs=require('node:fs');
const fiche=fs.readFileSync('auditar-epi/worker-sheets-v382.js','utf8');
const ops=fs.readFileSync('auditar-epi/operation-quality-v381.js','utf8');
new Function(fiche);new Function(ops);
assert.ok(fiche.includes("const b=$$('[data-go]',nav).find("),'Bootstrap Fichas precisa de querySelectorAll antes de .find()');
assert.ok(!fiche.includes("const b=$('[data-go]',nav).find("),'querySelector().find() quebra inicialização');
assert.match(fiche,/closest\?\.\('#bottomNav button'\)/,'Clique inferior Fichas precisa ser capturado');
assert.match(fiche,/\\bfichas\\b/,'Captura não localizada');
assert.match(fiche,/e\.stopImmediatePropagation\(\);open\(\);return/,'Roteador antigo precisa ser impedido para Fichas');
assert.match(fiche,/},true\);/,'Handler precisa rodar na fase de captura');
assert.match(ops,/if\(!PC\)\{\$\('#opi381Sync'\)\?\.remove\(\);return\}/,'Android não deve repetir texto de sincronização');
console.log('PASSOU: navegação Fichas e painel de sincronização Android.');
