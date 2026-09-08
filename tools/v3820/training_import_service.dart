import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'package:archive/archive.dart';
import 'package:file_picker/file_picker.dart';
import 'package:path/path.dart' as p;
import 'package:path_provider/path_provider.dart';
import 'package:uuid/uuid.dart';
import 'package:xml/xml.dart';

import '../database.dart';
import '../models.dart';
import 'apps_script_http.dart';
import 'auth_service.dart';

class TrainingImportParticipant {
  final String name;
  final String cpf;
  final String role;
  final Worker? worker;
  final bool duplicate;

  const TrainingImportParticipant({
    required this.name,
    required this.cpf,
    required this.role,
    required this.worker,
    required this.duplicate,
  });

  bool get matched => worker != null;
}

class TrainingImportPreview {
  final String fileName;
  final String extension;
  final Uint8List sourceBytes;
  final String code;
  final String title;
  final String workload;
  final String instructor;
  final DateTime? trainingDate;
  final DateTime? expiryDate;
  final String confidence;
  final List<String> warnings;
  final List<TrainingImportParticipant> participants;

  const TrainingImportPreview({
    required this.fileName,
    required this.extension,
    required this.sourceBytes,
    required this.code,
    required this.title,
    required this.workload,
    required this.instructor,
    required this.trainingDate,
    required this.expiryDate,
    required this.confidence,
    required this.warnings,
    required this.participants,
  });

  int get matchedCount => participants.where((item) => item.matched).length;
  int get unmatchedCount => participants.where((item) => !item.matched).length;
  int get duplicateCount => participants.where((item) => item.duplicate).length;
  int get readyCount =>
      participants.where((item) => item.matched && !item.duplicate).length;
}

class TrainingImportSaveResult {
  final int savedCount;
  final String evidencePath;

  const TrainingImportSaveResult({
    required this.savedCount,
    required this.evidencePath,
  });
}

class TrainingImportException implements Exception {
  final String message;

  const TrainingImportException(this.message);

  @override
  String toString() => message;
}

class TrainingImportService {
  static Future<TrainingImportPreview?> pickAndAnalyze({
    required Company company,
    required List<Worker> workers,
    required List<TrainingControl> existingTrainings,
  }) async {
    final picked = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: const ['pdf', 'xlsx', 'csv'],
      withData: true,
    );
    if (picked == null || picked.files.isEmpty) return null;

    final selected = picked.files.single;
    Uint8List? bytes = selected.bytes;
    if (bytes == null && selected.path != null) {
      bytes = await File(selected.path!).readAsBytes();
    }
    if (bytes == null || bytes.isEmpty) {
      throw const TrainingImportException(
        'Não foi possível abrir o arquivo selecionado.',
      );
    }
    if (bytes.length > 12000000) {
      throw const TrainingImportException(
        'O arquivo ultrapassa 12 MB. Use um PDF ou planilha menor.',
      );
    }

    final extension = p.extension(selected.name).toLowerCase().replaceFirst('.', '');
    if (!const {'pdf', 'xlsx', 'csv'}.contains(extension)) {
      throw const TrainingImportException(
        'Formato não suportado. Use PDF, Excel (.xlsx) ou CSV.',
      );
    }

    String? extractedText;
    if (extension == 'csv') {
      extractedText = _decodeCsv(bytes);
    } else if (extension == 'xlsx') {
      extractedText = _extractXlsx(bytes);
    }

    final result = await _analyzeDocument(
      company: company,
      extension: extension,
      bytes: bytes,
      extractedText: extractedText,
    );

    final code = '${result['code'] ?? ''}'.trim();
    final title = '${result['title'] ?? ''}'.trim();
    final trainingDate = _parseDate('${result['trainingDate'] ?? ''}');
    final expiryDate = _parseDate('${result['expiryDate'] ?? ''}');
    final workload = '${result['workload'] ?? ''}'.trim();
    final instructor = '${result['instructor'] ?? ''}'.trim();
    final confidence = '${result['confidence'] ?? ''}'.trim();
    final warnings = (result['warnings'] is List)
        ? (result['warnings'] as List)
            .map((item) => '$item'.trim())
            .where((item) => item.isNotEmpty)
            .toList()
        : <String>[];

