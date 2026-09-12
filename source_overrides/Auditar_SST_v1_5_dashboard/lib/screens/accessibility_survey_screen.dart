import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:path_provider/path_provider.dart';

import '../database.dart';
import '../services/accessibility_ai_service.dart';

class AccessibilitySurveyScreen extends StatefulWidget {
  const AccessibilitySurveyScreen({super.key});

  @override
  State<AccessibilitySurveyScreen> createState() =>
      _AccessibilitySurveyScreenState();
}

class _AccessibilitySurveyScreenState extends State<AccessibilitySurveyScreen> {
  bool _loading = true;
  List<Map<String, dynamic>> _projects = [];

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final projects = await _AccessibilityStorage.loadProjects();
    if (!mounted) return;
    setState(() {
      _projects = projects;
      _loading = false;
    });
  }

  Future<void> _createProject() async {
    final companyController = TextEditingController();
    final addressController = TextEditingController();
    final responsibleController = TextEditingController();

    final result = await showDialog<Map<String, String>>(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: const Text('Novo levantamento'),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                TextField(
                  controller: companyController,
                  textCapitalization: TextCapitalization.words,
                  decoration: const InputDecoration(
                    labelText: 'Empresa / estabelecimento *',
                    border: OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: addressController,
                  textCapitalization: TextCapitalization.sentences,
                  maxLines: 2,
                  decoration: const InputDecoration(
                    labelText: 'Endereço / unidade',
                    border: OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: responsibleController,
                  textCapitalization: TextCapitalization.words,
                  decoration: const InputDecoration(
                    labelText: 'Responsável que acompanha a vistoria',
                    border: OutlineInputBorder(),
                  ),
                ),
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(),
              child: const Text('Cancelar'),
            ),
            FilledButton(
              onPressed: () {
                if (companyController.text.trim().isEmpty) return;
                Navigator.of(context).pop({
                  'companyName': companyController.text.trim(),
                  'address': addressController.text.trim(),
                  'responsible': responsibleController.text.trim(),
                });
              },
              child: const Text('Criar'),
            ),
          ],
        );
      },
    );

    companyController.dispose();
    addressController.dispose();
    responsibleController.dispose();
    if (result == null) return;

    final project = <String, dynamic>{
      'id': DateTime.now().microsecondsSinceEpoch.toString(),
      'companyName': result['companyName'] ?? '',
      'address': result['address'] ?? '',
      'responsible': result['responsible'] ?? '',
      'createdAt': DateTime.now().toIso8601String(),
      'updatedAt': DateTime.now().toIso8601String(),
      'notes': '',
      'points': <Map<String, dynamic>>[],
    };
    _projects = [project, ..._projects];
    await _AccessibilityStorage.saveProjects(_projects);
    if (!mounted) return;
    await _openProject(project['id'] as String);
  }

  Future<void> _openProject(String id) async {
    final index = _projects.indexWhere((item) => '${item['id']}' == id);
    if (index < 0) return;
    final updated = await Navigator.of(context).push<Map<String, dynamic>>(
      MaterialPageRoute(
        builder: (_) => AccessibilityProjectScreen(
          project: Map<String, dynamic>.from(_projects[index]),
        ),
      ),
    );
    if (updated == null) return;
    final updatedIndex = _projects.indexWhere(
      (item) => '${item['id']}' == '${updated['id']}',
    );
    if (updatedIndex >= 0) {
      _projects[updatedIndex] = updated;
    } else {
      _projects.insert(0, updated);
    }
    await _AccessibilityStorage.saveProjects(_projects);
    if (mounted) setState(() {});
  }

  Future<void> _deleteProject(Map<String, dynamic> project) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Excluir levantamento?'),
        content: Text(
          'O levantamento de ${project['companyName']} será removido deste aparelho.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: const Text('Cancelar'),
          ),
          FilledButton(
            onPressed: () => Navigator.of(context).pop(true),
            child: const Text('Excluir'),
          ),
        ],
      ),
    );
    if (confirmed != true) return;
    _projects.removeWhere((item) => '${item['id']}' == '${project['id']}');
    await _AccessibilityStorage.saveProjects(_projects);
    if (mounted) setState(() {});
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Laudo de Acessibilidade'),
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _createProject,
        icon: const Icon(Icons.add_rounded),
        label: const Text('Novo levantamento'),
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _projects.isEmpty
              ? _emptyState()
              : RefreshIndicator(
                  onRefresh: _load,
                  child: ListView.builder(
                    padding: const EdgeInsets.fromLTRB(14, 14, 14, 96),
                    itemCount: _projects.length + 1,
                    itemBuilder: (context, index) {
                      if (index == 0) return _introCard();
                      final project = _projects[index - 1];
                      return _projectCard(project);
                    },
                  ),
                ),
    );
  }

  Widget _introCard() {
    return Card(
      margin: const EdgeInsets.only(bottom: 14),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(
                  Icons.accessible_forward_rounded,
                  color: Theme.of(context).colorScheme.primary,
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(
                    'Levantamento guiado + Assistente IA',
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                          fontWeight: FontWeight.w800,
                        ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            const Text(
              'Registre medidas, fotos e observações por ponto da edificação. A IA ajuda a organizar o achado, sugerir o que precisa ser conferido e preparar recomendações, sem substituir a validação técnica do laudo.',
            ),
          ],
        ),
      ),
    );
  }

  Widget _emptyState() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(28),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.accessible_rounded, size: 68),
            const SizedBox(height: 16),
            Text(
              'Nenhum levantamento de acessibilidade',
              style: Theme.of(context).textTheme.titleLarge,
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 8),
            const Text(
              'Crie o primeiro levantamento para iniciar a coleta em campo.',
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 18),
            FilledButton.icon(
              onPressed: _createProject,
              icon: const Icon(Icons.add_rounded),
              label: const Text('Novo levantamento'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _projectCard(Map<String, dynamic> project) {
    final points = _AccessibilityStorage.pointsOf(project);
    final nonConforming = points
        .where((point) => '${point['status']}' == 'Não conforme')
        .length;
    final pending = points
        .where((point) => '${point['status']}' == 'Requer verificação')
        .length;

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: InkWell(
        borderRadius: BorderRadius.circular(12),
        onTap: () => _openProject('${project['id']}'),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Icon(Icons.apartment_rounded),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          '${project['companyName'] ?? ''}',
                          style:
                              Theme.of(context).textTheme.titleMedium?.copyWith(
                                    fontWeight: FontWeight.w800,
                                  ),
                        ),
                        if ('${project['address'] ?? ''}'.trim().isNotEmpty)
                          Padding(
                            padding: const EdgeInsets.only(top: 3),
                            child: Text('${project['address']}'),
                          ),
                      ],
                    ),
                  ),
                  PopupMenuButton<String>(
                    onSelected: (value) {
                      if (value == 'delete') _deleteProject(project);
                    },
                    itemBuilder: (_) => const [
                      PopupMenuItem(
                        value: 'delete',
                        child: Text('Excluir levantamento'),
                      ),
                    ],
                  ),
                ],
              ),
              const SizedBox(height: 12),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  _countChip('${points.length} pontos', Icons.pin_drop_outlined),
                  _countChip(
                    '$nonConforming não conformes',
                    Icons.warning_amber_rounded,
                  ),
                  _countChip(
                    '$pending a conferir',
                    Icons.help_outline_rounded,
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _countChip(String text, IconData icon) {
    return Chip(
      avatar: Icon(icon, size: 17),
      label: Text(text),
      visualDensity: VisualDensity.compact,
    );
  }
}

