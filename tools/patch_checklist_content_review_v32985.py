#!/usr/bin/env python3
from pathlib import Path
import re, sys

root = Path(sys.argv[1])
platform = (sys.argv[2] if len(sys.argv) > 2 else 'android').lower()
keep_version = '--keep-version' in sys.argv[3:]

def read(rel):
    return (root / rel).read_text(encoding='utf-8')

def write(rel, text):
    (root / rel).write_text(text, encoding='utf-8', newline='\n')

def q(value):
    return value.replace("\\", "\\\\").replace("'", "\\'")

def item(category, text, reference, priority):
    return (
        "ReadyChecklistItem(category: '" + q(category) +
        "', text: '" + q(text) +
        "', reference: '" + q(reference) +
        "', priority: '" + q(priority) + "')"
    )

# -----------------------------------------------------------------
# 1) CONTEÚDO: substituir o bloco genérico copiado em 20 modelos
#    por seis verificações compatíveis com a realidade de cada área.
# -----------------------------------------------------------------
replacements = {
'ready-manut-mecanica-geral': [
 ('Planejamento do serviço','Os riscos específicos do serviço de manutenção foram avaliados antes do início e as medidas de prevenção necessárias estão definidas?','NR-01','Alta'),
 ('EPI da tarefa','Os EPIs utilizados correspondem aos riscos reais da intervenção, como projeção, ruído, corte, contato químico ou soldagem, quando aplicável?','NR-06','Alta'),
 ('Energias perigosas','Antes de intervir em máquinas, as fontes de energia são identificadas, isoladas e controladas contra acionamento inesperado?','NR-12','Crítica'),
 ('Área de manutenção','Peças, ferramentas, mangueiras, cabos e materiais estão organizados sem criar risco de tropeço, queda ou colisão?','NR-01','Alta'),
 ('Trabalho a quente','Solda, corte ou esmerilhamento, quando realizados, possuem controle de faíscas, materiais combustíveis e recursos de emergência?','NR-23','Crítica'),
 ('Óleos e produtos','Óleos, graxas, desengraxantes e outros produtos utilizados estão identificados e armazenados sem recipientes improvisados?','NR-26','Alta'),
],
'ready-manut-oficina-mecanica': [
 ('Organização da oficina','Bancadas, corredores e áreas de trabalho permanecem organizados, sem ferramentas, peças ou mangueiras criando risco de acidente?','NR-01','Alta'),
 ('EPI por atividade','Os EPIs são definidos conforme a tarefa executada, como corte, lixamento, solda, uso de produtos químicos ou projeção de partículas?','NR-06','Alta'),
 ('Máquinas da oficina','As máquinas realmente existentes na oficina possuem suas proteções aplicáveis e não apresentam dispositivos de segurança neutralizados?','NR-12','Crítica'),
 ('Instalações elétricas','Tomadas, extensões e cabos utilizados na oficina estão íntegros e protegidos contra danos e improvisações?','NR-10','Alta'),
 ('Incêndio e faíscas','Materiais combustíveis, cilindros e produtos inflamáveis permanecem afastados de faíscas e fontes de calor quando necessário?','NR-23','Crítica'),
 ('Armazenamento','Peças, ferramentas, sucatas e materiais pesados estão armazenados de forma estável e sem risco de queda?','NR-11','Alta'),
],
'ready-ceramica-producao-telhas': [
 ('Proteção de máquinas','Prensas, modeladoras, cortadores e demais equipamentos realmente existentes no setor possuem proteção nas zonas de esmagamento, corte e arraste?','NR-12','Crítica'),
 ('Poeira','Há medidas de controle para reduzir a dispersão e o acúmulo de poeira de argila no posto e nas áreas de circulação?','NR-09','Alta'),
 ('EPI','Os trabalhadores utilizam os EPIs definidos para os riscos efetivamente presentes na produção?','NR-06','Alta'),
 ('Circulação','Telhas, carrinhos, pallets e resíduos não bloqueiam passagens nem criam risco de tropeço ou colisão?','NR-01','Alta'),
 ('Movimentação','A movimentação de peças e carrinhos ocorre sem colocar trabalhadores entre cargas, estruturas ou equipamentos em movimento?','NR-11','Crítica'),
 ('Sinalização','Zonas de máquinas, circulação de equipamentos e outros riscos relevantes do setor estão identificados quando necessário?','NR-26','Média'),
],
'ready-ceramica-secadores-telhas': [
 ('Calor','A exposição ao calor e a permanência nas áreas mais quentes são controladas conforme as condições reais da atividade?','NR-09','Alta'),
 ('Superfícies quentes','Superfícies com possibilidade de contato e queimadura possuem proteção, isolamento ou sinalização compatível com o risco?','NR-14 / NR-26','Alta'),
 ('Movimentação','Vagões, carrinhos ou sistemas de transporte associados aos secadores circulam sem expor pessoas a esmagamento ou colisão?','NR-11 / NR-12','Crítica'),
 ('Ventiladores e transmissões','Ventiladores, correias, eixos e transmissões acessíveis possuem proteção contra contato acidental?','NR-12','Crítica'),
 ('Acesso e circulação','Acessos aos secadores e áreas de circulação permanecem livres de peças quebradas, obstáculos e materiais soltos?','NR-01','Alta'),
 ('Intervenções','Limpeza, desobstrução e manutenção são realizadas com controle das energias perigosas e da condição térmica quando necessário?','NR-12','Crítica'),
],
'ready-ceramica-expedicao': [
 ('Empilhamento','Pilhas, pallets e conjuntos de telhas permanecem estáveis e sem inclinação ou peças com risco de queda sobre pessoas?','NR-11','Crítica'),
 ('Tráfego','Pedestres e veículos possuem circulação organizada durante carregamento, retirada e manobra?','NR-11','Crítica'),
 ('Carga de veículos','Durante o carregamento, trabalhadores permanecem fora de pontos de esmagamento, queda de materiais e zona de manobra?','NR-11','Crítica'),
 ('Piso e circulação','O piso e os corredores da expedição estão livres de telhas quebradas, cintas, pallets e outros obstáculos?','NR-01','Alta'),
 ('Ergonomia','A movimentação manual de telhas é organizada para reduzir peso excessivo, alcance desfavorável e repetitividade?','NR-17','Alta'),
 ('EPI','Os EPIs definidos para movimentação, carregamento e risco de impacto/corte estão disponíveis e sendo utilizados?','NR-06','Alta'),
],
'ready-ceramica-patio-barreiro': [
 ('Tráfego de máquinas','Rotas de pá carregadeira, caminhões e pedestres estão organizadas para evitar aproximação indevida e pontos cegos?','NR-11','Crítica'),
 ('Condição do terreno','Vias e áreas de operação não apresentam buracos, lama, bordas ou desníveis que comprometam estabilidade e circulação segura?','NR-01','Alta'),
 ('Máquina móvel','Freios, alarme, iluminação, pneus e itens de segurança da máquina móvel em uso estão em condições adequadas?','NR-11 / NR-12','Crítica'),
 ('Taludes e cavas','A operação próxima a bordas, cavas ou taludes mantém distância e condição segura contra queda ou tombamento?','NR-01','Crítica'),
 ('Acesso de terceiros','Pessoas sem relação com a atividade permanecem fora das zonas de operação e carregamento?','NR-01 / NR-26','Alta'),
 ('Exposição externa','As condições de poeira, calor, radiação solar e intempéries são consideradas nas medidas de prevenção da atividade?','NR-01 / NR-21','Alta'),
],
'ready-colchoes-geral': [
 ('Materiais combustíveis','Espumas, tecidos e embalagens estão armazenados sem bloquear saídas e afastados de fontes de ignição?','NR-23','Crítica'),
 ('Máquinas do processo','Máquinas de corte, laminação, costura, bordado, moagem e outras existentes possuem as proteções aplicáveis ao seu risco?','NR-12','Crítica'),
 ('Adesivos e químicos','Adesivos, solventes e produtos químicos utilizados estão identificados, fechados e armazenados de forma compatível com seus riscos?','NR-26','Alta'),
 ('Circulação','Corredores entre setores, estoques e máquinas permanecem livres de espumas, tecidos, embalagens e outros obstáculos?','NR-01','Alta'),
 ('Ergonomia','A organização dos postos considera repetitividade, permanência em pé, levantamento e movimentação de colchões e materiais?','NR-17','Alta'),
 ('Incêndio','Extintores, saídas e rotas de emergência permanecem acessíveis diante da carga de materiais combustíveis existente?','NR-23','Crítica'),
],
'ready-colchoes-costura': [
 ('Agulhas e mecanismos','Agulhas, correias, polias e mecanismos acessíveis das máquinas de costura possuem as proteções aplicáveis e estão conservados?','NR-12','Alta'),
 ('Postura','Cadeira, mesa, pedal e posição do material permitem ajuste e postura compatíveis com a tarefa?','NR-17','Alta'),
 ('Repetitividade','A organização do trabalho considera variação de tarefa, pausas ou outras medidas definidas na avaliação ergonômica?','NR-17','Alta'),
 ('Iluminação','A iluminação permite costurar e inspecionar o material sem sombras ou ofuscamento relevante no posto?','NR-17','Média'),
 ('Cabos e pedais','Cabos, extensões e pedais estão posicionados sem improvisações elétricas ou risco de tropeço?','NR-10 / NR-01','Alta'),
 ('Organização','Tecidos, linhas, peças e recipientes não obstruem a circulação nem os movimentos do operador?','NR-01','Média'),
],
'ready-colchoes-bordado': [
 ('Zona das agulhas','A zona de agulhas e cabeçotes permanece protegida contra acesso durante o movimento automático?','NR-12','Crítica'),
 ('Parada','Os comandos de parada e emergência previstos para a máquina estão acessíveis ao operador e funcionais?','NR-12','Crítica'),
 ('Intervenção','Enfiamento, limpeza, troca de agulha e manutenção são feitos com o movimento perigoso interrompido?','NR-12','Alta'),
 ('Área de movimento','A área de deslocamento do cabeçote, bastidor ou estrutura móvel permanece livre de pessoas e objetos durante a operação?','NR-12','Crítica'),
 ('Ergonomia','Abastecimento de linhas, posicionamento e retirada de material evitam alcances excessivos e esforço desnecessário?','NR-17','Média'),
 ('Organização','Linhas, tecidos, caixas e cabos estão organizados sem interferir na circulação ou nos movimentos da máquina?','NR-01','Média'),
],
'ready-colchoes-tapecaria': [
 ('Ferramentas pneumáticas','Grampeadores, pistolas pneumáticas, mangueiras e conexões estão íntegros e sem acionamento improvisado?','NR-12','Alta'),
 ('Projeção de grampos','A atividade é organizada para que nenhuma pessoa permaneça na direção de possível projeção de grampos ou partículas?','NR-01','Crítica'),
 ('Proteção das mãos e olhos','Os EPIs definidos para risco de perfuração, projeção e demais exposições da tarefa estão sendo utilizados?','NR-06','Alta'),
 ('Postura','A altura e o posicionamento da peça reduzem flexão excessiva do tronco e alcance prolongado durante a montagem?','NR-17','Alta'),
 ('Movimentação de colchões','Há método e espaço suficientes para virar e deslocar colchões sem prensar mãos ou causar esforço excessivo?','NR-17','Alta'),
 ('Organização','Grampos, agulhas, ferramentas, mangueiras e resíduos não permanecem espalhados pelo piso e área de trabalho?','NR-01','Alta'),
],
'ready-colchoes-embalagem': [
 ('Seladoras e partes quentes','Seladoras, resistências e superfícies aquecidas possuem proteção ou condição que evite contato acidental durante a operação?','NR-12','Alta'),
 ('Filme plástico','Filmes, aparas e embalagens descartadas são retirados do piso para evitar escorregamento e obstrução?','NR-01','Alta'),
 ('Movimentação','A embalagem e movimentação de colchões são organizadas para reduzir levantamento, compressão manual e posturas forçadas?','NR-17','Alta'),
 ('Máquinas de embalagem','Equipamentos de compressão ou embalagem existentes possuem proteção nos pontos de esmagamento e comandos acessíveis?','NR-12','Crítica'),
 ('Circulação','A área permite movimentar o colchão sem atingir pessoas, estruturas ou bloquear corredores?','NR-01','Alta'),
 ('Incêndio','Materiais plásticos e combustíveis não obstruem saídas nem ficam acumulados junto a fontes de calor?','NR-23','Crítica'),
],
'ready-colchoes-almoxarifado': [
 ('Espumas e tecidos','Espumas, tecidos e outros materiais combustíveis estão organizados sem bloquear saídas e afastados de fontes de ignição?','NR-23','Crítica'),
 ('Empilhamento','Blocos de espuma, rolos, caixas e outros materiais estão apoiados e empilhados de forma estável?','NR-11','Alta'),
 ('Corredores','Corredores e acesso a equipamentos de emergência permanecem livres em toda a área de armazenagem?','NR-11 / NR-23','Crítica'),
 ('Prateleiras','Estantes e estruturas de armazenagem não apresentam deformações, instabilidade ou sobrecarga aparente?','NR-11','Alta'),
 ('Produtos químicos','Adesivos e outros produtos químicos armazenados estão identificados e segregados conforme seus riscos?','NR-26','Alta'),
 ('Movimentação manual','Materiais pesados ou volumosos são posicionados e movimentados de modo a reduzir esforço e alcance inadequados?','NR-17','Alta'),
],
'ready-colchoes-expedicao': [
 ('Carga manual','O método de movimentação reduz levantamento excessivo, transporte manual desnecessário e torção do tronco?','NR-17','Alta'),
 ('Veículos','O veículo permanece imobilizado e a área de carga tem circulação de pessoas controlada durante a operação?','NR-11','Alta'),
 ('Acondicionamento','Colchões e volumes são acondicionados de forma estável no estoque e no veículo, sem risco aparente de queda?','NR-11','Alta'),
 ('Zona de manobra','Trabalhadores permanecem fora da trajetória de veículos e de pontos de prensamento durante manobras?','NR-11','Crítica'),
 ('Piso e acessos','A área de expedição está livre de filmes, cintas, pallets e outros materiais que prejudiquem a circulação?','NR-01','Alta'),
 ('Incêndio','Saídas e equipamentos de emergência permanecem acessíveis mesmo durante a formação temporária das cargas?','NR-23','Crítica'),
],
'ready-logistica-almoxarifado': [
 ('Empilhamento','Materiais, pallets e volumes estão empilhados de forma estável e compatível com as estruturas de armazenagem?','NR-11','Crítica'),
 ('Prateleiras','Prateleiras e porta-paletes não apresentam danos, deformações, proteção deslocada ou sobrecarga aparente?','NR-11','Alta'),
 ('Corredores','Corredores de pedestres e equipamentos de movimentação permanecem livres e com largura compatível com o uso?','NR-11','Alta'),
 ('Tráfego interno','Quando há empilhadeira ou paleteira, a circulação é organizada para reduzir conflito com pedestres?','NR-11','Crítica'),
 ('Ergonomia','Materiais pesados e de uso frequente estão posicionados para reduzir levantamento e alcance inadequados?','NR-17','Alta'),
 ('Emergência','Saídas, extintores e demais recursos de emergência permanecem livres e identificáveis entre os materiais armazenados?','NR-23','Crítica'),
],
'ready-logistica-recebimento': [
 ('Imobilização do veículo','O veículo permanece imobilizado de forma segura durante o recebimento e a descarga?','NR-11','Crítica'),
 ('Zona de descarga','Pessoas permanecem fora da área de queda, giro, esmagamento e movimentação da carga?','NR-11','Crítica'),
 ('Equipamentos de movimentação','Empilhadeiras, paleteiras, talhas e acessórios realmente utilizados estão adequados e em condição segura?','NR-11 / NR-12','Alta'),
 ('Pedestres','A circulação de pedestres é controlada durante manobras e movimentação de cargas?','NR-11','Crítica'),
 ('Carga manual','O descarregamento manual é organizado para reduzir peso, distância, alcance e posturas forçadas?','NR-17','Alta'),
 ('Piso e doca','Piso, bordas, rampas e área de descarga não apresentam condição evidente de queda, tombamento ou colisão?','NR-01 / NR-11','Alta'),
],
'ready-logistica-expedicao': [
 ('Acondicionamento','A carga está estável e protegida contra deslocamento ou queda durante preparação e carregamento?','NR-11','Alta'),
 ('Zona de manobra','Há controle para impedir permanência de pessoas na trajetória de veículos e equipamentos durante a operação?','NR-11','Crítica'),
 ('Doca e bordas','Desníveis, bordas e plataformas de carga possuem proteção ou sinalização compatível com o risco?','NR-11','Alta'),
 ('Equipamentos de movimentação','Empilhadeiras, paleteiras e outros equipamentos utilizados na expedição apresentam condição segura de operação?','NR-11 / NR-12','Alta'),
 ('Ergonomia','A movimentação manual é organizada para reduzir peso, distância de transporte e posturas forçadas?','NR-17','Alta'),
 ('Emergência','Cargas temporariamente posicionadas não bloqueiam saídas nem equipamentos de emergência?','NR-23','Crítica'),
],
'ready-apoio-administrativo': [
 ('Iluminação','A iluminação do escritório é suficiente para leitura e uso de computador sem ofuscamento relevante?','NR-17','Média'),
 ('Conforto do ambiente','Ventilação, temperatura e organização do ambiente são compatíveis com a permanência e as atividades administrativas?','NR-17','Média'),
 ('Armazenamento','Armários, estantes, arquivos e caixas estão estáveis e organizados sem risco aparente de queda de materiais?','NR-01','Alta'),
 ('Tomadas e equipamentos','Tomadas, filtros de linha e equipamentos elétricos de escritório estão íntegros, sem sobrecarga ou adaptações improvisadas?','NR-10','Alta'),
 ('Piso e circulação','Pisos, tapetes, caixas e mobiliário não criam risco de tropeço nem estreitam indevidamente os acessos?','NR-01','Alta'),
 ('Incêndio e saída','Rotas de saída e equipamentos de emergência permanecem acessíveis e sem móveis ou arquivos bloqueando o caminho?','NR-23','Crítica'),
],
'ready-telecom-geral': [
 ('Planejamento do serviço','Antes da manutenção, são identificados os riscos específicos do local, como altura, eletricidade, trânsito e acesso a áreas de terceiros?','NR-01','Alta'),
 ('Trabalho em altura','Quando houver poste, torre, telhado ou estrutura elevada, são aplicados os controles previstos para trabalho em altura?','NR-35','Crítica'),
 ('Eletricidade','A proximidade de redes e instalações energizadas é verificada e controlada antes do início do serviço?','NR-10','Crítica'),
 ('Via pública','Quando o serviço ocorre em via ou área de circulação pública, a zona de trabalho é sinalizada e protegida contra tráfego e aproximação de terceiros?','NR-01 / NR-26','Alta'),
 ('Ferramentas e escadas','Ferramentas, escadas e equipamentos efetivamente usados na atividade estão íntegros e adequados ao serviço?','NR-12 / NR-35','Alta'),
 ('EPI','Os EPIs são selecionados conforme os riscos reais daquela intervenção e estão sendo utilizados corretamente?','NR-06','Alta'),
],
'ready-telecom-sala-tecnica': [
 ('Acesso à sala','O acesso à sala técnica e aos racks é controlado, sem armazenar materiais que não pertencem à operação do local?','NR-10','Alta'),
 ('Racks e painéis','Racks, quadros e equipamentos estão fixos, fechados quando necessário e sem partes energizadas acessíveis?','NR-10','Crítica'),
 ('Cabeamento','Cabos de energia e telecom estão organizados sem obstruir circulação, portas, ventilação ou acesso aos equipamentos?','NR-10 / NR-01','Alta'),
 ('Baterias e fontes','Baterias, UPS e fontes existentes estão protegidas contra curto-circuito, contato acidental e acesso indevido?','NR-10','Crítica'),
 ('Climatização','A ventilação ou climatização evita aquecimento anormal dos equipamentos e mantém as entradas/saídas de ar desobstruídas?','NR-01','Alta'),
 ('Incêndio','Materiais combustíveis indevidos não são armazenados na sala e os recursos de emergência permanecem acessíveis?','NR-23','Crítica'),
],
'ready-saude-clinica': [
 ('EPI conforme exposição','Os EPIs são utilizados de acordo com a atividade realmente executada e com o risco biológico, químico ou de respingo existente?','NR-06 / NR-32','Alta'),
 ('Equipamentos elétricos','Equipamentos elétricos de atendimento e apoio estão íntegros, com cabos e plugues sem danos ou adaptações improvisadas?','NR-10 / NR-32','Alta'),
 ('Produtos químicos','Desinfetantes, saneantes e outros produtos utilizados estão identificados e armazenados sem recipientes inadequados?','NR-26 / NR-32','Alta'),
 ('Piso e circulação','Pisos e áreas de circulação permanecem limpos, secos ou controlados contra escorregamento e sem materiais obstruindo a passagem?','NR-01 / NR-32','Alta'),
 ('Emergência','Rotas de saída e equipamentos de emergência permanecem acessíveis nas áreas de atendimento e apoio?','NR-23','Crítica'),
 ('Movimentação e postura','Atividades de atendimento, coleta ou movimentação de materiais/pacientes são organizadas para reduzir postura forçada e esforço excessivo quando aplicável?','NR-17 / NR-32','Alta'),
],
}