    final rawParticipants = result['participants'];
    if (rawParticipants is! List || rawParticipants.isEmpty) {
      throw const TrainingImportException(
        'A IA não encontrou participantes no registro de treinamento.',
      );
    }

    final workersByCpf = <String, Worker>{};
    final workersByName = <String, List<Worker>>{};
    for (final worker in workers.where((item) => item.active)) {
      final cpf = _digits(worker.cpf);
      if (cpf.length == 11) workersByCpf[cpf] = worker;
      workersByName.putIfAbsent(_normalize(worker.name), () => <Worker>[]).add(worker);
    }

    final participants = <TrainingImportParticipant>[];
    final seenWorkers = <String>{};
    for (final raw in rawParticipants) {
      if (raw is! Map) continue;
      final name = '${raw['name'] ?? ''}'.trim();
      final cpf = _digits('${raw['cpf'] ?? ''}');
      final role = '${raw['role'] ?? ''}'.trim();
      if (name.isEmpty && cpf.isEmpty) continue;

      Worker? matched;
      if (cpf.length == 11) matched = workersByCpf[cpf];
      if (matched == null && name.isNotEmpty) {
        final sameName = workersByName[_normalize(name)] ?? const <Worker>[];
        if (sameName.length == 1) {
          matched = sameName.first;
        } else if (sameName.length > 1 && role.isNotEmpty) {
          final sameRole = sameName
              .where((worker) => _normalize(worker.role) == _normalize(role))
              .toList();
          if (sameRole.length == 1) matched = sameRole.first;
        }
      }

      if (matched != null && !seenWorkers.add(matched.id)) continue;
      final duplicate = matched == null
          ? false
          : _alreadyRegistered(
              existingTrainings,
              matched.id,
              code,
              title,
              trainingDate,
            );
      participants.add(
        TrainingImportParticipant(
          name: name.isEmpty ? (matched?.name ?? '') : name,
          cpf: cpf,
          role: role,
          worker: matched,
          duplicate: duplicate,
        ),
      );
    }

    if (participants.isEmpty) {
      throw const TrainingImportException(
        'Nenhum participante utilizável foi encontrado no arquivo.',
      );
    }

