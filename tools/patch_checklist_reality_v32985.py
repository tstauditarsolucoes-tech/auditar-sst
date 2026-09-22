#!/usr/bin/env python3
from pathlib import Path
import re, sys

if len(sys.argv) < 2:
    raise SystemExit("uso: patch_checklist_reality_v32985.py <APP_DIR> [android|windows]")

root = Path(sys.argv[1])
platform = (sys.argv[2] if len(sys.argv) > 2 else "android").lower()
ready_path = root / "lib/ready_checklists.dart"
new_path = root / "lib/screens/new_inspection_screen.dart"
pubspec_path = root / "pubspec.yaml"

for path in (ready_path, new_path, pubspec_path):
    if not path.exists():
        raise SystemExit(f"arquivo ausente: {path}")

bad_common = {
    "Os riscos observados no setor estão contemplados no inventário de riscos e nas medidas de prevenção aplicáveis?",
    "Os trabalhadores utilizam os EPIs definidos para os riscos existentes no setor?",
    "Máquinas e equipamentos existentes apresentam proteções, comandos e condições seguras de operação?",
    "Pisos, acessos e rotas de circulação estão desobstruídos e sem condições evidentes de queda ou colisão?",
    "Saídas, rotas e equipamentos de resposta a incêndio permanecem acessíveis e sem obstruções?",
    "Riscos, áreas restritas, equipamentos e produtos estão identificados e sinalizados quando necessário?",
}

