import test from 'node:test';
import assert from 'node:assert/strict';
import {buildCipaIcs,upcomingCipaMeetings} from './cipaCalendar.ts';
const now=new Date('2027-02-01T10:00:00Z');
const a={id:'11111111-1111-4111-8111-111111111111',title:'Reunião de segurança',scheduled_at:'2027-02-03T13:00:00Z',status:'planejada'};
const b={id:'22222222-2222-4222-8222-222222222222',title:'Encerrada',scheduled_at:'2027-02-05T13:00:00Z',status:'realizada'};
test('only upcoming planned meetings appear',()=>assert.deepEqual(upcomingCipaMeetings([b,a],now),[a]));
test('private ICS includes optional calendar reminder without secrets',()=>{
  const ics=buildCipaIcs([a,b],now);
  assert.match(ics,/BEGIN:VCALENDAR\r\n/);
  assert.match(ics,/DTSTART:20270203T130000Z/);
  assert.match(ics,/TRIGGER:-P1D/);
  assert.doesNotMatch(ics,/Encerrada|senha|token=/);
});
test('newline and comma injection cannot add calendar properties',()=>{
  const ics=buildCipaIcs([{...a,title:'Pauta\r\nATTENDEE:public@invalid; de teste'}],now);
  assert.doesNotMatch(ics,/\r\nATTENDEE:/);
  assert.match(ics,/SUMMARY:Pauta ATTENDEE:public@invalid\\; de teste/);
});
