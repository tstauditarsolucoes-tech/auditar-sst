/**
 * Conversao integral das regras puras do OfflineFieldRulesService (Dart).
 * Origem: Auditar-SST/feature_sources/offline_field_rules_service_v329165.dart
 * Sem chamadas remotas, login, IA, banco, fotos ou dados reais.
 * NRs sao SUGESTOES e exigem validacao tecnica pelo TST.
 */
import { matrixScore, priorityFromMatrix } from './nc';
import type { Priority } from './nc';

type RuleProfile = {
  category: string;
  terms: readonly string[];
  risk: string;
  consequence: string;
  action: string;
  responsible: string;
  evidence: string;
  reason: string;
  probability: number;
  severity: number;
};

export type OfflineRuleResult = {
  nrs: string[];
  priority: Priority;
  score: number;
  actionPlan: string;
  responsibleSuggestion: string;
  deadlineSuggestion: string;
  possibleRecurrence: boolean;
  category: string;
  riskSummary: string;
  consequenceSummary: string;
  evidenceSuggestion: string;
  technicalReason: string;
  nrDetails: string[];
  suggestedProbability: number;
  suggestedSeverity: number;
};

const GENERIC: RuleProfile = {
  "category": "Risco ocupacional",
  "terms": [],
  "risk": "Condição com potencial de exposição a perigo ou falha de controle.",
  "consequence": "Incidente, lesão ou agravamento da condição caso o perigo permaneça sem tratamento.",
  "action": "Corrigir a condição registrada, definir responsável, comprovar a regularização com evidência e verificar a eficácia no acompanhamento.",
  "responsible": "Responsável da área a definir",
  "evidence": "Registrar foto após a correção e observação objetiva da medida adotada.",
  "reason": "A regra local não encontrou um tema específico suficiente; o enquadramento deve ser confirmado pelo TST.",
  "probability": 3,
  "severity": 3
};
const PROFILES: readonly RuleProfile[] = [
  {
    "category": "Segurança de máquinas — parada de emergência",
    "terms": [
      "parada de emergencia",
      "botao de emergencia",
      "botoeira de emergencia",
      "botao",
      "botoeira"
    ],
    "risk": "Impossibilidade ou atraso na parada imediata da máquina diante de uma condição perigosa.",
    "consequence": "Agravamento de acidente por continuidade de movimento, aprisionamento, esmagamento, corte ou outro contato perigoso.",
    "action": "Interromper a operação quando a função de parada de emergência estiver inoperante, solicitar correção pela manutenção e testar o dispositivo antes da liberação.",
    "responsible": "Manutenção / responsável técnico da máquina",
    "evidence": "Foto do dispositivo e registro do teste funcional após o reparo.",
    "reason": "Termos associados a comando/parada de emergência e segurança de máquinas foram identificados.",
    "probability": 3,
    "severity": 5
  },
  {
    "category": "Segurança de máquinas — sensor/intertravamento",
    "terms": [
      "sensor",
      "intertravamento",
      "chave de seguranca",
      "micro switch"
    ],
    "risk": "Acesso à zona de perigo sem atuação adequada do sistema de proteção.",
    "consequence": "Aprisionamento, esmagamento, corte ou contato com partes perigosas em movimento.",
    "action": "Suspender o uso quando o dispositivo integrar função de segurança, corrigir o sensor/intertravamento e realizar teste funcional antes da liberação.",
    "responsible": "Manutenção / responsável técnico da máquina",
    "evidence": "Foto do dispositivo e registro do teste funcional após a correção.",
    "reason": "Foram identificados termos associados a sensores e intertravamentos de segurança.",
    "probability": 3,
    "severity": 5
  },
  {
    "category": "Segurança de máquinas — proteção física",
    "terms": [
      "protecao de maquina",
      "grade de protecao",
      "carter",
      "parte movel",
      "zona de perigo",
      "polia",
      "correia",
      "engrenagem"
    ],
    "risk": "Contato com partes móveis, pontos de esmagamento, corte, arraste ou aprisionamento.",
    "consequence": "Lesões graves, amputações ou outros traumas por contato com componentes em movimento.",
    "action": "Interromper a condição insegura, reinstalar ou adequar a proteção e somente liberar a máquina após verificação funcional e de acesso à zona de perigo.",
    "responsible": "Manutenção / responsável técnico da máquina",
    "evidence": "Foto da proteção instalada e verificação visual/funcional antes da liberação.",
    "reason": "Foram identificados termos ligados a proteção de partes perigosas de máquinas.",
    "probability": 3,
    "severity": 5
  },
  {
    "category": "Eletricidade",
    "terms": [
      "painel eletrico",
      "quadro eletrico",
      "fiacao",
      "cabo eletrico",
      "cabo energ",
      "aterramento",
      "tomada",
      "plugue",
      "choque"
    ],
    "risk": "Contato com partes energizadas, falha de isolação, curto-circuito ou energização indevida de partes metálicas.",
    "consequence": "Choque elétrico, queimaduras, incêndio ou acidente grave/fatal.",
    "action": "Isolar a condição quando houver exposição elétrica e encaminhar a regularização a profissional autorizado antes da liberação.",
    "responsible": "Manutenção elétrica / profissional autorizado",
    "evidence": "Foto da correção e confirmação da condição segura pelo responsável autorizado.",
    "reason": "A descrição contém termos associados a instalações ou componentes elétricos.",
    "probability": 3,
    "severity": 5
  },
  {
    "category": "Proteção contra incêndio",
    "terms": [
      "extintor",
      "hidrante",
      "rota de fuga",
      "saida de emergencia",
      "incendio"
    ],
    "risk": "Comprometimento do acesso, identificação ou disponibilidade do recurso de emergência.",
    "consequence": "Atraso ou redução da eficiência da resposta inicial em situação de incêndio ou evacuação.",
    "action": "Regularizar imediatamente acesso, sinalização e condição do equipamento ou rota, mantendo o ponto disponível e claramente identificado.",
    "responsible": "Gestão da unidade / responsável da área",
    "evidence": "Foto do ponto regularizado e, quando aplicável, registro de manutenção/inspeção.",
    "reason": "Foram identificados termos relacionados a proteção contra incêndio e resposta a emergência.",
    "probability": 3,
    "severity": 4
  },
  {
    "category": "Inflamáveis e combustíveis",
    "terms": [
      "gasolina",
      "diesel",
      "combustivel",
      "inflamavel",
      "glp",
      "solvente"
    ],
    "risk": "Vazamento, formação de atmosfera inflamável, contato com fonte de ignição ou armazenamento incompatível.",
    "consequence": "Incêndio, explosão, queimaduras e danos materiais.",
    "action": "Regularizar recipiente, identificação, armazenamento e controle de fontes de ignição, restringindo a condição insegura até a correção.",
    "responsible": "Gestão da área / responsável pelo armazenamento",
    "evidence": "Foto do recipiente/local regularizado e identificação visível do produto.",
    "reason": "Foram identificados termos associados a inflamáveis ou combustíveis.",
    "probability": 3,
    "severity": 5
  },
  {
    "category": "Trabalho em altura / proteção contra quedas",
    "terms": [
      "trabalho em altura",
      "linha de vida",
      "ancoragem",
      "cinto paraquedista",
      "guarda corpo",
      "telhado",
      "queda de nivel"
    ],
    "risk": "Queda de trabalhador para nível inferior por ausência ou falha de proteção coletiva/individual.",
    "consequence": "Traumas graves ou acidente fatal.",
    "action": "Restringir a atividade até a regularização das medidas de proteção contra quedas e liberar somente após verificação das condições seguras.",
    "responsible": "Supervisão da atividade / SST / responsável técnico",
    "evidence": "Foto das proteções regularizadas e registro da liberação da condição de trabalho.",
    "reason": "A descrição indica atividade ou condição com potencial de queda de nível.",
    "probability": 3,
    "severity": 5
  },
  {
    "category": "Andaimes e plataformas",
    "terms": [
      "andaime",
      "plataforma de trabalho"
    ],
    "risk": "Queda de trabalhador, queda de materiais ou instabilidade/tombamento da estrutura.",
    "consequence": "Traumas graves, esmagamento ou acidente fatal.",
    "action": "Interromper o uso do andaime inseguro, regularizar estabilidade, acessos, proteções e montagem antes de nova liberação.",
    "responsible": "Responsável da obra / montagem / SST",
    "evidence": "Fotos da base, amarração/ancoragem, acesso e proteções após regularização.",
    "reason": "Foram identificados termos relacionados a andaimes ou plataformas de trabalho.",
    "probability": 3,
    "severity": 5
  },
  {
    "category": "Escadas e acessos",
    "terms": [
      "escada portatil",
      "escada fixa",
      "escada",
      "corrimao"
    ],
    "risk": "Perda de equilíbrio, escorregamento, tombamento ou queda durante acesso e circulação.",
    "consequence": "Contusões, fraturas ou lesões graves.",
    "action": "Retirar de uso acessos inadequados ou restringir a passagem, corrigindo apoio, conservação e proteção antes da liberação.",
    "responsible": "Responsável da área / manutenção",
    "evidence": "Foto do acesso regularizado, incluindo apoio, corrimão ou proteção aplicável.",
    "reason": "A descrição contém termos relacionados a escadas e acessos.",
    "probability": 3,
    "severity": 4
  },
  {
    "category": "Equipamento de proteção individual",
    "terms": [
      "epi",
      "capacete",
      "luva",
      "oculos",
      "protetor auricular",
      "respirador",
      "mascara",
      "botina",
      "perneira",
      "avental"
    ],
    "risk": "Exposição ao perigo existente sem a proteção individual prevista para a atividade ou área.",
    "consequence": "Aumento da possibilidade e da gravidade de lesões ou agravos relacionados à exposição.",
    "action": "Regularizar o EPI adequado, orientar o trabalhador e reforçar a supervisão do uso durante a atividade e circulação em área de risco.",
    "responsible": "Supervisão da área / SST",
    "evidence": "Registro de orientação/entrega quando aplicável e foto da condição regularizada.",
    "reason": "Foram identificados termos de EPI ou proteção individual.",
    "probability": 3,
    "severity": 4
  },
  {
    "category": "Ruído ocupacional",
    "terms": [
      "ruido",
      "barulho",
      "protetor auricular"
    ],
    "risk": "Exposição a níveis de ruído potencialmente relevantes sem controle suficiente.",
    "consequence": "Danos auditivos, fadiga, dificuldade de comunicação e aumento do risco de acidentes.",
    "action": "Reavaliar controles da fonte/ambiente, reforçar uso de proteção auditiva quando prevista e manter acompanhamento da exposição.",
    "responsible": "Gestão da área / SST",
    "evidence": "Registro da medida adotada, EPI regularizado e avaliação de ruído quando necessária.",
    "reason": "A descrição contém termos associados a exposição ocupacional ao ruído.",
    "probability": 3,
    "severity": 4
  },
  {
    "category": "Calor ocupacional",
    "terms": [
      "calor",
      "estresse termico",
      "temperatura elevada",
      "fonte de calor"
    ],
    "risk": "Sobrecarga térmica durante a execução da atividade.",
    "consequence": "Desidratação, exaustão térmica, redução de atenção e outros agravos relacionados ao calor.",
    "action": "Avaliar a exposição e revisar controles, pausas, hidratação e organização do trabalho conforme o resultado da avaliação ocupacional.",
    "responsible": "Gestão da área / SST",
    "evidence": "Registro dos controles adotados e resultado da avaliação ocupacional quando aplicável.",
    "reason": "Foram identificados termos associados a carga térmica ou fonte de calor.",
    "probability": 3,
    "severity": 4
  },
  {
    "category": "Poeiras, fumos e particulados",
    "terms": [
      "poeira",
      "particulado",
      "fumaca",
      "fumo metalico"
    ],
    "risk": "Inalação de partículas ou contato com olhos e vias respiratórias.",
    "consequence": "Irritação, desconforto respiratório e possíveis agravos relacionados à exposição.",
    "action": "Revisar controles de fonte, ventilação e limpeza e garantir proteção respiratória/ocular quando prevista na avaliação de risco.",
    "responsible": "Gestão da área / SST",
    "evidence": "Foto dos controles implantados e registro da avaliação/medidas de proteção adotadas.",
    "reason": "Foram identificados termos associados a contaminantes particulados no ar.",
    "probability": 3,
    "severity": 4
  },
  {
    "category": "Produtos químicos",
    "terms": [
      "produto quimico",
      "quimico",
      "recipiente sem identificacao",
      "rotulo",
      "ficha de seguranca",
      "fispq"
    ],
    "risk": "Exposição, uso incorreto ou mistura incompatível por falha de identificação ou controle do produto.",
    "consequence": "Intoxicação, irritação, queimadura química, reação perigosa ou contaminação.",
    "action": "Regularizar identificação, armazenamento, informações de segurança e controles de manuseio antes de manter o produto em uso.",
    "responsible": "Responsável da área / SST / almoxarifado",
    "evidence": "Foto do recipiente identificado e do armazenamento após regularização.",
    "reason": "Foram identificados termos relacionados a produtos químicos e comunicação de perigos.",
    "probability": 3,
    "severity": 4
  },
  {
    "category": "Ergonomia e movimentação manual",
    "terms": [
      "ergonomia",
      "postura",
      "levantamento manual",
      "movimentacao manual",
      "sobrecarga",
      "repetitiv",
      "peso"
    ],
    "risk": "Sobrecarga biomecânica por postura, esforço, repetitividade, alcance ou movimentação manual.",
    "consequence": "Dor, fadiga, distensão e possíveis agravos musculoesqueléticos.",
    "action": "Reorganizar o método, reduzir esforço e alcance, orientar a técnica e avaliar auxílio mecânico, trabalho em dupla ou mudança do processo.",
    "responsible": "Gestão da área / SST",
    "evidence": "Foto do método ajustado e registro da orientação ou medida ergonômica adotada.",
    "reason": "Foram identificados termos associados a ergonomia ou movimentação manual.",
    "probability": 3,
    "severity": 3
  },
  {
    "category": "Movimentação e armazenamento de materiais",
    "terms": [
      "empilhadeira",
      "empilhamento",
      "armazenamento",
      "pallet",
      "carga",
      "movimentacao de materiais"
    ],
    "risk": "Queda, tombamento, colisão ou atingimento durante movimentação ou armazenamento de materiais.",
    "consequence": "Contusões, esmagamentos, fraturas ou lesões graves.",
    "action": "Reorganizar o armazenamento/movimentação, estabilizar materiais, manter circulação segura e revisar o método e a operação dos equipamentos envolvidos.",
    "responsible": "Logística / almoxarifado / supervisão da área",
    "evidence": "Foto do empilhamento/local regularizado e registro do método adotado.",
    "reason": "A descrição contém termos relacionados a movimentação, empilhamento ou armazenamento.",
    "probability": 3,
    "severity": 4
  },
  {
    "category": "Organização, circulação e quedas no mesmo nível",
    "terms": [
      "organizacao",
      "obstrucao",
      "corredor",
      "passagem",
      "piso molhado",
      "buraco",
      "canaleta",
      "tropeco"
    ],
    "risk": "Tropeço, escorregamento, queda no mesmo nível, colisão ou dificuldade de circulação.",
    "consequence": "Contusões, entorses, fraturas ou interferência em rotas e acessos.",
    "action": "Eliminar a condição, organizar a área, proteger aberturas e manter rotas de circulação e acessos livres.",
    "responsible": "Responsável da área / manutenção",
    "evidence": "Foto da área após limpeza, organização, proteção ou reparo.",
    "reason": "Foram identificados termos relacionados a organização, piso ou circulação.",
    "probability": 3,
    "severity": 3
  },
  {
    "category": "Condições sanitárias e de conforto",
    "terms": [
      "refeitorio",
      "banheiro",
      "sanitario",
      "vestiario",
      "agua potavel"
    ],
    "risk": "Exposição a condições inadequadas de higiene, conservação ou conforto.",
    "consequence": "Desconforto, contaminação e comprometimento das condições sanitárias do ambiente.",
    "action": "Regularizar higiene, conservação, organização e estrutura do ambiente, mantendo rotina de verificação.",
    "responsible": "Gestão da unidade / serviços gerais",
    "evidence": "Foto do ambiente regularizado e registro da medida adotada.",
    "reason": "Foram identificados termos ligados a instalações sanitárias, refeições ou conforto.",
    "probability": 2,
    "severity": 3
  },
  {
    "category": "Sinalização e identificação",
    "terms": [
      "sinalizacao",
      "placa",
      "demarcacao",
      "identificacao"
    ],
    "risk": "Falha de comunicação do perigo, orientação inadequada ou dificuldade de identificação.",
    "consequence": "Acesso indevido, comportamento inadequado ou atraso na resposta ao risco.",
    "action": "Instalar ou corrigir sinalização e identificação no ponto adequado, garantindo visibilidade e coerência com o perigo existente.",
    "responsible": "Responsável da área / SST",
    "evidence": "Foto da sinalização instalada ou corrigida.",
    "reason": "Foram identificados termos de sinalização, demarcação ou identificação.",
    "probability": 2,
    "severity": 3
  },
  {
    "category": "Espaço confinado",
    "terms": [
      "espaco confinado",
      "entrada em tanque",
      "entrada em silo"
    ],
    "risk": "Entrada não autorizada e exposição a atmosfera perigosa, deficiência/enriquecimento de oxigênio ou outros perigos do espaço.",
    "consequence": "Intoxicação, asfixia, queda, aprisionamento ou acidente fatal.",
    "action": "Restringir o acesso e verificar caracterização, autorização, avaliação atmosférica, supervisão e controles aplicáveis antes de qualquer entrada.",
    "responsible": "Responsável técnico / supervisor de entrada / SST",
    "evidence": "Registro da identificação do espaço, controle de acesso e documentação aplicável antes da entrada.",
    "reason": "A descrição indica possível situação de espaço confinado.",
    "probability": 3,
    "severity": 5
  },
  {
    "category": "Equipamentos pressurizados",
    "terms": [
      "caldeira",
      "vaso de pressao",
      "compressor",
      "tubulacao pressurizada",
      "tanque metalico"
    ],
    "risk": "Falha de integridade, operação inadequada ou perda de controle de equipamento pressurizado.",
    "consequence": "Ruptura, projeção de partes, queimaduras ou acidente grave.",
    "action": "Encaminhar para verificação do responsável técnico, conferindo identificação, integridade, inspeções e controles aplicáveis antes da continuidade insegura.",
    "responsible": "Responsável técnico / manutenção",
    "evidence": "Registro da inspeção/regularização e foto da identificação ou condição corrigida.",
    "reason": "Foram identificados termos relacionados a equipamentos ou sistemas pressurizados.",
    "probability": 2,
    "severity": 5
  }
];
const NR_TERMS: readonly {nr: string; terms: readonly string[]}[] = [
  {
    "nr": "NR-01",
    "terms": [
      "risco",
      "perigo",
      "nao conform",
      "condicao insegura",
      "ato inseguro",
      "recorrente",
      "plano de acao"
    ]
  },
  {
    "nr": "NR-06",
    "terms": [
      "epi",
      "capacete",
      "luva",
      "oculos",
      "protetor auricular",
      "respirador",
      "mascara",
      "botina",
      "perneira",
      "avental",
      "cinto paraquedista"
    ]
  },
  {
    "nr": "NR-10",
    "terms": [
      "painel eletrico",
      "eletric",
      "fiacao",
      "cabo energ",
      "cabo eletrico",
      "aterramento",
      "choque",
      "tomada",
      "plugue",
      "quadro eletrico"
    ]
  },
  {
    "nr": "NR-11",
    "terms": [
      "empilhadeira",
      "movimentacao de carga",
      "transporte de materiais",
      "armazenamento",
      "empilhamento",
      "pallet",
      "carga suspensa"
    ]
  },
  {
    "nr": "NR-12",
    "terms": [
      "maquina",
      "sensor",
      "intertravamento",
      "botoeira",
      "botao",
      "parada de emergencia",
      "protecao de maquina",
      "parte movel",
      "zona de perigo",
      "prensa",
      "esteira",
      "betoneira",
      "polia",
      "correia",
      "engrenagem"
    ]
  },
  {
    "nr": "NR-13",
    "terms": [
      "caldeira",
      "vaso de pressao",
      "compressor",
      "tubulacao pressurizada",
      "tanque metalico"
    ]
  },
  {
    "nr": "NR-15",
    "terms": [
      "ruido",
      "calor",
      "agente quimico",
      "poeira",
      "poeira mineral",
      "fumaca",
      "fumo metalico"
    ]
  },
  {
    "nr": "NR-17",
    "terms": [
      "ergonom",
      "postura",
      "levantamento manual",
      "peso",
      "sobrecarga",
      "repetitiv",
      "movimentacao manual"
    ]
  },
  {
    "nr": "NR-18",
    "terms": [
      "obra",
      "construcao",
      "andaime",
      "escavacao",
      "canteiro",
      "abertura no piso",
      "guarda corpo"
    ]
  },
  {
    "nr": "NR-20",
    "terms": [
      "inflamavel",
      "combustivel",
      "gasolina",
      "diesel",
      "glp",
      "solvente"
    ]
  },
  {
    "nr": "NR-23",
    "terms": [
      "extintor",
      "incendio",
      "hidrante",
      "rota de fuga",
      "saida de emergencia"
    ]
  },
  {
    "nr": "NR-24",
    "terms": [
      "refeitorio",
      "banheiro",
      "sanitario",
      "vestiario",
      "agua potavel"
    ]
  },
  {
    "nr": "NR-26",
    "terms": [
      "sinalizacao",
      "placa",
      "rotulagem",
      "identificacao",
      "produto quimico",
      "recipiente sem identificacao"
    ]
  },
  {
    "nr": "NR-33",
    "terms": [
      "espaco confinado",
      "entrada em tanque",
      "entrada em silo"
    ]
  },
  {
    "nr": "NR-35",
    "terms": [
      "trabalho em altura",
      "altura",
      "linha de vida",
      "ancoragem",
      "cinto paraquedista",
      "queda de nivel",
      "telhado",
      "andaime",
      "guarda corpo"
    ]
  }
];
const NR_LABELS: Readonly<Record<string,string>> = {
  "NR-01": "Gerenciamento de riscos ocupacionais",
  "NR-06": "Equipamento de Proteção Individual",
  "NR-10": "Segurança em instalações e serviços em eletricidade",
  "NR-11": "Transporte, movimentação, armazenagem e manuseio de materiais",
  "NR-12": "Segurança no trabalho em máquinas e equipamentos",
  "NR-13": "Caldeiras, vasos de pressão, tubulações e tanques metálicos",
  "NR-15": "Atividades e operações insalubres",
  "NR-17": "Ergonomia",
  "NR-18": "Segurança e saúde na indústria da construção",
  "NR-20": "Inflamáveis e combustíveis",
  "NR-23": "Proteção contra incêndios",
  "NR-24": "Condições sanitárias e de conforto",
  "NR-26": "Sinalização de segurança",
  "NR-33": "Segurança e saúde em espaços confinados",
  "NR-35": "Trabalho em altura"
};