# Itens de abertura próprios para modelos que haviam recebido o mesmo bloco genérico.
# Os itens específicos já existentes em cada modelo são preservados.
tailored = {
"ready-manut-mecanica-geral": [
("Organização","Piso, acessos e área de manutenção estão sem óleo, peças, cabos, mangueiras ou ferramentas criando risco de queda ou tropeço?","NR-01 / NR-17","Alta"),
("EPI da tarefa","Os EPIs definidos para as tarefas de manutenção realmente executadas no momento estão disponíveis, conservados e sendo utilizados?","NR-06","Alta"),
("Emergência","Extintores, saídas e acessos de emergência da área de manutenção permanecem livres e acessíveis?","NR-23","Crítica"),
("Sinalização","Equipamentos interditados, áreas de intervenção e riscos temporários da manutenção estão identificados ou isolados quando necessário?","NR-01 / NR-26","Alta"),
],
"ready-manut-oficina-mecanica": [
("Organização da oficina","Piso, bancadas e circulação estão livres de óleo, sucata, cabos, mangueiras e peças soltas?","NR-01 / NR-17","Alta"),
("EPI da tarefa","Os EPIs usados correspondem aos riscos das atividades que estão sendo executadas, como projeção, ruído, corte, solda ou produtos químicos?","NR-06","Alta"),
("Emergência","Extintores e rotas de saída da oficina estão acessíveis e sem materiais armazenados à frente?","NR-23","Crítica"),
("Sinalização","Máquinas fora de serviço, cilindros, produtos e áreas de risco estão identificados quando necessário?","NR-26","Média"),
],
"ready-ceramica-producao-telhas": [
("Circulação","A circulação entre máquinas e postos está livre de telhas quebradas, carrinhos, cabos e outros obstáculos?","NR-01","Alta"),
("EPI","Os EPIs definidos para poeira, ruído e demais riscos realmente existentes na fabricação de telhas estão sendo utilizados?","NR-06","Alta"),
("Emergência","Rotas e equipamentos de emergência do setor permanecem acessíveis e sem materiais à frente?","NR-23","Crítica"),
("Sinalização","Zonas perigosas, áreas restritas e pontos de circulação de máquinas estão identificados quando necessário?","NR-26","Alta"),
],
"ready-ceramica-secadores-telhas": [
("Circulação","Corredores, trilhos e áreas de passagem junto aos secadores estão desobstruídos e em condição segura?","NR-01","Alta"),
("EPI","Os EPIs definidos para calor, poeira, ruído ou outros riscos presentes na atividade estão sendo utilizados?","NR-06","Alta"),
("Emergência","Rotas de saída e recursos de emergência da área dos secadores permanecem acessíveis?","NR-23","Crítica"),
("Sinalização","Zonas quentes, áreas restritas e pontos de risco dos secadores estão identificados e sinalizados quando necessário?","NR-26","Alta"),
],
"ready-ceramica-expedicao": [
("Circulação","A circulação de pessoas e veículos está organizada durante o carregamento e a expedição?","NR-11 / NR-26","Crítica"),
("EPI","Os EPIs definidos para carregamento, movimentação e amarração das cargas estão sendo utilizados?","NR-06","Alta"),
("Emergência","Os acessos e equipamentos de emergência próximos à expedição permanecem livres?","NR-23","Alta"),
("Piso","A área de carga está sem telhas quebradas, materiais ou irregularidades que aumentem o risco de queda ou colisão?","NR-01","Alta"),
],
"ready-ceramica-patio-barreiro": [
("EPI","Os EPIs definidos para a atividade no pátio ou barreiro estão sendo utilizados?","NR-06","Alta"),
("Visibilidade","Poeira, iluminação, chuva ou outras condições do ambiente não comprometem a visibilidade necessária à operação segura?","NR-01 / NR-21","Alta"),
("Sinalização","Rotas, cavas, bordas, áreas de manobra e pontos de acesso restrito estão identificados ou isolados quando necessário?","NR-26","Crítica"),
("Comunicação","Há forma segura de comunicação entre operadores, motoristas e pessoas que precisam acessar a área durante manobras?","NR-11","Alta"),
],
"ready-colchoes-geral": [
("Circulação","Corredores e áreas de produção estão livres de espumas, retalhos, filmes plásticos e outros materiais no piso?","NR-01","Alta"),
("EPI","Os EPIs definidos para corte, colagem, moagem, ruído ou outros riscos efetivamente presentes estão sendo utilizados?","NR-06","Alta"),
("Emergência","Saídas e equipamentos de combate a incêndio permanecem livres de espumas, colchões, tecidos e embalagens?","NR-23","Crítica"),
("Sinalização","Áreas de máquinas, produtos químicos e riscos de incêndio estão identificadas quando necessário?","NR-26","Média"),
],
"ready-colchoes-costura": [
("Organização","Linhas, retalhos, cabos e materiais não estão acumulados na área dos pedais e da circulação?","NR-01 / NR-17","Média"),
("Emergência","Rotas e equipamentos de incêndio do setor permanecem desobstruídos por tecidos, carrinhos ou materiais?","NR-23","Crítica"),
("Elétrica","Tomadas, cabos, pedais e ligações das máquinas de costura estão íntegros e sem improvisações?","NR-10 / NR-12","Alta"),
],
"ready-colchoes-bordado": [
("Organização","Linhas, tecidos, cabos e materiais não obstruem a circulação e o acesso ao equipamento?","NR-01","Média"),
("Emergência","Rotas de saída e recursos de emergência permanecem livres de materiais do setor?","NR-23","Crítica"),
("Elétrica","Cabos, tomadas, painéis e ligações do equipamento de bordado estão íntegros e sem improvisações?","NR-10 / NR-12","Alta"),
],
"ready-colchoes-tapecaria": [
("Circulação","Colchões, tecidos, mangueiras e materiais não bloqueiam a movimentação segura no posto?","NR-01 / NR-17","Alta"),
("Emergência","Colchões e materiais não bloqueiam saídas nem equipamentos de combate a incêndio?","NR-23","Crítica"),
("Mangueiras e conexões","Mangueiras e conexões pneumáticas estão íntegras, fixadas e posicionadas sem criar risco de chicoteamento ou tropeço?","NR-12","Alta"),
],
"ready-colchoes-embalagem": [
("Circulação","Colchões, filmes e materiais de embalagem não bloqueiam corredores e áreas de movimentação?","NR-01","Alta"),
("Emergência","Volumes embalados não bloqueiam saídas nem equipamentos de combate a incêndio?","NR-23","Crítica"),
("Elétrica","Seladoras e demais equipamentos elétricos estão ligados sem cabos, tomadas ou extensões improvisadas?","NR-10 / NR-12","Alta"),
],
"ready-colchoes-almoxarifado": [
("EPI de movimentação","Quando a movimentação do material exigir proteção específica, os EPIs definidos estão sendo utilizados?","NR-06","Média"),
("Iluminação","Corredores, prateleiras e pontos de retirada possuem iluminação suficiente para movimentação segura?","NR-01","Média"),
("Sinalização","Limites de armazenamento, produtos e áreas restritas estão identificados quando necessário?","NR-11 / NR-26","Alta"),
],
"ready-colchoes-expedicao": [
("EPI","Os EPIs definidos para movimentação, carregamento e demais riscos presentes na expedição estão sendo utilizados?","NR-06","Alta"),
("Iluminação","A área possui iluminação suficiente para movimentação dos volumes e manobras de veículos?","NR-01","Média"),
("Emergência","Saídas e equipamentos de emergência permanecem livres durante o carregamento e armazenamento temporário?","NR-23","Crítica"),
],
"ready-logistica-almoxarifado": [
("Iluminação","Corredores, prateleiras e áreas de separação possuem iluminação suficiente para movimentação segura?","NR-01","Média"),
("Acesso às prateleiras","Escadas ou meios utilizados para alcançar níveis superiores são adequados e estão em condição segura?","NR-01","Alta"),
("EPI de movimentação","Quando a tarefa exigir EPI, o equipamento definido para o risco está disponível e sendo utilizado?","NR-06","Média"),
],
"ready-logistica-recebimento": [
("EPI","Os EPIs definidos para descarga e movimentação do material recebido estão sendo utilizados?","NR-06","Alta"),
("Piso","A área de descarga está sem materiais, embalagens, desníveis ou derramamentos que comprometam a movimentação?","NR-01","Alta"),
("Sinalização","A zona de recebimento e movimentação de cargas está sinalizada ou isolada quando necessário?","NR-11 / NR-26","Crítica"),
("Iluminação","A iluminação permite visualizar pessoas, cargas, desníveis e equipamentos durante a descarga?","NR-01","Alta"),
],
"ready-logistica-expedicao": [
("EPI","Os EPIs definidos para carregamento e movimentação das cargas estão sendo utilizados?","NR-06","Alta"),
("Piso","A área de expedição está sem obstáculos, materiais soltos ou derramamentos que prejudiquem a movimentação?","NR-01","Alta"),
("Sinalização","A zona de carregamento está identificada e controlada durante manobras e movimentação de cargas?","NR-11 / NR-26","Crítica"),
("Iluminação","A iluminação permite realizar carregamento e manobras com visibilidade adequada?","NR-01","Alta"),
],
"ready-apoio-administrativo": [
("Arquivos e armários","Armários, arquivos e estantes estão estáveis, sem sobrecarga aparente ou risco de queda de materiais?","NR-01","Alta"),
("Iluminação e conforto","A iluminação e as condições do ambiente permitem trabalho com computador e leitura sem desconforto evidente?","NR-17","Média"),
("Instalações elétricas","Tomadas, filtros de linha e equipamentos do escritório estão sem sobrecarga ou ligações improvisadas?","NR-10","Alta"),
],
"ready-telecom-geral": [
("EPI da atividade","Os EPIs definidos para a atividade realmente executada, inclusive altura e eletricidade quando aplicáveis, estão sendo utilizados?","NR-06 / NR-10 / NR-35","Alta"),
("Ferramentas e acesso","Ferramentas, escadas e demais meios de acesso utilizados no serviço estão em condição segura e compatíveis com a tarefa?","NR-12 / NR-35","Alta"),
("Comunicação","A equipe possui meio de comunicação compatível com a atividade, especialmente em locais isolados, altura ou via pública?","NR-01","Alta"),
],
"ready-telecom-sala-tecnica": [
("Acesso","O acesso à sala técnica é controlado quando houver equipamentos elétricos, baterias ou outros riscos que exijam restrição?","NR-10","Alta"),
("Circulação","Piso, passagens e frente dos racks estão livres de caixas, cabos e materiais que dificultem acesso seguro?","NR-01 / NR-10","Alta"),
("Incêndio","Materiais combustíveis desnecessários não estão acumulados junto a racks, fontes e baterias, e os recursos de emergência permanecem acessíveis?","NR-23","Crítica"),
],
"ready-saude-clinica": [
("EPI e barreiras","Os EPIs e demais barreiras definidos para os procedimentos realmente realizados na clínica estão disponíveis e sendo utilizados?","NR-06 / NR-32","Crítica"),
("Circulação","Pisos, acessos e áreas de atendimento estão livres de obstáculos, materiais ou líquidos que possam causar quedas ou dificultar atendimento seguro?","NR-01 / NR-32","Alta"),
("Emergência","Rotas de saída e equipamentos de emergência permanecem acessíveis, inclusive durante o atendimento?","NR-23","Crítica"),
("Produtos químicos","Desinfetantes, saneantes e outros produtos utilizados estão identificados e armazenados de forma segura?","NR-26 / NR-32","Alta"),
],
}

