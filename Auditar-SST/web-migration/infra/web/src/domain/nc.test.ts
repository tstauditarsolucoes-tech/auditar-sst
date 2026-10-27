import test from 'node:test';
import assert from 'node:assert/strict';
import { matrixScore, priorityFromMatrix, displayNcTitle, normalizeFriendlyName } from './nc.ts';

test('matriz 1-5 usa o mesmo limite e bonus de recorrencia do Dart', () => {
  assert.equal(matrixScore(3, 3), 9);
  assert.equal(matrixScore(3, 3, true), 11);
  assert.equal(matrixScore(5, 5, true), 25);
  assert.equal(matrixScore(0, 10), 5);
});

test('faixas de prioridade sao equivalentes ao assistente offline', () => {
  assert.equal(priorityFromMatrix(2, 2), 'Baixa');
  assert.equal(priorityFromMatrix(3, 3), 'Média');
  assert.equal(priorityFromMatrix(4, 4), 'Alta');
  assert.equal(priorityFromMatrix(4, 4, true), 'Crítica');
  assert.throws(() => matrixScore(Number.NaN, 3), TypeError);
});

test('nome amigavel nao altera id nem a descricao original', () => {
  const row = { id: 'NC-001', description: 'Extintor vencido. Providenciar substituição.' };
  const title = displayNcTitle(row, { 'NC-001': 'Extintor vencido' });
  assert.equal(title, 'Extintor vencido');
  assert.equal(row.description, 'Extintor vencido. Providenciar substituição.');
  assert.equal(row.id, 'NC-001');
});

test('fallback extrai frase inicial e usa pergunta quando necessario', () => {
  assert.equal(displayNcTitle({ id: '1', description: 'Proteção removida. Ajustar.' }, {}), 'Proteção removida');
  assert.equal(displayNcTitle({ id: '2', question_text: 'A máquina tem proteção?' }, {}), 'A máquina tem proteção');
  assert.equal(displayNcTitle({ id: '3' }, {}), 'Não conformidade sem título');
  assert.equal(displayNcTitle({ description: 'a'.repeat(100) }, {}).length, 74);
});

test('nome amigavel respeita limite original de 80 caracteres', () => {
  assert.equal(normalizeFriendlyName(' Extintor   vencido '), 'Extintor vencido');
  assert.throws(() => normalizeFriendlyName('x'.repeat(81)), RangeError);
});
