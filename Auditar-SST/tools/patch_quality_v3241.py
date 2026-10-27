#!/usr/bin/env python3
"""Auditar SST v3.24.1 - qualidade, validação e segurança.

Aplicar depois de patch_checklist_v324.py.
"""
from pathlib import Path
import re
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else '.')


def read(rel):
    return (root / rel).read_text(encoding='utf-8')


def write(rel, text):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


def replace_once(text, old, new, label):
    if new in text:
        return text
    if old not in text:
        raise RuntimeError(f'Marcador não encontrado: {label}')
    return text.replace(old, new, 1)


# Versão
pub = read('pubspec.yaml')
pub = re.sub(r'^version:\s*\d+\.\d+\.\d+\+\d+\s*$', 'version: 3.24.1+101', pub, flags=re.M)
if 'flutter_secure_storage:' not in pub:
    pub = pub.replace('  qr_flutter: ^4.1.0\n', '  qr_flutter: ^4.1.0\n  flutter_secure_storage: ^9.2.4\n', 1)
write('pubspec.yaml', pub)

# Serviço de validação separado da tela principal.
write('lib/services/checklist_validation_service.dart', r'''class ChecklistValidationInput {
  final String label;
  final String status;
  final String description;
  final String risk;
  final String recommendation;
  final String priority;
  final int photoCount;

  const ChecklistValidationInput({
    required this.label,
    required this.status,
    required this.description,
    required this.risk,
    required this.recommendation,
    required this.priority,
    required this.photoCount,
  });
}

class ChecklistValidationService {
  const ChecklistValidationService._();

  static String normalizePriority(String value) {
    final normalized = value.trim().toLowerCase();
    if (normalized.startsWith('cr')) return 'Crítica';
    if (normalized.startsWith('alt')) return 'Alta';
    if (normalized.startsWith('baix')) return 'Baixa';
    return 'Média';
  }

  static String? firstIssue(ChecklistValidationInput input) {
    final status = input.status.trim();
    final isNc = status == 'Não Conforme';
    final isPartial = status == 'Parcial';
    if (!isNc && !isPartial) return null;

    if (input.description.trim().isEmpty) {
      return isNc
          ? 'Descreva a não conformidade em: ${input.label}.'
          : 'Descreva o que está parcialmente atendido em: ${input.label}.';
    }

    if (!isNc) return null;

    final priority = normalizePriority(input.priority);
    if ((priority == 'Alta' || priority == 'Crítica') && input.photoCount < 1) {
      return 'Adicione pelo menos 1 foto de evidência para a NC $priority em: ${input.label}.';
    }
    if (priority == 'Crítica' && input.risk.trim().isEmpty) {
      return 'Informe o risco identificado para a NC Crítica em: ${input.label}.';
    }
    if (priority == 'Crítica' && input.recommendation.trim().isEmpty) {
      return 'Informe a recomendação técnica para a NC Crítica em: ${input.label}.';
    }
    return null;
  }
}
''')

# Armazenamento protegido do token de sessão.
write('lib/services/auth_secure_store.dart', r'''import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class AuthSecureStore {
  AuthSecureStore._();

  static const FlutterSecureStorage _storage = FlutterSecureStorage();
  static const String _sessionTokenKey = 'auditar_sst_session_token_v1';

  static Future<String> readSessionToken() async {
    try {
      return (await _storage.read(key: _sessionTokenKey) ?? '').trim();
    } catch (_) {
      return '';
    }
  }

  static Future<bool> writeSessionToken(String token) async {
    try {
      await _storage.write(key: _sessionTokenKey, value: token.trim());
      return true;
    } catch (_) {
      return false;
    }
  }

  static Future<void> deleteSessionToken() async {
    try {
      await _storage.delete(key: _sessionTokenKey);
    } catch (_) {}
  }
}
''')