def find_definition(text: str, ident: str):
    pos = text.find("id: '" + ident + "'")
    if pos < 0:
        return None
    start = text.rfind("ReadyChecklistDefinition(", 0, pos)
    if start < 0:
        return None
    op = text.find("(", start)
    depth = 0
    quote = None
    escape = False
    for i in range(op, len(text)):
        ch = text[i]
        if quote:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == quote:
                quote = None
            continue
        if ch in ("'", '"'):
            quote = ch
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                return start, i + 1
    return None

def dart_item(item):
    category, text, reference, priority = item
    esc = lambda v: v.replace("\\", "\\\\").replace("'", "\\'")
    return (
        "      ReadyChecklistItem(category: '" + esc(category) +
        "', text: '" + esc(text) +
        "', reference: '" + esc(reference) +
        "', priority: '" + esc(priority) + "'),"
    )

for ident, replacements in tailored.items():
    loc = find_definition(s, ident) if (s := ready_path.read_text(encoding="utf-8")) else None
    if loc is None:
        raise SystemExit(f"checklist não localizado: {ident}")
    start, end = loc
    block = s[start:end]
    if all(q not in block for q in bad_common):
        # Já aplicado: só valida presença de ao menos um item novo.
        if replacements and replacements[0][1] not in block:
            raise SystemExit(f"{ident}: bloco genérico já não existe, mas revisão não foi localizada")
        continue
    lines = block.splitlines()
    cleaned = [line for line in lines if not any(q in line for q in bad_common)]
    insert_at = next((i + 1 for i, line in enumerate(cleaned) if "items: [" in line), None)
    if insert_at is None:
        raise SystemExit(f"{ident}: lista de itens não localizada")
    cleaned[insert_at:insert_at] = [dart_item(item) for item in replacements]
    new_block = "\n".join(cleaned)
    ready_path.write_text(s[:start] + new_block + s[end:], encoding="utf-8")