class AccessibilityProjectScreen extends StatefulWidget {
  const AccessibilityProjectScreen({
    super.key,
    required this.project,
  });

  final Map<String, dynamic> project;

  @override
  State<AccessibilityProjectScreen> createState() =>
      _AccessibilityProjectScreenState();
}

class _AccessibilityProjectScreenState extends State<AccessibilityProjectScreen> {
  late Map<String, dynamic> _project;
  bool _saving = false;

  @override
  void initState() {
    super.initState();
    _project = Map<String, dynamic>.from(widget.project);
    _project['points'] = _AccessibilityStorage.pointsOf(widget.project);
  }

  List<Map<String, dynamic>> get _points =>
      _AccessibilityStorage.pointsOf(_project);

  Future<void> _persist() async {
    _project['updatedAt'] = DateTime.now().toIso8601String();
    setState(() => _saving = true);
    await _AccessibilityStorage.upsertProject(_project);
    if (!mounted) return;
    setState(() => _saving = false);
  }

  Future<void> _addPoint() async {
    final point = await Navigator.of(context).push<Map<String, dynamic>>(
      MaterialPageRoute(
        builder: (_) => AccessibilityPointEditorScreen(
          projectId: '${_project['id']}',
          companyName: '${_project['companyName'] ?? ''}',
        ),
      ),
    );
    if (point == null) return;
    final points = _points;
    points.add(point);
    _project['points'] = points;
    await _persist();
  }