rel='lib/ready_checklists.dart'
src=read(rel)

def find_definition(text, template_id):
    marker = "id: '" + template_id + "'"
    pos = text.find(marker)
    if pos < 0:
        raise RuntimeError('Checklist não encontrado: ' + template_id)
    start = text.rfind('ReadyChecklistDefinition(', 0, pos)
    if start < 0:
        raise RuntimeError('Início não encontrado: ' + template_id)
    op = text.find('(', start)
    depth=0; quote=None; esc=False
    for i in range(op, len(text)):
        ch=text[i]
        if quote:
            if esc: esc=False
            elif ch == '\\': esc=True
            elif ch == quote: quote=None
            continue
        if ch in "'\"": quote=ch
        elif ch == '(': depth += 1
        elif ch == ')':
            depth -= 1
            if depth == 0:
                return start, i+1
    raise RuntimeError('Fim não encontrado: ' + template_id)

for template_id, rows in replacements.items():
    st,en=find_definition(src,template_id)
    block=src[st:en]
    matches=list(re.finditer(r"ReadyChecklistItem\s*\((.*?)\)(?=\s*,|\s*\])", block, re.S))
    if len(matches) < 6:
        raise RuntimeError(f'{template_id}: menos de 6 itens')
    # Os 20 modelos afetados tinham exatamente o mesmo bloco genérico nas seis primeiras posições.
    first_six=[m.group(0) for m in matches[:6]]
    expected=[
      'Os riscos observados no setor estão contemplados no inventário de riscos e nas medidas de prevenção aplicáveis?',
      'Os trabalhadores utilizam os EPIs definidos para os riscos existentes no setor?',
      'Máquinas e equipamentos existentes apresentam proteções, comandos e condições seguras de operação?',
      'Pisos, acessos e rotas de circulação estão desobstruídos e sem condições evidentes de queda ou colisão?',
      'Saídas, rotas e equipamentos de resposta a incêndio permanecem acessíveis e sem obstruções?',
      'Riscos, áreas restritas, equipamentos e produtos estão identificados e sinalizados quando necessário?',
    ]
    for old, phrase in zip(first_six, expected):
        if phrase not in old:
            raise RuntimeError(f'{template_id}: bloco genérico mudou antes da revisão')
    offset=0
    for m,row in zip(matches[:6],rows):
        new=item(*row)
        a=m.start()+offset; b=m.end()+offset
        block=block[:a]+new+block[b:]
        offset += len(new)-(m.end()-m.start())
    src=src[:st]+block+src[en:]