# AuthService: token deixa de ficar em JSON em texto puro; migra sessão antiga automaticamente.
auth = read('lib/services/auth_service.dart')
if "import 'auth_secure_store.dart';" not in auth:
    auth = auth.replace("import 'apps_script_http.dart';\n", "import 'apps_script_http.dart';\nimport 'auth_secure_store.dart';\n", 1)

old_init = r'''  static Future<void> initialize() async {
    final file = await _authFile();
    if (!await file.exists()) return;
    try {
      final decoded = jsonDecode(await file.readAsString());
      if (decoded is! Map) return;
      final map = Map<String, dynamic>.from(decoded);
      final token = '${map['sessionToken'] ?? ''}'.trim();
      final rawUser = map['user'];
      if (token.isEmpty || rawUser is! Map) return;
      _sessionToken = token;
      _currentUser = AuditarUser.fromMap(Map<String, dynamic>.from(rawUser));
      _deviceId = '${map['deviceId'] ?? ''}'.trim();
      if (_deviceId.isEmpty) _deviceId = const Uuid().v4();
    } catch (_) {
      try {
        await file.delete();
      } catch (_) {}
      _sessionToken = '';
      _currentUser = null;
      _deviceId = '';
    }
  }
'''
new_init = r'''  static Future<void> initialize() async {
    final file = await _authFile();
    if (!await file.exists()) return;
    try {
      final decoded = jsonDecode(await file.readAsString());
      if (decoded is! Map) return;
      final map = Map<String, dynamic>.from(decoded);
      final rawUser = map['user'];
      if (rawUser is! Map) return;

      var token = await AuthSecureStore.readSessionToken();
      final legacyToken = '${map['sessionToken'] ?? ''}'.trim();
      if (token.isEmpty && legacyToken.isNotEmpty) {
        final migrated = await AuthSecureStore.writeSessionToken(legacyToken);
        if (migrated) token = legacyToken;
      }
      if (token.isEmpty) return;

      _sessionToken = token;
      _currentUser = AuditarUser.fromMap(Map<String, dynamic>.from(rawUser));
      _deviceId = '${map['deviceId'] ?? ''}'.trim();
      if (_deviceId.isEmpty) _deviceId = const Uuid().v4();

      if (legacyToken.isNotEmpty) {
        await _persist();
      }
    } catch (_) {
      _sessionToken = '';
      _currentUser = null;
      _deviceId = '';
    }
  }
'''
auth = replace_once(auth, old_init, new_init, 'AuthService.initialize seguro')

old_persist = r'''  static Future<void> _persist() async {
    final user = _currentUser;
    if (user == null || _sessionToken.isEmpty) return;
    if (_deviceId.isEmpty) _deviceId = const Uuid().v4();
    final file = await _authFile();
    await file.writeAsString(jsonEncode({
      'sessionToken': _sessionToken,
      'deviceId': _deviceId,
      'user': user.toMap(),
    }));
  }
'''
new_persist = r'''  static Future<void> _persist() async {
    final user = _currentUser;
    if (user == null || _sessionToken.isEmpty) return;
    if (_deviceId.isEmpty) _deviceId = const Uuid().v4();
    final protected = await AuthSecureStore.writeSessionToken(_sessionToken);
    if (!protected) {
      throw StateError('Não foi possível proteger a sessão neste dispositivo.');
    }
    final file = await _authFile();
    await file.writeAsString(jsonEncode({
      'deviceId': _deviceId,
      'user': user.toMap(),
    }));
  }
'''
auth = replace_once(auth, old_persist, new_persist, 'AuthService.persist seguro')

old_logout = r'''    _sessionToken = '';
    _currentUser = null;
    final file = await _authFile();
    if (await file.exists()) await file.delete();
    await AppDatabase.deactivateUser();
'''
new_logout = r'''    _sessionToken = '';
    _currentUser = null;
    await AuthSecureStore.deleteSessionToken();
    final file = await _authFile();
    if (await file.exists()) await file.delete();
    await AppDatabase.deactivateUser();
'''
auth = replace_once(auth, old_logout, new_logout, 'logout apaga token protegido')
write('lib/services/auth_service.dart', auth)