  Future<void> _editPoint(Map<String, dynamic> point) async {
    final updated = await Navigator.of(context).push<Map<String, dynamic>>(
      MaterialPageRoute(
        builder: (_) => AccessibilityPointEditorScreen(
          projectId: '${_project['id']}',
          companyName: '${_project['companyName'] ?? ''}',
          point: Map<String, dynamic>.from(point),
        ),
      ),
    );
    if (updated == null) return;
    final points = _points;
    final index = points.indexWhere((item) => '${item['id']}' == '${updated['id']}');
    if (index >= 0) points[index] = updated;
    _project['points'] = points;
    await _persist();
  }

  Future<void> _deletePoint(Map<String, dynamic> point) async {
    final points = _points;
    points.removeWhere((item) => '${item['id']}' == '${point['id']}');
    _project['points'] = points;
    await _persist();
  }

  void _showChecklistSummary() {
    final points = _points;
    final missingPhotos = points
        .where((point) => (point['photos'] as List? ?? const []).isEmpty)
        .length;
    final notEvaluated = points
        .where((point) => '${point['status']}' == 'Não avaliado')
        .length;
    final needsCheck = points
        .where((point) => '${point['status']}' == 'Requer verificação')
        .length;
    final withoutObservation = points
        .where((point) => '${point['observation'] ?? ''}'.trim().isEmpty)
        .length;

    showModalBottomSheet<void>(
      context: context,
      showDragHandle: true,
      builder: (context) => Padding(
        padding: const EdgeInsets.fromLTRB(20, 4, 20, 28),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Conferência do levantamento',
              style: Theme.of(context).textTheme.titleLarge,
            ),
            const SizedBox(height: 12),
            _summaryLine('Pontos cadastrados', '${points.length}'),
            _summaryLine('Sem foto', '$missingPhotos'),
            _summaryLine('Não avaliados', '$notEvaluated'),
            _summaryLine('Requerem verificação', '$needsCheck'),
            _summaryLine('Sem observação técnica', '$withoutObservation'),
            const SizedBox(height: 12),
            const Text(
              'A conferência ajuda a identificar lacunas de coleta. A conclusão de conformidade e o laudo final permanecem sob revisão do responsável técnico.',
            ),
          ],
        ),
      ),
    );
  }

  Widget _summaryLine(String label, String value) {
    return ListTile(
      contentPadding: EdgeInsets.zero,
      dense: true,
      title: Text(label),
      trailing: Text(
        value,
        style: const TextStyle(fontWeight: FontWeight.w800),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final points = _points;
    final nonConforming = points
        .where((point) => '${point['status']}' == 'Não conforme')
        .length;

    return PopScope(
      canPop: false,
      onPopInvokedWithResult: (didPop, result) {
        if (didPop) return;
        Navigator.of(context).pop(_project);
      },
      child: Scaffold(
        appBar: AppBar(
          title: Text('${_project['companyName'] ?? 'Acessibilidade'}'),
          actions: [
            if (_saving)
              const Padding(
                padding: EdgeInsets.all(14),
                child: SizedBox(
                  width: 18,
                  height: 18,
                  child: CircularProgressIndicator(strokeWidth: 2),
                ),
              ),
            IconButton(
              tooltip: 'Conferir levantamento',
              onPressed: _showChecklistSummary,
              icon: const Icon(Icons.fact_check_outlined),
            ),
          ],
        ),
        floatingActionButton: FloatingActionButton.extended(
          onPressed: _addPoint,
          icon: const Icon(Icons.add_location_alt_outlined),
          label: const Text('Adicionar ponto'),
        ),
        body: ListView(
          padding: const EdgeInsets.fromLTRB(14, 14, 14, 96),
          children: [
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Levantamento em campo',
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                            fontWeight: FontWeight.w800,
                          ),
                    ),
                    const SizedBox(height: 8),
                    Text('${_project['address'] ?? ''}'.trim().isEmpty
                        ? 'Endereço não informado'
                        : '${_project['address']}'),
                    if ('${_project['responsible'] ?? ''}'.trim().isNotEmpty)
                      Padding(
                        padding: const EdgeInsets.only(top: 4),
                        child: Text(
                          'Acompanhante: ${_project['responsible']}',
                        ),
                      ),
                    const SizedBox(height: 12),
                    Wrap(
                      spacing: 8,
                      runSpacing: 8,
                      children: [
                        Chip(label: Text('${points.length} pontos')),
                        Chip(label: Text('$nonConforming não conformes')),
                        const Chip(
                          avatar: Icon(Icons.auto_awesome_rounded, size: 17),
                          label: Text('Assistente IA por ponto'),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 12),
            if (points.isEmpty)
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(22),
                  child: Column(
                    children: [
                      const Icon(Icons.straighten_rounded, size: 48),
                      const SizedBox(height: 10),
                      const Text(
                        'Adicione o primeiro ponto da vistoria: acesso, porta, rampa, sanitário, corredor, vaga, sinalização e outros.',
                        textAlign: TextAlign.center,
                      ),
                      const SizedBox(height: 14),
                      FilledButton.icon(
                        onPressed: _addPoint,
                        icon: const Icon(Icons.add_rounded),
                        label: const Text('Adicionar ponto'),
                      ),
                    ],
                  ),
                ),
              )
            else
              ...points.map(_pointCard),
          ],
        ),
      ),
    );
  }

  Widget _pointCard(Map<String, dynamic> point) {
    final photos = (point['photos'] as List? ?? const []).cast<String>();
    final ai = point['ai'] is Map
        ? Map<String, dynamic>.from(point['ai'] as Map)
        : <String, dynamic>{};
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: InkWell(
        borderRadius: BorderRadius.circular(12),
        onTap: () => _editPoint(point),
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Expanded(
                    child: Text(
                      '${point['category'] ?? ''}',
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                            fontWeight: FontWeight.w800,
                          ),
                    ),
                  ),
                  _statusChip('${point['status'] ?? 'Não avaliado'}'),
                  PopupMenuButton<String>(
                    onSelected: (value) {
                      if (value == 'delete') _deletePoint(point);
                    },
                    itemBuilder: (_) => const [
                      PopupMenuItem(
                        value: 'delete',
                        child: Text('Excluir ponto'),
                      ),
                    ],
                  ),
                ],
              ),
              if ('${point['location'] ?? ''}'.trim().isNotEmpty)
                Padding(
                  padding: const EdgeInsets.only(top: 4),
                  child: Text('${point['location']}'),
                ),
              const SizedBox(height: 10),
              Row(
                children: [
                  Icon(Icons.photo_camera_outlined, size: 18, color: Colors.grey.shade700),
                  const SizedBox(width: 5),
                  Text('${photos.length} foto(s)'),
                  const SizedBox(width: 16),
                  Icon(Icons.auto_awesome_rounded, size: 18, color: Colors.grey.shade700),
                  const SizedBox(width: 5),
                  Text(ai.isEmpty ? 'IA não analisada' : 'IA analisada'),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _statusChip(String status) {
    IconData icon;
    switch (status) {
      case 'Conforme':
        icon = Icons.check_circle_outline_rounded;
        break;
      case 'Não conforme':
        icon = Icons.error_outline_rounded;
        break;
      case 'Requer verificação':
        icon = Icons.help_outline_rounded;
        break;
      default:
        icon = Icons.radio_button_unchecked_rounded;
    }
    return Chip(
      avatar: Icon(icon, size: 17),
      label: Text(status),
      visualDensity: VisualDensity.compact,
    );
  }
}

class AccessibilityPointEditorScreen extends StatefulWidget {
  const AccessibilityPointEditorScreen({
    super.key,
    required this.projectId,
    required this.companyName,
    this.point,
  });

  final String projectId;
  final String companyName;
  final Map<String, dynamic>? point;

  @override
  State<AccessibilityPointEditorScreen> createState() =>
      _AccessibilityPointEditorScreenState();
}

class _AccessibilityPointEditorScreenState
    extends State<AccessibilityPointEditorScreen> {
  final _formKey = GlobalKey<FormState>();
  final _picker = ImagePicker();
  final _locationController = TextEditingController();
  final _observationController = TextEditingController();
  final Map<String, TextEditingController> _fieldControllers = {};

  late String _category;
  late String _status;
  List<String> _photos = [];
  Map<String, dynamic> _ai = {};
  bool _analyzing = false;

  @override
  void initState() {
    super.initState();
    final point = widget.point;
    _category = '${point?['category'] ?? _AccessibilityCatalog.categories.first}';
    _status = '${point?['status'] ?? 'Não avaliado'}';
    _locationController.text = '${point?['location'] ?? ''}';
    _observationController.text = '${point?['observation'] ?? ''}';
    _photos = (point?['photos'] as List? ?? const []).cast<String>();
    if (point?['ai'] is Map) {
      _ai = Map<String, dynamic>.from(point!['ai'] as Map);
    }
    _loadFieldControllers(point?['measurements']);
  }

  void _loadFieldControllers(dynamic rawMeasurements) {
    for (final controller in _fieldControllers.values) {
      controller.dispose();
    }
    _fieldControllers.clear();
    final existing = rawMeasurements is Map
        ? Map<String, dynamic>.from(rawMeasurements)
        : <String, dynamic>{};
    for (final field in _AccessibilityCatalog.fieldsFor(_category)) {
      _fieldControllers[field] = TextEditingController(
        text: '${existing[field] ?? ''}',
      );
    }
  }

  @override
  void dispose() {
    _locationController.dispose();
    _observationController.dispose();
    for (final controller in _fieldControllers.values) {
      controller.dispose();
    }
    super.dispose();
  }

  Future<void> _changeCategory(String? value) async {
    if (value == null || value == _category) return;
    setState(() {
      _category = value;
      _loadFieldControllers(null);
      _ai = {};
    });
  }

  Future<String> _storePhoto(XFile photo) async {
    final root = await getApplicationDocumentsDirectory();
    final folder = Directory(
      '${root.path}${Platform.pathSeparator}accessibility_evidence${Platform.pathSeparator}${widget.projectId}',
    );
    if (!await folder.exists()) await folder.create(recursive: true);
    final ext = photo.path.toLowerCase().endsWith('.png') ? '.png' : '.jpg';
    final target = File(
      '${folder.path}${Platform.pathSeparator}${DateTime.now().microsecondsSinceEpoch}$ext',
    );
    await File(photo.path).copy(target.path);
    return target.path;
  }

  Future<void> _takePhoto() async {
    final photo = await _picker.pickImage(
      source: ImageSource.camera,
      imageQuality: 62,
      maxWidth: 1440,
      maxHeight: 1440,
    );
    if (photo == null) return;
    final path = await _storePhoto(photo);
    if (!mounted) return;
    setState(() {
      _photos = [..._photos, path].take(6).toList(growable: true);
      _ai = {};
    });
  }

  Future<void> _pickPhoto() async {
    final photo = await _picker.pickImage(
      source: ImageSource.gallery,
      imageQuality: 62,
      maxWidth: 1440,
      maxHeight: 1440,
    );
    if (photo == null) return;
    final path = await _storePhoto(photo);
    if (!mounted) return;
    setState(() {
      _photos = [..._photos, path].take(6).toList(growable: true);
      _ai = {};
    });
  }

  Future<List<String>> _imageDataUris() async {
    final result = <String>[];
    for (final path in _photos.take(4)) {
      final file = File(path);
      if (!await file.exists()) continue;
      final bytes = await file.readAsBytes();
      final mime = path.toLowerCase().endsWith('.png') ? 'image/png' : 'image/jpeg';
      result.add('data:$mime;base64,${base64Encode(bytes)}');
    }
    return result;
  }

  Map<String, String> _measurements() {
    return _fieldControllers.map(
      (key, controller) => MapEntry(key, controller.text.trim()),
    );
  }

  Future<void> _analyzeWithAi() async {
    if (_locationController.text.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Informe o local exato antes de analisar.')),
      );
      return;
    }
    setState(() => _analyzing = true);
    try {
      final images = await _imageDataUris();
      final result = await AccessibilityAiService.analyzePoint(
        companyName: widget.companyName,
        category: _category,
        location: _locationController.text.trim(),
        measurements: _measurements(),
        technicianObservation: _observationController.text.trim(),
        imageDataUris: images,
      );
      if (!mounted) return;
      setState(() {
        _ai = <String, dynamic>{
          'summary': result.summary,
          'recommendation': result.recommendation,
          'checksRequired': result.checksRequired,
          'references': result.references,
          'confidence': result.confidence,
          'analyzedAt': DateTime.now().toIso8601String(),
        };
      });
      _showAiResult();
    } catch (error) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('$error')),
      );
    } finally {
      if (mounted) setState(() => _analyzing = false);
    }
  }

  void _showAiResult() {
    final checks = (_ai['checksRequired'] as List? ?? const []).cast<dynamic>();
    final references = (_ai['references'] as List? ?? const []).cast<dynamic>();
    showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      showDragHandle: true,
      builder: (context) => SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.fromLTRB(20, 4, 20, 28),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  const Icon(Icons.auto_awesome_rounded),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      'Assistente IA · Acessibilidade',
                      style: Theme.of(context).textTheme.titleLarge,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 6),
              const Text(
                'Rascunho de apoio. Confirme medidas, requisitos e conclusão técnica antes de usar no laudo.',
              ),
              const SizedBox(height: 16),
              _aiSection('Análise', '${_ai['summary'] ?? ''}'),
              _aiSection('Recomendação', '${_ai['recommendation'] ?? ''}'),
              if (checks.isNotEmpty)
                _aiList('Conferir presencialmente', checks.map((e) => '$e').toList()),
              if (references.isNotEmpty)
                _aiList('Referências prováveis a conferir', references.map((e) => '$e').toList()),
              if ('${_ai['confidence'] ?? ''}'.trim().isNotEmpty)
                _aiSection('Confiança da sugestão', '${_ai['confidence']}'),
            ],
          ),
        ),
      ),
    );
  }

  Widget _aiSection(String title, String text) {
    if (text.trim().isEmpty) return const SizedBox.shrink();
    return Padding(
      padding: const EdgeInsets.only(bottom: 14),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title, style: const TextStyle(fontWeight: FontWeight.w800)),
          const SizedBox(height: 4),
          Text(text),
        ],
      ),
    );
  }

  Widget _aiList(String title, List<String> items) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 14),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title, style: const TextStyle(fontWeight: FontWeight.w800)),
          const SizedBox(height: 4),
          ...items.map(
            (item) => Padding(
              padding: const EdgeInsets.only(bottom: 4),
              child: Text('• $item'),
            ),
          ),
        ],
      ),
    );
  }

  void _save() {
    if (!(_formKey.currentState?.validate() ?? false)) return;
    final point = <String, dynamic>{
      'id': '${widget.point?['id'] ?? DateTime.now().microsecondsSinceEpoch}',
      'category': _category,
      'location': _locationController.text.trim(),
      'status': _status,
      'measurements': _measurements(),
      'observation': _observationController.text.trim(),
      'photos': _photos,
      'ai': _ai,
      'updatedAt': DateTime.now().toIso8601String(),
    };
    Navigator.of(context).pop(point);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.point == null ? 'Novo ponto' : 'Editar ponto'),
        actions: [
          TextButton(
            onPressed: _save,
            child: const Text('SALVAR'),
          ),
        ],
      ),
      body: Form(
        key: _formKey,
        child: ListView(
          padding: const EdgeInsets.fromLTRB(14, 14, 14, 28),
          children: [
            DropdownButtonFormField<String>(
              value: _category,
              decoration: const InputDecoration(
                labelText: 'Categoria do ponto',
                border: OutlineInputBorder(),
              ),
              items: _AccessibilityCatalog.categories
                  .map((item) => DropdownMenuItem(value: item, child: Text(item)))
                  .toList(),
              onChanged: _changeCategory,
            ),
            const SizedBox(height: 12),
            TextFormField(
              controller: _locationController,
              textCapitalization: TextCapitalization.sentences,
              decoration: const InputDecoration(
                labelText: 'Local exato *',
                hintText: 'Ex.: entrada principal, banheiro térreo, corredor bloco B',
                border: OutlineInputBorder(),
              ),
              validator: (value) => value == null || value.trim().isEmpty
                  ? 'Informe onde este ponto está localizado.'
                  : null,
            ),
            const SizedBox(height: 12),
            DropdownButtonFormField<String>(
              value: _status,
              decoration: const InputDecoration(
                labelText: 'Avaliação do técnico',
                border: OutlineInputBorder(),
              ),
              items: const [
                'Não avaliado',
                'Conforme',
                'Não conforme',
                'Requer verificação',
              ]
                  .map((item) => DropdownMenuItem(value: item, child: Text(item)))
                  .toList(),
              onChanged: (value) {
                if (value != null) setState(() => _status = value);
              },
            ),
            const SizedBox(height: 18),
            Text(
              'Medidas e dados de campo',
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.w800,
                  ),
            ),
            const SizedBox(height: 5),
            const Text(
              'Preencha somente o que foi medido ou verificado. Não estime valores.',
            ),
            const SizedBox(height: 12),
            ..._fieldControllers.entries.map(
              (entry) => Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: TextFormField(
                  controller: entry.value,
                  textCapitalization: TextCapitalization.sentences,
                  decoration: InputDecoration(
                    labelText: entry.key,
                    border: const OutlineInputBorder(),
                  ),
                ),
              ),
            ),
            TextFormField(
              controller: _observationController,
              maxLines: 4,
              textCapitalization: TextCapitalization.sentences,
              decoration: const InputDecoration(
                labelText: 'Observação do técnico',
                hintText: 'Descreva barreiras, condição encontrada ou contexto que a medida sozinha não mostra.',
                border: OutlineInputBorder(),
                alignLabelWithHint: true,
              ),
            ),
            const SizedBox(height: 18),
            Row(
              children: [
                Expanded(
                  child: Text(
                    'Evidências fotográficas',
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                          fontWeight: FontWeight.w800,
                        ),
                  ),
                ),
                Text('${_photos.length}/6'),
              ],
            ),
            const SizedBox(height: 10),
            Row(
              children: [
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: _photos.length >= 6 ? null : _takePhoto,
                    icon: const Icon(Icons.photo_camera_outlined),
                    label: const Text('Câmera'),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: _photos.length >= 6 ? null : _pickPhoto,
                    icon: const Icon(Icons.photo_library_outlined),
                    label: const Text('Galeria'),
                  ),
                ),
              ],
            ),
            if (_photos.isNotEmpty) ...[
              const SizedBox(height: 10),
              SizedBox(
                height: 94,
                child: ListView.separated(
                  scrollDirection: Axis.horizontal,
                  itemCount: _photos.length,
                  separatorBuilder: (_, __) => const SizedBox(width: 8),
                  itemBuilder: (context, index) {
                    final path = _photos[index];
                    return Stack(
                      children: [
                        ClipRRect(
                          borderRadius: BorderRadius.circular(10),
                          child: Image.file(
                            File(path),
                            width: 94,
                            height: 94,
                            fit: BoxFit.cover,
                            errorBuilder: (_, __, ___) => Container(
                              width: 94,
                              height: 94,
                              alignment: Alignment.center,
                              color: Colors.black12,
                              child: const Icon(Icons.broken_image_outlined),
                            ),
                          ),
                        ),
                        Positioned(
                          right: 2,
                          top: 2,
                          child: IconButton.filledTonal(
                            visualDensity: VisualDensity.compact,
                            onPressed: () => setState(() {
                              _photos.removeAt(index);
                              _ai = {};
                            }),
                            icon: const Icon(Icons.close_rounded, size: 17),
                          ),
                        ),
                      ],
                    );
                  },
                ),
              ),
            ],
            const SizedBox(height: 18),
            Card(
              child: Padding(
                padding: const EdgeInsets.all(14),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        const Icon(Icons.auto_awesome_rounded),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            'Assistente IA',
                            style: Theme.of(context)
                                .textTheme
                                .titleMedium
                                ?.copyWith(fontWeight: FontWeight.w800),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 6),
                    const Text(
                      'Use a IA depois de registrar as medidas e observações. Com foto, ela também considera a evidência visual. Toda sugestão deve ser revisada.',
                    ),
                    const SizedBox(height: 12),
                    SizedBox(
                      width: double.infinity,
                      child: FilledButton.icon(
                        onPressed: _analyzing ? null : _analyzeWithAi,
                        icon: _analyzing
                            ? const SizedBox(
                                width: 18,
                                height: 18,
                                child: CircularProgressIndicator(strokeWidth: 2),
                              )
                            : const Icon(Icons.auto_awesome_rounded),
                        label: Text(
                          _analyzing
                              ? 'Analisando...'
                              : _ai.isEmpty
                                  ? 'Analisar este ponto com IA'
                                  : 'Analisar novamente',
                        ),
                      ),
                    ),
                    if (_ai.isNotEmpty) ...[
                      const SizedBox(height: 10),
                      OutlinedButton.icon(
                        onPressed: _showAiResult,
                        icon: const Icon(Icons.visibility_outlined),
                        label: const Text('Ver análise salva'),
                      ),
                    ],
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),
            FilledButton.icon(
              onPressed: _save,
              icon: const Icon(Icons.save_outlined),
              label: const Text('Salvar ponto'),
            ),
          ],
        ),
      ),
    );
  }
}