write(rel,src)

# -----------------------------------------------------------------
# 2) COMBINAÇÃO: checklist geral complementa o específico.
#    Panificação: se houver máquina específica, não repetir os dois
#    checklists gerais de máquinas/NR-12.
# -----------------------------------------------------------------
rel='lib/screens/new_inspection_screen.dart'
c=read(rel)

anchor="""  List<ChecklistItem> _removeCombinedRepetitions(
    List<ChecklistItem> source,
  ) {
"""
helper="""  static const Set<String> _panificacaoMachineSpecificIds = {
    'ready-panificacao-amassadeira',
    'ready-panificacao-cilindro',
    'ready-panificacao-modeladora',
    'ready-panificacao-fatiadora',
    'ready-panificacao-batedeira',
    'ready-panificacao-laminadora',
    'ready-panificacao-moinho-farinha-rosca',
  };

  bool get _hasSpecificPanificacaoMachine => selectedTemplates.any(
        (template) => _panificacaoMachineSpecificIds.contains(template.id),
      );

  bool _isRedundantPanificacaoGeneral(String templateId) {
    if (!_hasSpecificPanificacaoMachine) return false;
    return templateId == 'ready-panificacao-nr12-geral' ||
        templateId == 'ready-panificacao-vistoria-maquinas';
  }

"""
if helper.strip() not in c:
    if anchor not in c:
        raise RuntimeError('Marcador _removeCombinedRepetitions ausente')
    c=c.replace(anchor,helper+anchor,1)

