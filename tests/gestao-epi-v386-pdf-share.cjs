const assert=require('node:assert/strict');
const fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const root=path.join(__dirname,'..'),mobile=path.join(root,'auditar-epi');
const receipt=fs.readFileSync(path.join(mobile,'receipt-print-fix-v380.js'),'utf8');
const sheet=fs.readFileSync(path.join(mobile,'worker-sheets-v382.js'),'utf8');
const java=fs.readFileSync(path.join(root,'auditar-epi-mobile/native/NativePrintPlugin.java'),'utf8');
new Function(receipt);new Function(sheet);
for(const method of ['void sharePdf','void savePdf','@ActivityCallback','ACTION_CREATE_DOCUMENT','grantUriPermission','FLAG_GRANT_READ_URI_PERMISSION','itemRow(','drawWrapped(','new PdfDocument.PageInfo.Builder']){
  assert.ok(java.includes(method),'Função nativa ausente: '+method);
}
assert.ok(receipt.includes("mode==='save'?'savePdf'"),'Salvar PDF ausente no comprovante');
assert.ok(receipt.includes("btnSaveReceiptPdf"),'Botão Salvar PDF ausente');
assert.ok(sheet.includes('data-ficha382-pdf="save"'),'Salvar ficha ausente');
assert.ok(sheet.includes('data-ficha382-pdf="share"'),'Compartilhar ficha ausente');
assert.ok(!/localStorage\s*\.\s*(?:setItem|clear|removeItem)\s*\(/.test(sheet),'A ficha não deve alterar dados');
assert.ok(!/\.movements\s*\.\s*(?:push|splice)\s*\(/.test(sheet),'Geração do PDF não pode movimentar estoque');
// Exercita a função real de associação ao trabalhador, extraída sem refatorar núcleo.
const functionLine=sheet.split('\n').find(l=>l.startsWith('function current(){'));
assert.ok(functionLine,'Função current() ausente');
const workers=[{id:'wA',companyId:'c1',name:'Alexandre'}, {id:'wB',companyId:'c1',name:'Alexandre'}];
const deliveries=[
 {id:'d1',workerId:'wA',createdAt:'2026-09-06',items:[{epiId:'e1',qty:1}]},
 {id:'d2',workerId:'wB',createdAt:'2026-09-07',items:[{epiId:'e2',qty:2}]}
];
function testWorker(wid){
 const context={workerId:wid,app:()=>({workers,companies:[{id:'c1'}],epis:[],deliveries})};
 return vm.runInNewContext(functionLine+'; current();',context,{timeout:1000});
}
assert.equal(testWorker('wA').d[0].id,'d1','Histórico do funcionário A misturado');
assert.equal(testWorker('wB').d[0].id,'d2','Histórico do funcionário B misturado');
assert.equal(testWorker('inexistente'),null,'ID não encontrado não pode assumir outra pessoa');
console.log('PASSOU v3.8.6: compartilhamento com fallback, layout e histórico por ID sem misturar homônimos.');
