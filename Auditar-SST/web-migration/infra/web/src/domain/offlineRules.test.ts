import test from 'node:test';
import assert from 'node:assert/strict';
import {
  analyzeOfflineField, suggestNrs, normalizeRuleText,
  suggestedProbabilityForText, suggestedSeverityForText,
  suggestDeadline, buildActionPlan, suggestResponsible,
} from './offlineRules.ts';

test('normalizacao Dart remove apenas acentos mapeados e pontuacao', () => {
  assert.equal(normalizeRuleText('  EXTINTOR: sinalização!  '), 'extintor sinalizacao');
  assert.equal(normalizeRuleText('Pó, ruído e elétrica'), 'po ruido e eletrica');
});

test('NRs sao ordenadas e sugeridas por familia tecnica, como no Dart', () => {
  assert.deepEqual(suggestNrs('Extintor vencido e sem sinalização'), ['NR-23', 'NR-26']);
  assert.deepEqual(suggestNrs('Andaime sem guarda-corpo'), ['NR-18', 'NR-35']);
  assert.deepEqual(suggestNrs('Sensor da máquina sem intertravamento'), ['NR-12']);
  assert.deepEqual(suggestNrs('sem palavras tecnicas especificas'), []);
});

test('perfil de incendio e bonus de recorrencia equivalentes ao Dart', () => {
  const result = analyzeOfflineField({text:'Extintor vencido', probability:4, severity:4, recurring:true});
  assert.equal(result.category, 'Proteção contra incêndio');
  assert.deepEqual(result.nrs, ['NR-23']);
  assert.equal(result.score, 18);
  assert.equal(result.priority, 'Crítica');
  assert.equal(result.suggestedProbability, 3);
  assert.equal(result.suggestedSeverity, 4);
  assert.match(result.actionPlan, /Tratamento imediato recomendado/);
  assert.match(result.nrDetails[0], /Proteção contra incêndios/);
  assert.equal(result.possibleRecurrence, true);
});

test('sensor e intertravamento retornam perfil especifico, prazo e responsavel', () => {
  const result = analyzeOfflineField({text:'Sensor sem intertravamento na prensa', probability:3, severity:3, learnedHistoryMatch:true});
  assert.equal(result.category, 'Segurança de máquinas — sensor/intertravamento');
  assert.equal(result.priority, 'Média');
  assert.equal(result.deadlineSuggestion, 'Programar correção — sugerido até 30 dias');
  assert.match(result.responsibleSuggestion, /Manutenção/);
  assert.equal(result.possibleRecurrence, true);
});

test('empate entre perfis mantém primeiro da lista de regras do Dart', () => {
  // 'protetor auricular' casa primeiro com EPI, mesmo quando o perfil de ruido tambem reconhece o termo.
  const result = analyzeOfflineField({text:'Uso incorreto de protetor auricular', probability:2, severity:2});
  assert.equal(result.category, 'Equipamento de proteção individual');
  // A funcao Dart suggestNrs nao inclui 'protetor auricular' na lista de termos da NR-15.
  assert.deepEqual(result.nrs, ['NR-06']);
});

test('perfil generico evita inventar NR ou risco especifico', () => {
  const result = analyzeOfflineField({text:'descrição sem correspondência conhecida', probability:1, severity:1});
  assert.deepEqual(result.nrs, []);
  assert.equal(result.category, 'Risco ocupacional');
  assert.match(result.technicalReason, /confirmado pelo TST/);
  assert.equal(result.score, 1);
});

test('funcoes auxiliares de prioridade, responsavel e prazo preservadas', () => {
  assert.equal(suggestDeadline('Alta'), 'Prioritário — sugerido até 7 dias, conforme risco e viabilidade');
  assert.equal(suggestDeadline('Crítica'), 'Imediato / antes da continuidade da condição de risco');
  assert.equal(suggestedProbabilityForText('painel elétrico exposto'), 3);
  assert.equal(suggestedSeverityForText('painel elétrico exposto'), 5);
  assert.match(suggestResponsible('painel elétrico exposto'), /Manutenção elétrica/);
  assert.match(buildActionPlan('painel elétrico exposto', 'Alta'), /Priorizar a correção/);
});