# Checklist: validações fortes e confirmação para marcação em massa.
checklist = read('lib/screens/checklist_screen.dart')
if "import '../services/checklist_validation_service.dart';" not in checklist:
    checklist = checklist.replace("import '../services/ai_assistant_service.dart';\n", "import '../services/ai_assistant_service.dart';\nimport '../services/checklist_validation_service.dart';\n", 1)

old_mark_all = r'''  void _markAllConforme() {
    setState(() {
      for (final item in widget.checklistItems) {
        statuses[item.id] = 'Conforme';
      }
    });

    _scheduleDraftSave();

    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text(
          'Todos os itens foram marcados como Conforme. '
          'Agora altere somente os itens que apresentarem problema.',
        ),
      ),
    );
  }
'''
new_mark_all = r'''  Future<void> _markAllConforme() async {
    final issuesAlreadyMarked = statuses.values
        .where((value) => value == 'Não Conforme' || value == 'Parcial')
        .length;
    final confirmed = await showDialog<bool>(
          context: context,
          builder: (dialogContext) => AlertDialog(
            title: const Text('Marcar todos como Conforme?'),
            content: Text(
              issuesAlreadyMarked > 0
                  ? 'Há $issuesAlreadyMarked item(ns) já marcado(s) como NC ou Parcial. '
                      'Ao confirmar, eles também serão alterados para Conforme. '
                      'Use esta opção somente depois de verificar os itens no local.'
                  : 'Todos os itens do checklist serão marcados como Conforme. '
                      'Confirme somente se eles realmente foram verificados no local.',
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.pop(dialogContext, false),
                child: const Text('Cancelar'),
              ),
              FilledButton(
                onPressed: () => Navigator.pop(dialogContext, true),
                child: const Text('Sim, marcar todos'),
              ),
            ],
          ),
        ) ??
        false;
    if (!confirmed || !mounted) return;

    setState(() {
      for (final item in widget.checklistItems) {
        statuses[item.id] = 'Conforme';
      }
    });

    _scheduleDraftSave();

    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text(
          'Todos os itens foram marcados como Conforme. '
          'Altere os itens que apresentarem problema.',
        ),
      ),
    );
  }
'''
checklist = replace_once(checklist, old_mark_all, new_mark_all, 'confirmação marcar todos conforme')

old_validate = r'''  Future<bool> _validate() async {
    if (statuses.length != widget.checklistItems.length) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Responda todos os itens do checklist.'),
        ),
      );
      return false;
    }

    for (final item in widget.checklistItems) {
      final status = statuses[item.id];
      if (status == 'Não Conforme' || status == 'Parcial') {
        if (observations[item.id]!.text.trim().isEmpty) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text(
                status == 'Não Conforme'
                    ? 'Descreva a não conformidade em: ${item.category.isEmpty ? item.text : item.category}.'
                    : 'Descreva o que está parcialmente atendido em: ${item.category.isEmpty ? item.text : item.category}.',
              ),
            ),
          );
          return false;
        }
      }
    }

    return true;
  }
'''
new_validate = r'''  Future<void> _showValidationError(String message) async {
    if (!mounted) return;
    await showDialog<void>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('Complete o registro antes de finalizar'),
        content: Text(message),
        actions: [
          FilledButton(
            onPressed: () => Navigator.pop(dialogContext),
            child: const Text('Voltar ao checklist'),
          ),
        ],
      ),
    );
  }

  Future<bool> _validate() async {
    if (statuses.length != widget.checklistItems.length) {
      await _showValidationError('Responda todos os itens do checklist.');
      return false;
    }

    for (final item in widget.checklistItems) {
      final label = item.category.isEmpty ? item.text : item.category;
      final validPhotos = (photos[item.id] ?? const <String>[])
          .where((path) => File(path).existsSync())
          .length;
      final error = ChecklistValidationService.firstIssue(
        ChecklistValidationInput(
          label: label,
          status: statuses[item.id] ?? '',
          description: observations[item.id]!.text,
          risk: risks[item.id]!.text,
          recommendation: recommendations[item.id]!.text,
          priority: priorities[item.id] ?? item.priority,
          photoCount: validPhotos,
        ),
      );
      if (error != null) {
        await _showValidationError(error);
        return false;
      }

      for (final occurrence in extraOccurrences[item.id] ?? const <_ExtraNcOccurrence>[]) {
        final occurrenceError = ChecklistValidationService.firstIssue(
          ChecklistValidationInput(
            label: '$label • ocorrência adicional',
            status: 'Não Conforme',
            description: occurrence.description,
            risk: occurrence.risk,
            recommendation: occurrence.recommendation,
            priority: occurrence.priority,
            photoCount: validPhotos,
          ),
        );
        if (occurrenceError != null) {
          await _showValidationError(occurrenceError);
          return false;
        }
      }
    }

    return true;
  }
'''
checklist = replace_once(checklist, old_validate, new_validate, 'validação forte de NC')
write('lib/screens/checklist_screen.dart', checklist)

