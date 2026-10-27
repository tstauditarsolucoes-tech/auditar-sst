/**
 * Primeira funcao realmente portada do Flutter/Dart para TypeScript.
 * Referencias: feature_sources/offline_field_rules_service_v329165.dart
 * e feature_sources/nc_title_store_v1.dart.
 * Algoritmos puros; nao acessam backend, conta, banco, dados ou IA.
 */
export type Priority = 'Baixa' | 'Média' | 'Alta' | 'Crítica';

export type NcRow = {
  id?: string | null;
  description?: string | null;
  question_text?: string | null;
};

function clampOneToFive(value: number): number {
  if (!Number.isInteger(value)) throw new TypeError('Probabilidade e severidade devem ser inteiros');
  return Math.max(1, Math.min(5, value));
}

export function matrixScore(probability: number, severity: number, recurring = false): number {
  const p = clampOneToFive(probability);
  const s = clampOneToFive(severity);
  return Math.min(25, p * s + (recurring ? 2 : 0));
}

export function priorityFromMatrix(probability: number, severity: number, recurring = false): Priority {
  const score = matrixScore(probability, severity, recurring);
  if (score <= 4) return 'Baixa';
  if (score <= 9) return 'Média';
  if (score <= 16) return 'Alta';
  return 'Crítica';
}

function normalized(text: string | null | undefined): string {
  return String(text ?? '').replace(/\s+/g, ' ').trim();
}

export function normalizeFriendlyName(value: string): string {
  const name = normalized(value);
  if (name.length > 80) throw new RangeError('Máximo de 80 caracteres');
  return name;
}

export function displayNcTitle(row: NcRow, names: Readonly<Record<string, string>>): string {
  const alias = normalized(names[String(row.id ?? '')]);
  if (alias) return alias;
  const description = normalized(row.description);
  const question = normalized(row.question_text);
  const source = description || question;
  if (!source) return 'Não conformidade sem título';
  const first = source.split(/[.;!?]/)[0].trim();
  const title = first || source;
  return title.length <= 76 ? title : title.slice(0, 73).trimEnd() + '…';
}