old="""    for (final item in ordered) {
      if (item.templateId == 'template-geral-sst' &&
          coveredDomains.contains(item.category)) {
        continue;
      }
      if (seenQuestions.add(_normalizedQuestion(item.text))) {
"""
new="""    for (final item in ordered) {
      if (_isRedundantPanificacaoGeneral(item.templateId)) {
        continue;
      }
      if (item.templateId == 'template-geral-sst' &&
          coveredDomains.contains(item.category)) {
        continue;
      }
      if (seenQuestions.add(_normalizedQuestion(item.text))) {
"""
if new not in c:
    if old not in c:
        raise RuntimeError('Loop de desduplicação não encontrado')
    c=c.replace(old,new,1)

# Orientação de uso do N/A diretamente na tela de seleção/início.
hint_anchor="""          FilledButton.icon(
            onPressed: _start,
"""
hint="""          Container(
            width: double.infinity,
            margin: const EdgeInsets.only(bottom: 10),
            padding: const EdgeInsets.all(11),
            decoration: BoxDecoration(
              color: Theme.of(context).colorScheme.surfaceContainerHighest,
              borderRadius: BorderRadius.circular(12),
            ),
            child: const Text(
              'Dica de campo: quando um requisito realmente não existir ou não se aplicar ao local/equipamento vistoriado, marque N/A. Não registre Não Conforme apenas porque aquele item não existe naquele contexto.',
              style: TextStyle(fontSize: 12.5, height: 1.35),
            ),
          ),
"""
if 'Dica de campo: quando um requisito realmente não existir' not in c:
    if hint_anchor not in c:
        raise RuntimeError('Botão iniciar não encontrado')
    c=c.replace(hint_anchor,hint+hint_anchor,1)