const ACCENTS: Readonly<Record<string, string>> = {
  'á':'a','à':'a','â':'a','ã':'a','ä':'a',
  'é':'e','è':'e','ê':'e','ë':'e',
  'í':'i','ì':'i','î':'i','ï':'i',
  'ó':'o','ò':'o','ô':'o','õ':'o','ö':'o',
  'ú':'u','ù':'u','û':'u','ü':'u','ç':'c',
};

/** Mesma limpeza da fonte Dart. */
export function normalizeRuleText(input: string): string {
  let value = input.toLowerCase().trim();
  for (const [from, to] of Object.entries(ACCENTS)) value = value.replaceAll(from, to);
  return value.replace(/[^a-z0-9]+/g, ' ').replace(/\s+/g, ' ').trim();
}

function bestProfile(normalized: string): RuleProfile {
  let best: RuleProfile = GENERIC;
  let bestScore = 0;
  for (const profile of PROFILES) {
    let score = 0;
    for (const term of profile.terms) {
      if (normalized.includes(term)) score += term.includes(' ') ? 5 : 2;
    }
    if (score > bestScore) {
      best = profile;
      bestScore = score;
    }
  }
  return best;
}

export function suggestNrs(text: string): string[] {
  const value = normalizeRuleText(text);
  return NR_TERMS
    .filter(({terms}) => terms.some(term => value.includes(term)))
    .map(({nr}) => nr)
    .sort((a, b) => Number(a.replace(/[^0-9]/g, '')) - Number(b.replace(/[^0-9]/g, '')));
}