# Testes unitários reais para as regras de campo.
write('test/checklist_validation_service_test.dart', r'''import 'package:flutter_test/flutter_test.dart';
import 'package:auditar_sst/services/checklist_validation_service.dart';

ChecklistValidationInput input({
  String status = 'Não Conforme',
  String description = 'Proteção ausente.',
  String risk = 'Contato com parte móvel.',
  String recommendation = 'Instalar proteção fixa.',
  String priority = 'Média',
  int photoCount = 0,
}) {
  return ChecklistValidationInput(
    label: 'Máquinas',
    status: status,
    description: description,
    risk: risk,
    recommendation: recommendation,
    priority: priority,
    photoCount: photoCount,
  );
}

void main() {
  group('ChecklistValidationService', () {
    test('conforme não exige campos adicionais', () {
      expect(
        ChecklistValidationService.firstIssue(
          input(status: 'Conforme', description: '', risk: '', recommendation: ''),
        ),
        isNull,
      );
    });

    test('parcial exige descrição', () {
      expect(
        ChecklistValidationService.firstIssue(
          input(status: 'Parcial', description: ''),
        ),
        contains('parcialmente atendido'),
      );
    });

    test('parcial não exige foto', () {
      expect(
        ChecklistValidationService.firstIssue(
          input(status: 'Parcial', photoCount: 0),
        ),
        isNull,
      );
    });

    test('NC média exige descrição, mas não obriga foto', () {
      expect(ChecklistValidationService.firstIssue(input(priority: 'Média')), isNull);
    });

    test('NC alta exige foto', () {
      expect(
        ChecklistValidationService.firstIssue(input(priority: 'Alta', photoCount: 0)),
        contains('foto de evidência'),
      );
      expect(
        ChecklistValidationService.firstIssue(input(priority: 'Alta', photoCount: 1)),
        isNull,
      );
    });

    test('NC crítica exige foto', () {
      expect(
        ChecklistValidationService.firstIssue(input(priority: 'Crítica', photoCount: 0)),
        contains('foto de evidência'),
      );
    });

    test('NC crítica exige risco', () {
      expect(
        ChecklistValidationService.firstIssue(
          input(priority: 'Crítica', photoCount: 1, risk: ''),
        ),
        contains('risco identificado'),
      );
    });

    test('NC crítica exige recomendação técnica', () {
      expect(
        ChecklistValidationService.firstIssue(
          input(priority: 'Crítica', photoCount: 1, recommendation: ''),
        ),
        contains('recomendação técnica'),
      );
    });

    test('NC crítica completa é aceita', () {
      expect(
        ChecklistValidationService.firstIssue(
          input(priority: 'Crítica', photoCount: 2),
        ),
        isNull,
      );
    });

    test('normaliza prioridade sem depender de maiúsculas', () {
      expect(ChecklistValidationService.normalizePriority('crítica'), 'Crítica');
      expect(ChecklistValidationService.normalizePriority('ALTA'), 'Alta');
    });
  });
}
''')