    return TrainingImportPreview(
      fileName: selected.name,
      extension: extension,
      sourceBytes: bytes,
      code: code,
      title: title,
      workload: workload,
      instructor: instructor,
      trainingDate: trainingDate,
      expiryDate: expiryDate,
      confidence: confidence,
      warnings: warnings,
      participants: participants,
    );
  }

  static Future<TrainingImportSaveResult> save({
    required String companyId,
    required TrainingImportPreview preview,
    required Set<String> workerIds,
    required String code,
    required String title,
    required DateTime trainingDate,
    DateTime? expiryDate,
    required String workload,
    required String instructor,
  }) async {
    if (workerIds.isEmpty) {
      throw const TrainingImportException(
        'Selecione pelo menos um participante para registrar.',
      );
    }
    if (title.trim().isEmpty) {
      throw const TrainingImportException('Informe o nome do treinamento.');
    }
    if (expiryDate != null && expiryDate.isBefore(trainingDate)) {
      throw const TrainingImportException(
        'O vencimento não pode ser anterior ao treinamento.',
      );
    }

    final evidencePath = await _saveEvidence(companyId, preview);
    final requirements = await AppDatabase.instance.getTrainingRequirements(
      companyId: companyId,
    );
    final workers = await AppDatabase.instance.getWorkers(companyId: companyId);
    final workerById = {for (final worker in workers) worker.id: worker};
    final existing = await AppDatabase.instance.getTrainingControls(
      companyId: companyId,
    );

    final records = <TrainingControl>[];
    for (final workerId in workerIds) {
      final worker = workerById[workerId];
      if (worker == null) continue;
      if (_alreadyRegistered(existing, workerId, code, title, trainingDate)) {
        continue;
      }
      final effectiveExpiry = expiryDate ??
          _expiryFromRequirement(
            requirements,
            worker,
            code,
            title,
            trainingDate,
          );
      final notes = <String>[
        if (instructor.trim().isNotEmpty) 'Instrutor: ${instructor.trim()}',
        if (workload.trim().isNotEmpty) 'Carga horária: ${workload.trim()}',
        'Importado de: ${preview.fileName}',
        'Registro conferido antes da importação.',
      ].join('\n');
      records.add(
        TrainingControl(
          id: const Uuid().v4(),
          workerId: workerId,
          code: code.trim(),
          title: title.trim(),
          trainingDate: trainingDate,
          expiryDate: effectiveExpiry,
          certificatePath: evidencePath,
          notes: notes,
        ),
      );
    }

    if (records.isEmpty) {
      throw const TrainingImportException(
        'Nenhum registro novo foi criado. Os participantes selecionados já podem estar registrados.',
      );
    }
    await AppDatabase.instance.upsertTrainingControlsBatch(records);
    return TrainingImportSaveResult(
      savedCount: records.length,
      evidencePath: evidencePath,
    );
  }

  static Future<Map<String, dynamic>> _analyzeDocument({
    required Company company,
    required String extension,
    required Uint8List bytes,
    required String? extractedText,
  }) async {
    final endpoint = (await AppDatabase.instance.getSetting(
      'management_panel_endpoint',
      fallback: '',
    ))
        .trim();
    final syncKey = (await AppDatabase.instance.getSetting(
      'management_panel_sync_key',
      fallback: '',
    ))
        .trim();
    if (endpoint.isEmpty || syncKey.isEmpty) {
      throw const TrainingImportException(
        'Configure primeiro a publicação web em Configurações para usar a importação com IA.',
      );
    }

    final payload = <String, Object?>{
      'mode': 'training_document_import',
      'companyName': company.name,
      'fileType': extension,
    };
    if (extension == 'pdf') {
      payload['document'] =
          'data:application/pdf;base64,${base64Encode(bytes)}';
    } else {
      final text = (extractedText ?? '').trim();
      if (text.isEmpty) {
        throw const TrainingImportException(
          'Não consegui extrair os dados da planilha selecionada.',
        );
      }
      payload['extractedText'] = text.length > 180000
          ? text.substring(0, 180000)
          : text;
    }

    try {
      final response = await AppsScriptHttp.postJson(
        Uri.parse(endpoint),
        {
          'action': 'ai_assistant',
          'syncKey': syncKey,
          'authToken': AuthService.sessionToken,
          'payload': payload,
        },
        timeout: const Duration(seconds: 180),
      );
      if (response.statusCode < 200 || response.statusCode >= 300) {
        throw TrainingImportException(
          'O serviço respondeu com erro ${response.statusCode}.',
        );
      }
      final decoded = jsonDecode(utf8.decode(response.bodyBytes));
      if (decoded is! Map || decoded['ok'] != true) {
        throw TrainingImportException(
          decoded is Map
              ? '${decoded['message'] ?? 'A análise do treinamento não foi concluída.'}'
              : 'A análise retornou uma resposta inválida.',
        );
      }
      final result = decoded['result'];
      if (result is! Map) {
        throw const TrainingImportException(
          'A IA retornou dados de treinamento inválidos.',
        );
      }
      return Map<String, dynamic>.from(result);
    } on SocketException {
      throw const TrainingImportException(
        'A importação com IA precisa de internet. Tente novamente quando estiver conectado.',
      );
    } on FormatException {
      throw const TrainingImportException(
        'O serviço retornou uma resposta inválida.',
      );
    } on TrainingImportException {
      rethrow;
    } catch (error) {
      throw TrainingImportException(
        'Não foi possível analisar o registro de treinamento: $error',
      );
    }
  }

  static Future<String> _saveEvidence(
    String companyId,
    TrainingImportPreview preview,
  ) async {
    final root = await getApplicationDocumentsDirectory();
    final directory = Directory(
      p.join(root.path, 'training_evidence', _safeName(companyId)),
    );
    await directory.create(recursive: true);
    final stamp = DateTime.now().millisecondsSinceEpoch;
    final base = _safeName(p.basenameWithoutExtension(preview.fileName));
    final extension = preview.extension.isEmpty ? 'bin' : preview.extension;
    final file = File(p.join(directory.path, '${stamp}_$base.$extension'));
    await file.writeAsBytes(preview.sourceBytes, flush: true);
    return file.path;
  }

  static bool _alreadyRegistered(
    List<TrainingControl> existing,
    String workerId,
    String code,
    String title,
    DateTime? trainingDate,
  ) {
    if (trainingDate == null) return false;
    final target = AppDatabase.normalizeTrainingKey(
      code.trim().isNotEmpty ? code : title,
    );
    final day = DateTime(trainingDate.year, trainingDate.month, trainingDate.day);
    return existing.any((item) {
      if (item.workerId != workerId || item.trainingDate == null) return false;
      final itemKey = AppDatabase.normalizeTrainingKey(
        item.code.trim().isNotEmpty ? item.code : item.title,
      );
      final itemDay = DateTime(
        item.trainingDate!.year,
        item.trainingDate!.month,
        item.trainingDate!.day,
      );
      return itemKey == target && itemDay == day;
    });
  }

  static DateTime? _expiryFromRequirement(
    List<TrainingRequirement> requirements,
    Worker worker,
    String code,
    String title,
    DateTime trainingDate,
  ) {
    final role = AppDatabase.normalizeRoleKey(worker.role);
    final codeKey = AppDatabase.normalizeTrainingKey(code);
    final titleKey = AppDatabase.normalizeTrainingKey(title);
    for (final requirement in requirements.where((item) => item.active)) {
      if (AppDatabase.normalizeRoleKey(requirement.role) != role) continue;
      final requiredCode = AppDatabase.normalizeTrainingKey(requirement.code);
      final requiredTitle = AppDatabase.normalizeTrainingKey(requirement.title);
      final matches = (codeKey.isNotEmpty && codeKey == requiredCode) ||
          (titleKey.isNotEmpty && titleKey == requiredTitle);
      if (!matches || requirement.validityMonths <= 0) continue;
      return _addMonths(trainingDate, requirement.validityMonths);
    }
    return null;
  }

  static DateTime _addMonths(DateTime date, int months) {
    final target = DateTime(date.year, date.month + months, 1);
    final lastDay = DateTime(target.year, target.month + 1, 0).day;
    final day = date.day > lastDay ? lastDay : date.day;
    return DateTime(target.year, target.month, day);
  }

  static DateTime? _parseDate(String raw) {
    final value = raw.trim();
    if (value.isEmpty) return null;
    final iso = DateTime.tryParse(value);
    if (iso != null) return DateTime(iso.year, iso.month, iso.day);
    final match = RegExp(r'^(\d{1,2})[\/-](\d{1,2})[\/-](\d{2,4})$').firstMatch(value);
    if (match == null) return null;
    var year = int.parse(match.group(3)!);
    if (year < 100) year += 2000;
    final date = DateTime(year, int.parse(match.group(2)!), int.parse(match.group(1)!));
    if (date.year != year) return null;
    return date;
  }

  static String _decodeCsv(Uint8List bytes) {
    final utf = utf8.decode(bytes, allowMalformed: true);
    final replacements = RegExp('�').allMatches(utf).length;
    if (replacements <= 2) return utf;
    return latin1.decode(bytes, allowInvalid: true);
  }

  static String _extractXlsx(Uint8List bytes) {
    try {
      final archive = ZipDecoder().decodeBytes(bytes);
      final sharedFile = archive.findFile('xl/sharedStrings.xml');
      final shared = <String>[];
      if (sharedFile != null) {
        final xmlBytes = sharedFile.readBytes();
        if (xmlBytes != null) {
          final document = XmlDocument.parse(utf8.decode(xmlBytes));
          for (final item in document.findAllElements('si')) {
            shared.add(item.findAllElements('t').map((e) => e.innerText).join());
          }
        }
      }

      final sheets = archive.files
          .where((file) =>
              file.isFile &&
              RegExp(r'^xl/worksheets/sheet\d+\.xml$').hasMatch(file.name))
          .toList()
        ..sort((a, b) => a.name.compareTo(b.name));
      if (sheets.isEmpty) {
        throw const TrainingImportException(
          'A planilha Excel não possui uma aba de dados legível.',
        );
      }

      final output = StringBuffer();
      var totalRows = 0;
      for (final sheet in sheets.take(5)) {
        final sheetBytes = sheet.readBytes();
        if (sheetBytes == null) continue;
        final document = XmlDocument.parse(utf8.decode(sheetBytes));
        final rows = <List<String>>[];
        for (final rowElement in document.findAllElements('row')) {
          if (totalRows >= 5000) break;
          final cells = <int, String>{};
          var maxColumn = -1;
          for (final cell in rowElement.findElements('c')) {
            final reference = cell.getAttribute('r') ?? '';
            final column = _columnIndex(reference);
            if (column < 0 || column > 80) continue;
            final type = cell.getAttribute('t') ?? '';
            String value = '';
            if (type == 'inlineStr') {
              value = cell.findAllElements('t').map((e) => e.innerText).join();
            } else {
              final valueElement = cell.findElements('v').firstOrNull;
              final raw = valueElement?.innerText ?? '';
              if (type == 's') {
                final index = int.tryParse(raw);
                value = index != null && index >= 0 && index < shared.length
                    ? shared[index]
                    : raw;
              } else {
                value = raw;
              }
            }
            cells[column] = value.trim();
            if (column > maxColumn) maxColumn = column;
          }
          if (maxColumn < 0) continue;
          final row = List<String>.filled(maxColumn + 1, '');
          cells.forEach((index, value) => row[index] = value);
          rows.add(row);
          totalRows++;
        }
        _convertExcelDates(rows);
        output.writeln('### ${sheet.name}');
        for (final row in rows) {
          output.writeln(row.map(_cleanCell).join('\t'));
        }
        if (totalRows >= 5000) break;
      }
      final text = output.toString().trim();
      if (text.isEmpty) {
        throw const TrainingImportException(
          'Não encontrei células preenchidas na planilha Excel.',
        );
      }
      return text;
    } on TrainingImportException {
      rethrow;
    } catch (error) {
      throw TrainingImportException(
        'Não foi possível ler a planilha Excel: $error',
      );
    }
  }

  static int _columnIndex(String reference) {
    final match = RegExp(r'^([A-Za-z]+)').firstMatch(reference);
    if (match == null) return -1;
    var result = 0;
    for (final unit in match.group(1)!.toUpperCase().codeUnits) {
      result = result * 26 + (unit - 64);
    }
    return result - 1;
  }

  static void _convertExcelDates(List<List<String>> rows) {
    if (rows.isEmpty) return;
    var headerIndex = -1;
    final dateColumns = <int>{};
    for (var r = 0; r < rows.length && r < 20; r++) {
      final row = rows[r];
      final found = <int>{};
      for (var c = 0; c < row.length; c++) {
        final key = _normalize(row[c]);
        if (key.contains('DATA') ||
            key.contains('VENC') ||
            key.contains('VALIDADE') ||
            key == 'DT') {
          found.add(c);
        }
      }
      if (found.isNotEmpty) {
        headerIndex = r;
        dateColumns.addAll(found);
        break;
      }
    }
    if (headerIndex < 0 || dateColumns.isEmpty) return;
    for (var r = headerIndex + 1; r < rows.length; r++) {
      for (final c in dateColumns) {
        if (c >= rows[r].length) continue;
        final serial = double.tryParse(rows[r][c].replaceAll(',', '.'));
        if (serial == null || serial < 20000 || serial > 80000) continue;
        final date = DateTime(1899, 12, 30).add(Duration(days: serial.floor()));
        rows[r][c] =
            '${date.year.toString().padLeft(4, '0')}-${date.month.toString().padLeft(2, '0')}-${date.day.toString().padLeft(2, '0')}';
      }
    }
  }

  static String _cleanCell(String value) =>
      value.replaceAll('\t', ' ').replaceAll('\n', ' ').replaceAll('\r', ' ').trim();

  static String _digits(String value) => value.replaceAll(RegExp(r'\D'), '');

  static String _normalize(String value) {
    var text = value.toUpperCase().trim();
    const source = 'ÁÀÂÃÄÉÈÊËÍÌÎÏÓÒÔÕÖÚÙÛÜÇÑ';
    const target = 'AAAAAEEEEIIIIOOOOOUUUUCN';
    for (var i = 0; i < source.length; i++) {
      text = text.replaceAll(source[i], target[i]);
    }
    return text.replaceAll(RegExp(r'[^A-Z0-9]+'), ' ').trim();
  }

  static String _safeName(String value) {
    final cleaned = value
        .replaceAll(RegExp(r'[\\/:*?"<>|\x00-\x1F]'), '_')
        .replaceAll(RegExp(r'\s+'), '_')
        .trim();
    return cleaned.isEmpty ? 'arquivo' : cleaned.substring(0, cleaned.length > 90 ? 90 : cleaned.length);
  }
}

extension _IterableFirstOrNull<T> on Iterable<T> {
  T? get firstOrNull => isEmpty ? null : first;
}
