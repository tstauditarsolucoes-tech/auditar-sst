#!/usr/bin/env python3
"""Correção pontual: central da IA consistente com login; cadastro e demais módulos intactos."""
from pathlib import Path
import re,sys

root=Path(sys.argv[1])
platform=(sys.argv[2] if len(sys.argv)>2 else 'android').lower()
rel='lib/services/ai_assistant_service.dart'
p=root/rel
s=p.read_text(encoding='utf-8')
old="""    final endpoint = savedEndpoint.isNotEmpty
        ? savedEndpoint
        : WebServiceConfig.endpoint.trim();
    final syncKey = savedSyncKey.isNotEmpty
        ? savedSyncKey
        : WebServiceConfig.syncKey.trim();
"""
new="""    // Usa a mesma Central e chave do login. Uma URL de publicacao antiga
    // guardada no aparelho nao pode desviar somente a IA para outro endpoint.
    // Se a compilacao nao contiver configuracao embutida, o cadastro local
    // continua funcionando como fallback, sem alterar nenhum valor salvo.
    final embeddedEndpoint = WebServiceConfig.endpoint.trim();
    final embeddedSyncKey = WebServiceConfig.syncKey.trim();
    final endpoint =
        embeddedEndpoint.isNotEmpty ? embeddedEndpoint : savedEndpoint;
    final syncKey =
        embeddedSyncKey.isNotEmpty ? embeddedSyncKey : savedSyncKey;
"""
if s.count(old)!=1: raise RuntimeError('Selecao da URL/chave da IA diferente da esperada')
s=s.replace(old,new,1)
old2="""        if (response.statusCode < 200 || response.statusCode >= 300) {
          return AiAssistantReply(
            success: false,
            message: transientHttp.contains(response.statusCode)
"""
new2="""        // A resposta 302 e um redirecionamento esperado do ContentService,
        // que o transporte normalmente segue ate o JSON. Se o aparelho
        // devolveu o 302 bruto, nao repetir o POST da foto: a Central pode
        // ter executado a analise. Preserva os registros e informa a etapa.
        if (response.statusCode == 302) {
          return const AiAssistantReply(
            success: false,
            message:
                'O Google nao concluiu o redirecionamento da resposta da IA. '
                'A foto e o registro continuam salvos; tente analisar novamente '
                'quando a conexao estiver estavel.',
          );
        }
        if (response.statusCode < 200 || response.statusCode >= 300) {
          return AiAssistantReply(
            success: false,
            message: transientHttp.contains(response.statusCode)
"""
if s.count(old2)!=1: raise RuntimeError('Tratamento HTTP da IA nao localizado')
s=s.replace(old2,new2,1)
p.write_text(s,encoding='utf-8',newline='\n')
pubp=root/'pubspec.yaml'
pub=pubp.read_text(encoding='utf-8')
version='3.30.22+209' if platform=='windows' else '3.29.95+237'
pub,n=re.subn(r'(?m)^version:\s*[^\r\n]+$',f'version: {version}',pub,count=1)
if n!=1: raise RuntimeError('Versao nao localizada')
pubp.write_text(pub,encoding='utf-8',newline='\n')
check=p.read_text(encoding='utf-8')
assert check.count('final embeddedEndpoint = WebServiceConfig.endpoint.trim();')==1
assert 'embeddedEndpoint.isNotEmpty ? embeddedEndpoint : savedEndpoint' in check
assert "if (response.statusCode == 302)" in check
assert "final maxAttempts = photoAnalysis ? 1 : 2;" in check
assert f'version: {version}' in pubp.read_text(encoding='utf-8')
print('WORKERS_AI_CENTRAL_ENDPOINT_OK',platform,version)
