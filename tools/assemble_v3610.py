#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise RuntimeError(f'Trecho esperado não encontrado: {label}')
    return text.replace(old, new, 1)


def main() -> int:
    repo = Path(__file__).resolve().parent.parent
    subprocess.run([sys.executable, str(repo / 'tools' / 'assemble_v3600.py')], cwd=repo, check=True)
    app = repo / 'app' / 'Auditar_SST_v1_5_dashboard'

    # Versão
    pub = app / 'pubspec.yaml'
    text = pub.read_text(encoding='utf-8')
    text = replace_once(text, 'version: 3.36.0+155', 'version: 3.36.1+156', 'versão 3.36.1')
    pub.write_text(text, encoding='utf-8')

    # Checklist: câmera só no celular; no Windows fica seleção de arquivo/foto.
    p = app / 'lib' / 'screens' / 'checklist_screen.dart'
    text = p.read_text(encoding='utf-8')
    old = """                                OutlinedButton.icon(\n                                  onPressed: evidence.length >= 10\n                                      ? null\n                                      : () => _takePhoto(item.id),\n                                  icon: const Icon(Icons.camera_alt),\n                                  label: const Text('Tirar foto'),\n                                ),\n"""
    new = """                                if (!Platform.isWindows)\n                                  OutlinedButton.icon(\n                                    onPressed: evidence.length >= 10\n                                        ? null\n                                        : () => _takePhoto(item.id),\n                                    icon: const Icon(Icons.camera_alt),\n                                    label: const Text('Tirar foto'),\n                                  ),\n"""
    text = replace_once(text, old, new, 'câmera do checklist')
    text = text.replace("label: const Text('Galeria'),", "label: Text(Platform.isWindows ? 'Adicionar foto / arquivo' : 'Galeria'),", 1)
    p.write_text(text, encoding='utf-8')

    # Plano de ação: foto pela câmera só no Android/celular.
    p = app / 'lib' / 'screens' / 'action_detail_screen.dart'
    text = p.read_text(encoding='utf-8')
    old = """              OutlinedButton.icon(\n                onPressed:\n                    afterPaths.length >= 10\n                        ? null\n                        : _takeAfterPhoto,\n                icon: const Icon(Icons.camera_alt),\n                label: const Text('Tirar foto'),\n              ),\n"""
    new = """              if (!Platform.isWindows)\n                OutlinedButton.icon(\n                  onPressed:\n                      afterPaths.length >= 10\n                          ? null\n                          : _takeAfterPhoto,\n                  icon: const Icon(Icons.camera_alt),\n                  label: const Text('Tirar foto'),\n                ),\n"""
    text = replace_once(text, old, new, 'câmera do plano de ação')
    text = text.replace("label: const Text('Galeria'),", "label: Text(Platform.isWindows ? 'Adicionar foto / arquivo' : 'Galeria'),", 1)
    p.write_text(text, encoding='utf-8')

    # Melhorias: esconder câmera e o espaçamento associado no Windows.
    p = app / 'lib' / 'screens' / 'improvements_screen.dart'
    text = p.read_text(encoding='utf-8')
    old = """                Expanded(\n                  child: OutlinedButton.icon(\n                    onPressed:\n                        () => _pickPhoto(\n                          before: before,\n                          source: ImageSource.camera,\n                        ),\n                    icon: const Icon(Icons.photo_camera_outlined, size: 17),\n                    label: const Text('Câmera'),\n                  ),\n                ),\n                const SizedBox(width: 6),\n"""
    new = """                if (!Platform.isWindows) ...[\n                  Expanded(\n                    child: OutlinedButton.icon(\n                      onPressed:\n                          () => _pickPhoto(\n                            before: before,\n                            source: ImageSource.camera,\n                          ),\n                      icon: const Icon(Icons.photo_camera_outlined, size: 17),\n                      label: const Text('Câmera'),\n                    ),\n                  ),\n                  const SizedBox(width: 6),\n                ],\n"""
    text = replace_once(text, old, new, 'câmera de melhorias')
    text = text.replace("label: const Text('Galeria'),", "label: Text(Platform.isWindows ? 'Adicionar foto / arquivo' : 'Galeria'),", 1)
    p.write_text(text, encoding='utf-8')

    # Extintores: câmera só no celular; arquivo/foto no PC.
    p = app / 'lib' / 'screens' / 'extinguishers_screen.dart'
    text = p.read_text(encoding='utf-8')
    old = """                Expanded(\n                  child: OutlinedButton.icon(\n                    onPressed: () => _pickPhoto(ImageSource.camera),\n                    icon: const Icon(Icons.photo_camera_outlined),\n                    label: const Text('Tirar foto'),\n                  ),\n                ),\n                const SizedBox(width: 8),\n"""
    new = """                if (!Platform.isWindows) ...[\n                  Expanded(\n                    child: OutlinedButton.icon(\n                      onPressed: () => _pickPhoto(ImageSource.camera),\n                      icon: const Icon(Icons.photo_camera_outlined),\n                      label: const Text('Tirar foto'),\n                    ),\n                  ),\n                  const SizedBox(width: 8),\n                ],\n"""
    text = replace_once(text, old, new, 'câmera de extintores')
    text = text.replace("label: const Text('Galeria'),", "label: Text(Platform.isWindows ? 'Adicionar foto / arquivo' : 'Galeria'),", 1)
    p.write_text(text, encoding='utf-8')

    # Atos e condições inseguras: câmera só no celular.
    p = app / 'lib' / 'screens' / 'safety_observations_screen.dart'
    text = p.read_text(encoding='utf-8')
    old = """                Expanded(\n                  child: OutlinedButton.icon(\n                    onPressed: () => _pickPhoto(ImageSource.camera),\n                    icon: const Icon(Icons.photo_camera_outlined),\n                    label: const Text('Câmera'),\n                  ),\n                ),\n                const SizedBox(width: 8),\n"""
    new = """                if (!Platform.isWindows) ...[\n                  Expanded(\n                    child: OutlinedButton.icon(\n                      onPressed: () => _pickPhoto(ImageSource.camera),\n                      icon: const Icon(Icons.photo_camera_outlined),\n                      label: const Text('Câmera'),\n                    ),\n                  ),\n                  const SizedBox(width: 8),\n                ],\n"""
    text = replace_once(text, old, new, 'câmera de observações')
    text = text.replace("label: const Text('Galeria'),", "label: Text(Platform.isWindows ? 'Adicionar foto / arquivo' : 'Galeria'),", 1)
    p.write_text(text, encoding='utf-8')

    # Assinatura em tela cheia é recurso de campo/celular. Assinatura normal,
    # Gov.br e sem assinatura continuam disponíveis no Windows.
    p = app / 'lib' / 'screens' / 'signature_screen.dart'
    text = p.read_text(encoding='utf-8')
    old = """            SizedBox(\n              width: double.infinity,\n              child: FilledButton.tonalIcon(\n                onPressed: () => _openFullScreenSignature(\n                  controller: controller,\n                  title: title,\n                ),\n                icon: const Icon(Icons.fullscreen),\n                label: const Text('Assinar em tela cheia'),\n              ),\n            ),\n            const SizedBox(height: 8),\n"""
    new = """            if (Platform.isAndroid) ...[\n              SizedBox(\n                width: double.infinity,\n                child: FilledButton.tonalIcon(\n                  onPressed: () => _openFullScreenSignature(\n                    controller: controller,\n                    title: title,\n                  ),\n                  icon: const Icon(Icons.fullscreen),\n                  label: const Text('Assinar em tela cheia'),\n                ),\n              ),\n              const SizedBox(height: 8),\n            ],\n"""
    text = replace_once(text, old, new, 'assinatura em tela cheia')
    p.write_text(text, encoding='utf-8')

    # Relatórios: no Windows a ação principal passa a ser Salvar PDF. No Android
    # permanece Gerar/compartilhar + salvar no aparelho.
    p = app / 'lib' / 'screens' / 'report_screen.dart'
    text = p.read_text(encoding='utf-8')
    if "import 'dart:io';" not in text:
        text = "import 'dart:io';\n\n" + text
    old = """            Row(\n              children: [\n                Expanded(\n                  child: FilledButton.icon(\n                    onPressed: pdfBusy ? null : onShare,\n                    icon: const Icon(Icons.picture_as_pdf_outlined),\n                    label: Text(\n                      pdfBusy ? 'Gerando...' : 'Gerar / compartilhar',\n                    ),\n                    style: FilledButton.styleFrom(\n                      backgroundColor: AuditarBrand.greenDark,\n                      padding: const EdgeInsets.symmetric(vertical: 13),\n                    ),\n                  ),\n                ),\n                const SizedBox(width: 8),\n                IconButton.outlined(\n                  tooltip: 'Salvar no aparelho',\n                  onPressed: onSave,\n                  icon: const Icon(Icons.download_outlined),\n                ),\n              ],\n            ),\n"""
    new = """            Row(\n              children: [\n                Expanded(\n                  child: FilledButton.icon(\n                    onPressed: pdfBusy ? null : (Platform.isWindows ? onSave : onShare),\n                    icon: Icon(Platform.isWindows ? Icons.download_outlined : Icons.picture_as_pdf_outlined),\n                    label: Text(\n                      pdfBusy\n                          ? 'Gerando...'\n                          : Platform.isWindows\n                              ? 'Salvar PDF'\n                              : 'Gerar / compartilhar',\n                    ),\n                    style: FilledButton.styleFrom(\n                      backgroundColor: AuditarBrand.greenDark,\n                      padding: const EdgeInsets.symmetric(vertical: 13),\n                    ),\n                  ),\n                ),\n                if (!Platform.isWindows) ...[\n                  const SizedBox(width: 8),\n                  IconButton.outlined(\n                    tooltip: 'Salvar no aparelho',\n                    onPressed: onSave,\n                    icon: const Icon(Icons.download_outlined),\n                  ),\n                ],\n              ],\n            ),\n"""
    text = replace_once(text, old, new, 'ações de relatório no PC')
    p.write_text(text, encoding='utf-8')

    # Central Windows: Campo rápido deixa de ser botão destacado no topo.
    # Continua disponível na navegação normal, portanto não perdemos a função.
    p = app / 'lib' / 'screens' / 'home_screen.dart'
    text = p.read_text(encoding='utf-8')
    text = text.replace("icon: const Icon(Icons.add_a_photo_outlined),", "icon: Icon(Platform.isWindows ? Icons.add_task_rounded : Icons.add_a_photo_outlined),", 1)
    old = """              Padding(\n                padding: const EdgeInsets.fromLTRB(14, 0, 14, 10),\n                child: SizedBox(\n                  width: double.infinity,\n                  child: OutlinedButton.icon(\n                    onPressed: () => _open(const FieldQuickScreen()),\n                    icon: const Icon(Icons.location_on_outlined),\n                    label: const Text('Campo rápido'),\n                  ),\n                ),\n              ),\n"""
    new = """              if (!Platform.isWindows)\n                Padding(\n                  padding: const EdgeInsets.fromLTRB(14, 0, 14, 10),\n                  child: SizedBox(\n                    width: double.infinity,\n                    child: OutlinedButton.icon(\n                      onPressed: () => _open(const FieldQuickScreen()),\n                      icon: const Icon(Icons.location_on_outlined),\n                      label: const Text('Campo rápido'),\n                    ),\n                  ),\n                ),\n"""
    text = replace_once(text, old, new, 'destaque do Campo rápido no Windows')
    text = text.replace('Auditar SST • versão 3.36.0', 'Auditar SST • versão 3.36.1')
    text = text.replace('Auditar SST para Windows • versão 3.36.0', 'Auditar SST para Windows • versão 3.36.1')
    p.write_text(text, encoding='utf-8')

    # Preservações essenciais.
    checks = {
        'versão': 'version: 3.36.1+156' in pub.read_text(encoding='utf-8'),
        'sync v2': "'syncProtocol': 2" in (app / 'lib' / 'services' / 'device_sync_service.dart').read_text(encoding='utf-8'),
        '44 checklists': (app / 'lib' / 'ready_checklists.dart').read_text(encoding='utf-8').count('  ReadyChecklistDefinition(') == 44,
        'assinatura Android preservada': "if (Platform.isAndroid) ...[" in (app / 'lib' / 'screens' / 'signature_screen.dart').read_text(encoding='utf-8') and 'Assinar em tela cheia' in (app / 'lib' / 'screens' / 'signature_screen.dart').read_text(encoding='utf-8'),
        'campo rápido preservado': 'FieldQuickScreen' in (app / 'lib' / 'screens' / 'home_screen.dart').read_text(encoding='utf-8'),
        'relatório Windows': "? 'Salvar PDF'" in (app / 'lib' / 'screens' / 'report_screen.dart').read_text(encoding='utf-8'),
        'company_units': 'company_units' in (app / 'lib' / 'database.dart').read_text(encoding='utf-8'),
    }
    missing = [name for name, ok in checks.items() if not ok]
    if missing:
        raise RuntimeError('Validações v3.36.1 falharam: ' + ', '.join(missing))

    print(f'Fonte v3.36.1 PC enxuto montada em {app}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
