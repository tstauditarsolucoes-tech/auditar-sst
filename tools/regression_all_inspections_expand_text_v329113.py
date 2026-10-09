#!/usr/bin/env python3
from pathlib import Path
import sys
root=Path(sys.argv[1]); version=sys.argv[2]
pub=(root/'pubspec.yaml').read_text(encoding='utf-8')
widget=(root/'lib/widgets/expandable_text_field.dart').read_text(encoding='utf-8')
assert 'version: '+version in pub
assert "tooltip: 'Expandir texto'" in widget
assert "label: const Text('Voltar para a vistoria')" in widget
checks={
 'lib/screens/checklist_screen.dart':['O que você identificou?','O que foi encontrado *','Correção recomendada'],
 'lib/screens/express_round_screen.dart':['Descrição sugerida','O que você encontrou?','Recomendação / ação corretiva'],
 'lib/screens/safety_observations_screen.dart':['Descrição *','Risco identificado','Recomendação / medida corretiva','Observações adicionais'],
 'lib/screens/sst_record_form_screen.dart':['Descrição do ocorrido','Riscos identificados','Medidas de controle','Conteúdo abordado / orientações *'],
}
for rel,labels in checks.items():
    body=(root/rel).read_text(encoding='utf-8')
    assert 'ExpandableTextField(' in body, rel
    for label in labels: assert label in body, (rel,label)
print('EXPANDABLE_TEXT_ALL_INSPECTION_MODES_OK',version)