export function suggestedProbabilityForText(text: string): number {
  return bestProfile(normalizeRuleText(text)).probability;
}

export function suggestedSeverityForText(text: string): number {
  return bestProfile(normalizeRuleText(text)).severity;
}

export function suggestDeadline(priority: string): string {
  switch (priority) {
    case 'Crítica': return 'Imediato / antes da continuidade da condição de risco';
    case 'Alta': return 'Prioritário — sugerido até 7 dias, conforme risco e viabilidade';
    case 'Média': return 'Programar correção — sugerido até 30 dias';
    default: return 'Programar melhoria — sugerido até 60 dias';
  }
}

function withPriority(action: string, priority: string): string {
  if (priority === 'Crítica') {
    return action + ' Tratamento imediato recomendado antes da continuidade da condição de risco.';
  }
  if (priority === 'Alta') {
    return action + ' Priorizar a correção e acompanhar até a conclusão.';
  }
  return action;
}

export function buildActionPlan(text: string, priority: string): string {
  return withPriority(bestProfile(normalizeRuleText(text)).action, priority);
}

export function suggestResponsible(text: string): string {
  return bestProfile(normalizeRuleText(text)).responsible;
}

export function analyzeOfflineField(args: {
  text: string;
  probability: number;
  severity: number;
  recurring?: boolean;
  learnedHistoryMatch?: boolean;
}): OfflineRuleResult {
  const { text, probability, severity, recurring = false, learnedHistoryMatch = false } = args;
  const normalized = normalizeRuleText(text);
  const profile = bestProfile(normalized);
  const nrsFound = suggestNrs(normalized);
  const priority = priorityFromMatrix(probability, severity, recurring);
  return {
    nrs: nrsFound,
    priority,
    score: matrixScore(probability, severity, recurring),
    actionPlan: withPriority(profile.action, priority),
    responsibleSuggestion: profile.responsible,
    deadlineSuggestion: suggestDeadline(priority),
    possibleRecurrence: recurring || learnedHistoryMatch,
    category: profile.category,
    riskSummary: profile.risk,
    consequenceSummary: profile.consequence,
    evidenceSuggestion: profile.evidence,
    technicalReason: profile.reason,
    nrDetails: nrsFound.map(nr => NR_LABELS[nr] ? nr + ' — ' + NR_LABELS[nr] : nr),
    suggestedProbability: profile.probability,
    suggestedSeverity: profile.severity,
  };
}