class _AccessibilityCatalog {
  static const categories = <String>[
    'Acesso / entrada',
    'Calçada / área externa',
    'Rota acessível',
    'Corredor / circulação',
    'Porta',
    'Rampa',
    'Escada',
    'Corrimão / guarda-corpo',
    'Sanitário acessível',
    'Vaga reservada',
    'Balcão / atendimento',
    'Piso tátil / sinalização',
    'Elevador / plataforma',
    'Mobiliário / mesa',
    'Outro ponto',
  ];

  static const Map<String, List<String>> _fields = {
    'Acesso / entrada': [
      'Largura livre do acesso (cm)',
      'Existe desnível? Qual?',
      'Piso / superfície',
      'Obstáculos encontrados',
    ],
    'Calçada / área externa': [
      'Faixa livre de circulação (cm)',
      'Inclinação / condição do piso',
      'Desníveis / interferências',
      'Obstáculos ou mobiliário na rota',
    ],
    'Rota acessível': [
      'Largura livre (cm)',
      'Comprimento aproximado',
      'Desníveis existentes',
      'Condição do piso',
      'Obstáculos / interferências',
    ],
    'Corredor / circulação': [
      'Largura livre (cm)',
      'Extensão aproximada',
      'Pontos de estreitamento',
      'Obstáculos encontrados',
    ],
    'Porta': [
      'Largura livre (cm)',
      'Altura livre (cm)',
      'Tipo de maçaneta / acionamento',
      'Soleira / desnível (cm)',
      'Espaço para aproximação / manobra',
    ],
    'Rampa': [
      'Largura (cm)',
      'Comprimento do trecho (cm)',
      'Desnível vencido (cm)',
      'Inclinação medida ou calculada (%)',
      'Patamares',
      'Corrimãos / proteção lateral',
    ],
    'Escada': [
      'Largura (cm)',
      'Altura do espelho (cm)',
      'Profundidade do piso (cm)',
      'Quantidade de degraus',
      'Corrimãos',
      'Sinalização / contraste',
    ],
    'Corrimão / guarda-corpo': [
      'Altura medida (cm)',
      'Diâmetro / empunhadura',
      'Continuidade',
      'Prolongamento',
      'Condição / fixação',
    ],
    'Sanitário acessível': [
      'Largura livre da porta (cm)',
      'Dimensão interna / área de manobra',
      'Altura da bacia (cm)',
      'Barras de apoio',
      'Altura / aproximação do lavatório',
      'Acessórios / espelho / acionamentos',
    ],
    'Vaga reservada': [
      'Largura da vaga (cm)',
      'Comprimento da vaga (cm)',
      'Faixa adicional / circulação',
      'Sinalização horizontal e vertical',
      'Ligação com rota acessível',
    ],
    'Balcão / atendimento': [
      'Altura do balcão (cm)',
      'Largura do trecho acessível (cm)',
      'Altura livre inferior (cm)',
      'Profundidade para aproximação (cm)',
    ],
    'Piso tátil / sinalização': [
      'Tipo de sinalização',
      'Local de início e término',
      'Continuidade',
      'Contraste visual',
      'Interferências encontradas',
    ],
    'Elevador / plataforma': [
      'Largura livre da porta (cm)',
      'Dimensões internas',
      'Altura dos comandos (cm)',
      'Sinalização visual / sonora / tátil',
      'Espaço de aproximação',
    ],
    'Mobiliário / mesa': [
      'Altura da superfície (cm)',
      'Altura livre inferior (cm)',
      'Largura livre inferior (cm)',
      'Profundidade livre (cm)',
      'Espaço de aproximação',
    ],
    'Outro ponto': [
      'Medida principal',
      'Característica observada',
      'Barreira / dificuldade encontrada',
    ],
  };