write(rel,c)

# -----------------------------------------------------------------
# 3) Versão
# -----------------------------------------------------------------
rel='pubspec.yaml'
pub=read(rel)
version='3.30.13+200' if platform == 'windows' else '3.29.85+227'
pub,n=re.subn(r'^version:\s*[^\n]+', 'version: '+version, pub, count=1, flags=re.M)
if n != 1:
    raise RuntimeError('Versão não localizada')
write(rel,pub)

# Validações locais do patch
ready=read('lib/ready_checklists.dart')
bad="ReadyChecklistItem(category: 'Máquinas', text: 'Máquinas e equipamentos existentes apresentam proteções, comandos e condições seguras de operação?'"
for tid in replacements:
    st,en=find_definition(ready,tid)
    block=ready[st:en]
    if bad in block:
        raise RuntimeError(tid+': pergunta genérica de máquinas permaneceu')
if 'Máquinas e equipamentos existentes apresentam proteções, comandos e condições seguras de operação?' in find_definition(ready,'ready-apoio-administrativo') and False:
    pass
screen=read('lib/screens/new_inspection_screen.dart')
for marker in [
    '_panificacaoMachineSpecificIds',
    '_isRedundantPanificacaoGeneral',
    "ready-panificacao-nr12-geral",
    "ready-panificacao-vistoria-maquinas",
    'Dica de campo: quando um requisito realmente não existir',
]:
    if marker not in screen:
        raise RuntimeError('Marcador ausente: '+marker)

print('CHECKLIST_CONTENT_REVIEW_OK', platform, version, 'templates_revisados=', len(replacements))
