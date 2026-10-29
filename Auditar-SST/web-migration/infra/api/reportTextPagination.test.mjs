import test from 'node:test';
import assert from 'node:assert/strict';
import {cleanPdfText,takePdfText} from './reportTextPagination.mjs';
function fakePdf(){
  const state={size:9};
  return {
    font(){return this;},
    fontSize(size){state.size=size;return this;},
    heightOfString(s,opts){return Math.ceil(String(s).length/(opts.width/(state.size*0.5)))*state.size*1.3;},
  };
}
test('fracionamento nao descarta texto longo com espacos',()=>{
  const source=Array.from({length:120},(_,i)=>'orientação-'+i).join(' ');
  const pdf=fakePdf();
  let rest=source,parts=[];
  for(let n=0;n<200&&rest;n++){
    const split=takePdfText(pdf,rest,{width:240,maxHeight:70,fontSize:9});
    assert.ok(split.head.length>0);
    assert.ok(split.rest.length<rest.length);
    parts.push(split.head);rest=split.rest;
  }
  assert.equal(parts.join(''),source);
  assert.ok(parts.length>=2);
});
test('palavra sem espacos nao gera loop ou perda',()=>{
  const source='X'.repeat(4000);
  const pdf=fakePdf();let rest=source,out='';
  for(let n=0;n<400&&rest;n++){
    const x=takePdfText(pdf,rest,{width:260,maxHeight:85});
    assert.ok(x.head.length);out+=x.head;rest=x.rest;
  }
  assert.equal(out,source);
});
test('normalizacao mantém informacao legivel e remove controles',()=>{
  assert.equal(cleanPdfText('  extintor\n vencido\t;  verificar  '),'extintor vencido ; verificar');
  const pdf=fakePdf();
  assert.deepEqual(takePdfText(pdf,'', {width:300,maxHeight:20}),{head:'',rest:''});
});