  static List<String> fieldsFor(String category) =>
      List<String>.from(_fields[category] ?? _fields['Outro ponto']!);
}

class _AccessibilityStorage {
  static const _key = 'accessibility_projects_v1';

  static List<Map<String, dynamic>> pointsOf(Map<String, dynamic> project) {
    final raw = project['points'];
    if (raw is! List) return <Map<String, dynamic>>[];
    return raw
        .whereType<Map>()
        .map((item) => Map<String, dynamic>.from(item))
        .toList(growable: true);
  }

  static Future<List<Map<String, dynamic>>> loadProjects() async {
    final raw = await AppDatabase.instance.getSetting(_key, fallback: '[]');
    try {
      final decoded = jsonDecode(raw);
      if (decoded is! List) return [];
      return decoded
          .whereType<Map>()
          .map((item) => Map<String, dynamic>.from(item))
          .toList(growable: true);
    } catch (_) {
      return [];
    }
  }

  static Future<void> saveProjects(List<Map<String, dynamic>> projects) async {
    await AppDatabase.instance.setSetting(_key, jsonEncode(projects));
  }

  static Future<void> upsertProject(Map<String, dynamic> project) async {
    final projects = await loadProjects();
    final index = projects.indexWhere(
      (item) => '${item['id']}' == '${project['id']}',
    );
    if (index >= 0) {
      projects[index] = project;
    } else {
      projects.insert(0, project);
    }
    await saveProjects(projects);
  }
}