s = ready_path.read_text(encoding="utf-8")
renames = {
    "Checklist Geral NR-12 Panificação":
        "NR-12 Panificação - Avaliação Geral (quando não houver modelo específico)",
    "Vistoria de Máquinas - Setor de Panificação":
        "Máquina de Panificação - Vistoria Genérica",
    "Vistoria Geral - Padaria / Panificação":
        "Vistoria Geral - Padaria / Ambiente de Panificação",
}
for old, new in renames.items():
    s = s.replace("name: '" + old + "'", "name: '" + new + "'")
ready_path.write_text(s, encoding="utf-8")

new_src = new_path.read_text(encoding="utf-8")
pattern = re.compile(
    r"  List<ChecklistItem> _removeCombinedRepetitions\(\s*"
    r"List<ChecklistItem> source,\s*\) \{.*?^  \}\n\n"
    r"  Future<void> _start\(\) async \{",
    re.S | re.M,
)
replacement = r"""  List<ChecklistItem> _removeCombinedRepetitions(
    List<ChecklistItem> source,
  ) {
    final coveredDomains = _coveredGeneralDomains();
    final selectedIds = selectedTemplates.map((template) => template.id).toSet();

    const panSpecificMachineIds = <String>{
      'ready-panificacao-amassadeira',
      'ready-panificacao-cilindro',
      'ready-panificacao-modeladora',
      'ready-panificacao-fatiadora',
      'ready-panificacao-batedeira',
      'ready-panificacao-laminadora',
      'ready-panificacao-moinho-farinha-rosca',
      'ready-panificacao-fornos',
    };

    final hasPanSpecificMachine =
        selectedIds.any(panSpecificMachineIds.contains);
    final hasPanGenericMachine =
        selectedIds.contains('ready-panificacao-vistoria-maquinas');

    final seenQuestions = <String>{};
    final result = <ChecklistItem>[];

    // Modelos específicos vêm primeiro. Modelos gerais servem como complemento
    // e não repetem a inspeção da mesma máquina.
    final ordered = [
      ...source.where((item) => item.templateId != 'template-geral-sst'),
      ...source.where((item) => item.templateId == 'template-geral-sst'),
    ];

    for (final item in ordered) {
      if (item.templateId == 'template-geral-sst' &&
          coveredDomains.contains(item.category)) {
        continue;
      }

      // Panificação: ao escolher uma máquina específica, os dois modelos
      // genéricos de máquina deixam de repetir proteção, parada, elétrica,
      // limpeza, transmissão etc. O checklist geral do ambiente continua,
      // mas sua pergunta ampla de "Máquinas" é retirada.
      if (hasPanSpecificMachine &&
          (item.templateId == 'ready-panificacao-nr12-geral' ||
              item.templateId == 'ready-panificacao-vistoria-maquinas')) {
        continue;
      }
      if (hasPanSpecificMachine &&
          item.templateId == 'ready-panificacao-vistoria-geral-padaria' &&
          item.category == 'Máquinas') {
        continue;
      }

      // Se os dois modelos genéricos de máquinas de panificação forem
      // selecionados juntos, mantém somente o mais detalhado de vistoria.
      if (!hasPanSpecificMachine &&
          hasPanGenericMachine &&
          item.templateId == 'ready-panificacao-nr12-geral') {
        continue;
      }

      if (seenQuestions.add(_normalizedQuestion(item.text))) {
        result.add(item);
      }
    }
    return result;
  }

  Future<void> _start() async {"""