# Apps Script: senha com KDF iterativa + tokens armazenados em hash, com migração compatível.
multi = read('painel_web_google_apps_script/MultiUser.gs')
if 'const AUTH_PASSWORD_ROUNDS' not in multi:
    multi = multi.replace(
        "const AUTH_SESSION_DAYS = 180;\n",
        "const AUTH_SESSION_DAYS = 180;\nconst AUTH_PASSWORD_ROUNDS = 6000;\n",
        1,
    )
old_hash = r'''function authPasswordHash_(password, salt) {
  return authHex_(Utilities.computeDigest(
    Utilities.DigestAlgorithm.SHA_256,
    String(salt || '') + '|' + String(password || ''),
    Utilities.Charset.UTF_8
  ));
}
'''
new_hash = r'''function authPasswordHashLegacy_(password, salt) {
  return authHex_(Utilities.computeDigest(
    Utilities.DigestAlgorithm.SHA_256,
    String(salt || '') + '|' + String(password || ''),
    Utilities.Charset.UTF_8
  ));
}

function authPasswordDigest_(password, salt, rounds) {
  const cleanSalt = String(salt || '');
  const totalRounds = Math.max(1, Math.min(Number(rounds) || AUTH_PASSWORD_ROUNDS, 20000));
  let digest = Utilities.computeDigest(
    Utilities.DigestAlgorithm.SHA_256,
    cleanSalt + '|' + String(password || ''),
    Utilities.Charset.UTF_8
  );
  for (let i = 1; i < totalRounds; i++) {
    digest = Utilities.computeDigest(
      Utilities.DigestAlgorithm.SHA_256,
      authHex_(digest) + '|' + cleanSalt,
      Utilities.Charset.UTF_8
    );
  }
  return authHex_(digest);
}

function authPasswordHash_(password, salt) {
  return 'v2$' + AUTH_PASSWORD_ROUNDS + '$' +
    authPasswordDigest_(password, salt, AUTH_PASSWORD_ROUNDS);
}

function authPasswordMatches_(password, salt, storedHash) {
  const stored = String(storedHash || '');
  if (stored.indexOf('v2$') === 0) {
    const parts = stored.split('$');
    const rounds = Number(parts[1]) || AUTH_PASSWORD_ROUNDS;
    const expected = String(parts[2] || '');
    return expected === authPasswordDigest_(password, salt, rounds);
  }
  return stored === authPasswordHashLegacy_(password, salt);
}

function authTokenHash_(token) {
  return 'sha256$' + authHex_(Utilities.computeDigest(
    Utilities.DigestAlgorithm.SHA_256,
    String(token || ''),
    Utilities.Charset.UTF_8
  ));
}

function authTokenMatches_(candidateToken, storedToken) {
  const candidate = String(candidateToken || '').trim();
  const stored = String(storedToken || '').trim();
  if (!candidate || !stored) return false;
  // Compatibilidade com sessões v3.23/v3.24 já gravadas em texto puro.
  return stored === candidate || stored === authTokenHash_(candidate);
}
'''
multi = replace_once(multi, old_hash, new_hash, 'KDF de senha e hash de token')