new_src2, count = pattern.subn(replacement, new_src, count=1)
if count != 1:
    if "panSpecificMachineIds" not in new_src:
        raise SystemExit("função _removeCombinedRepetitions não localizada")
    new_src2 = new_src

# Não declarar no relatório um modelo genérico que ficou sem item após a
# composição com um checklist específico.
old_meta = """    final now = DateTime.now();
    final checklistNames =
        selectedTemplates.map((template) => template.name).join(' + ');
    final checklistIds =
        selectedTemplates.map((template) => template.id).join('|');
"""
new_meta = """    final now = DateTime.now();
    final activeTemplateIds =
        filteredItems.map((item) => item.templateId).toSet();
    final activeTemplates = selectedTemplates
        .where((template) => activeTemplateIds.contains(template.id))
        .toList();
    final checklistNames =
        activeTemplates.map((template) => template.name).join(' + ');
    final checklistIds =
        activeTemplates.map((template) => template.id).join('|');
"""
if old_meta in new_src2:
    new_src2 = new_src2.replace(old_meta, new_meta, 1)
elif "final activeTemplateIds =" not in new_src2:
    raise SystemExit("bloco de metadados da vistoria não localizado")

new_src2 = new_src2.replace(
    "'$removedRepetitions pergunta(s) geral(is) repetida(s) foram '",
    "'$removedRepetitions pergunta(s) geral(is) ou sobreposta(s) foram '",
)
new_path.write_text(new_src2, encoding="utf-8")

pub = pubspec_path.read_text(encoding="utf-8")
target = "3.30.12+199" if platform == "windows" else "3.29.85+227"
pub2, n = re.subn(r"(?m)^version:\s*[^\r\n]+", "version: " + target, pub, count=1)
if n != 1:
    raise SystemExit("version do pubspec não localizada")
pubspec_path.write_text(pub2, encoding="utf-8")

# Regressões de conteúdo.
final_ready = ready_path.read_text(encoding="utf-8")
for ident, replacements in tailored.items():
    loc = find_definition(final_ready, ident)
    if loc is None:
        raise SystemExit(f"regressão: {ident} ausente")
    block = final_ready[loc[0]:loc[1]]
    if any(q in block for q in bad_common):
        raise SystemExit(f"regressão: bloco genérico ainda presente em {ident}")
    for item in replacements:
        if item[1] not in block:
            raise SystemExit(f"regressão: item revisado ausente em {ident}")

if "panSpecificMachineIds" not in new_path.read_text(encoding="utf-8"):
    raise SystemExit("regressão: deduplicação contextual de panificação ausente")

print(f"Revisão contextual de checklists aplicada: {target} ({platform}).")