old_login = r'''  const user = users.find(item => item.email === email);
  if (!user || !user.active || authPasswordHash_(password, user.passwordSalt) !== user.passwordHash) {
    return {ok: false, code: 'LOGIN_INVALID', message: 'E-mail ou senha inválidos.'};
  }

  const now = new Date().toISOString();
  getSheet_(AUTH_USERS_SHEET).getRange(user.rowNumber, 12).setValue(now);
  user.lastLoginAt = now;
'''
new_login = r'''  const user = users.find(item => item.email === email);
  if (!user || !user.active || !authPasswordMatches_(password, user.passwordSalt, user.passwordHash)) {
    return {ok: false, code: 'LOGIN_INVALID', message: 'E-mail ou senha inválidos.'};
  }

  const userSheet = getSheet_(AUTH_USERS_SHEET);
  if (String(user.passwordHash || '').indexOf('v2$') !== 0) {
    const upgradedSalt =
      Utilities.getUuid().replace(/-/g, '') + Utilities.getUuid().replace(/-/g, '');
    const upgradedHash = authPasswordHash_(password, upgradedSalt);
    userSheet.getRange(user.rowNumber, 4, 1, 2).setValues([[upgradedHash, upgradedSalt]]);
    user.passwordHash = upgradedHash;
    user.passwordSalt = upgradedSalt;
  }

  const now = new Date().toISOString();
  userSheet.getRange(user.rowNumber, 12).setValue(now);
  user.lastLoginAt = now;
'''
multi = replace_once(multi, old_login, new_login, 'migração automática de hash no login')

multi = replace_once(
    multi,
    "  getSheet_(AUTH_SESSIONS_SHEET).appendRow([\n    token,\n",
    "  getSheet_(AUTH_SESSIONS_SHEET).appendRow([\n    authTokenHash_(token),\n",
    'armazenamento de sessão em hash',
)
multi = multi.replace(
    "if (String(rows[i][0] || '') === clean) {",
    "if (authTokenMatches_(clean, rows[i][0])) {",
)
multi = multi.replace(
    "if (String(rows[i][0] || '') === token) {",
    "if (authTokenMatches_(token, rows[i][0])) {",
)
write('painel_web_google_apps_script/MultiUser.gs', multi)

# Nota de versão / checklist de teste de campo.
write('MUDANCAS_V3_24_1_QUALIDADE_SEGURANCA.txt', r'''AUDITAR SST v3.24.1 — QUALIDADE E SEGURANÇA

Checklist/vistoria
- NC Alta: exige descrição e pelo menos 1 foto antes de finalizar.
- NC Crítica: exige descrição, foto, risco identificado e recomendação técnica.
- Ocorrências adicionais seguem as mesmas regras de prioridade.
- "Marcar todos como Conforme" agora pede confirmação e alerta quando já existem NCs/Parciais.
- Validação foi extraída para serviço separado, reduzindo regra de negócio dentro da tela.

Testes
- Adicionados testes automatizados das regras de validação do checklist.
- Builds Android e Windows passam a exigir flutter test; ausência de testes não é mais aceita silenciosamente.

Segurança
- Token de sessão do app passa a usar armazenamento seguro do sistema operacional.
- Sessões antigas em JSON são migradas automaticamente e o token deixa de ser salvo no arquivo comum.
- Novas senhas no Apps Script usam KDF iterativa; hashes antigos são atualizados no próximo login válido.
- Novas sessões são armazenadas na planilha apenas como hash do token; sessões antigas continuam válidas durante a migração.
- AUDITAR_SYNC_KEY permanece temporariamente para compatibilidade e primeiro bootstrap. Não remover nesta versão.

VERSÃO: 3.24.1+101
''')

# Sanidades para falhar cedo antes do Flutter.
assert "version: 3.24.1+101" in read('pubspec.yaml')
assert "flutter_secure_storage:" in read('pubspec.yaml')
assert "ChecklistValidationService.firstIssue" in read('lib/screens/checklist_screen.dart')
assert "AuthSecureStore.writeSessionToken" in read('lib/services/auth_service.dart')
assert "AUTH_PASSWORD_ROUNDS = 6000" in read('painel_web_google_apps_script/MultiUser.gs')
assert "authTokenHash_(token)" in read('painel_web_google_apps_script/MultiUser.gs')
assert (root / 'test/checklist_validation_service_test.dart').exists()
print('Auditar SST v3.24.1 aplicado com sucesso.')
