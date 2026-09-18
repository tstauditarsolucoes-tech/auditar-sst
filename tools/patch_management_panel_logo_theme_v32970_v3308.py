#!/usr/bin/env python3
from pathlib import Path
import re
import sys

root = Path(sys.argv[1])
platform = sys.argv[2].strip().lower()
if platform not in {'android','windows'}:
    raise SystemExit('Uso: patch_management_panel_logo_theme_v32970_v3308.py <app> <android|windows>')

pubp = root/'pubspec.yaml'
screenp = root/'lib/screens/management_panel_screen.dart'

pub = pubp.read_text(encoding='utf-8')
screen = screenp.read_text(encoding='utf-8')

target = '3.29.70+212' if platform == 'android' else '3.30.8+195'
pub, n = re.subn(r'^version:\s*[^\n]+', 'version: '+target, pub, count=1, flags=re.M)
if n != 1:
    raise RuntimeError('Versão não localizada')

if "import 'dart:io';" not in screen:
    screen = "import 'dart:io';\nimport 'dart:ui' as ui;\n\n" + screen
elif "import 'dart:ui' as ui;" not in screen:
    screen = screen.replace("import 'dart:io';\n", "import 'dart:io';\nimport 'dart:ui' as ui;\n", 1)

state_marker = "  List<SstRecord> trainingRecords = [];\n"
state_new = """  List<SstRecord> trainingRecords = [];
  Color companyAccent = AuditarBrand.navy;
  Color companyAccentDark = AuditarBrand.navyDark;
  bool companyIdentityLoaded = false;
"""
if "Color companyAccent = AuditarBrand.navy;" not in screen:
    if state_marker not in screen:
        raise RuntimeError('Estado do tema da empresa não localizado')
    screen = screen.replace(state_marker, state_new, 1)

init_old = """  void initState() {
    super.initState();
    _load();
  }
"""
init_new = """  void initState() {
    super.initState();
    _load();
    _loadCompanyIdentity();
  }
"""
if "_loadCompanyIdentity();" not in screen:
    if init_old not in screen:
        raise RuntimeError('initState não localizado')
    screen = screen.replace(init_old, init_new, 1)

helper_anchor = """  Future<void> _load() async {
"""
helpers = r'''  Color get _companyHeaderColor {
    final hsl = HSLColor.fromColor(companyAccent);
    return hsl
        .withSaturation(hsl.saturation.clamp(.18, .88).toDouble())
        .withLightness(hsl.lightness.clamp(.20, .37).toDouble())
        .toColor();
  }

  Color get _companyHeaderDark {
    final hsl = HSLColor.fromColor(companyAccentDark);
    return hsl
        .withSaturation(hsl.saturation.clamp(.16, .90).toDouble())
        .withLightness(hsl.lightness.clamp(.10, .25).toDouble())
        .toColor();
  }

  Color get _companySoft => companyAccent.withValues(alpha: .08);

  Color get _companySoftStrong => companyAccent.withValues(alpha: .14);

  String get _companyLogoPath => (widget.company.logoPath ?? '').trim();

  bool get _hasCompanyLogo =>
      _companyLogoPath.isNotEmpty && File(_companyLogoPath).existsSync();

  Future<void> _loadCompanyIdentity() async {
    Color accent = AuditarBrand.navy;
    Color dark = AuditarBrand.navyDark;

    final path = _companyLogoPath;
    if (path.isNotEmpty) {
      try {
        final file = File(path);
        if (await file.exists()) {
          final bytes = await file.readAsBytes();
          final codec = await ui.instantiateImageCodec(
            bytes,
            targetWidth: 56,
            targetHeight: 56,
          );
          final frame = await codec.getNextFrame();
          final image = frame.image;
          final data = await image.toByteData(
            format: ui.ImageByteFormat.rawRgba,
          );

          if (data != null) {
            final counts = <int, int>{};
            for (var i = 0; i + 3 < data.lengthInBytes; i += 4) {
              final r = data.getUint8(i);
              final g = data.getUint8(i + 1);
              final b = data.getUint8(i + 2);
              final a = data.getUint8(i + 3);
              if (a < 170) continue;

              final maxChannel = [r, g, b].reduce((a, b) => a > b ? a : b);
              final minChannel = [r, g, b].reduce((a, b) => a < b ? a : b);

              // Ignora fundo branco/transparente e preto puro de textos.
              if (minChannel > 238) continue;
              if (maxChannel < 28) continue;

              final spread = maxChannel - minChannel;
              final key = ((r >> 4) << 8) | ((g >> 4) << 4) | (b >> 4);
              final colorWeight = 1 + (spread ~/ 36);
              counts[key] = (counts[key] ?? 0) + colorWeight;
            }

            if (counts.isNotEmpty) {
              final selected = counts.entries.reduce(
                (a, b) => a.value >= b.value ? a : b,
              ).key;
              final r = (((selected >> 8) & 0xF) << 4) + 8;
              final g = (((selected >> 4) & 0xF) << 4) + 8;
              final b = ((selected & 0xF) << 4) + 8;
              final candidate = Color.fromARGB(255, r, g, b);
              final hsl = HSLColor.fromColor(candidate);

              if (hsl.saturation >= .10) {
                accent = hsl
                    .withSaturation(hsl.saturation.clamp(.32, .88).toDouble())
                    .withLightness(hsl.lightness.clamp(.30, .54).toDouble())
                    .toColor();
                dark = hsl
                    .withSaturation(hsl.saturation.clamp(.26, .90).toDouble())
                    .withLightness(hsl.lightness.clamp(.16, .30).toDouble())
                    .toColor();
              }
            }
          }
          image.dispose();
          codec.dispose();
        }
      } catch (_) {
        // A identidade visual nunca impede o Painel Gerencial de abrir.
      }
    }

    if (!mounted) return;
    setState(() {
      companyAccent = accent;
      companyAccentDark = dark;
      companyIdentityLoaded = true;
    });
  }

  Widget _companyLogoWidget({
    double size = 58,
  }) {
    if (!_hasCompanyLogo) {
      return Container(
        width: size,
        height: size,
        decoration: BoxDecoration(
          color: Colors.white.withValues(alpha: .14),
          borderRadius: BorderRadius.circular(15),
        ),
        child: const Icon(
          Icons.monitor_heart_outlined,
          color: Colors.white,
          size: 30,
        ),
      );
    }

    return Container(
      width: size,
      height: size,
      padding: const EdgeInsets.all(6),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(15),
        boxShadow: const [
          BoxShadow(
            color: Color(0x24000000),
            blurRadius: 10,
            offset: Offset(0, 3),
          ),
        ],
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(10),
        child: Image.file(
          File(_companyLogoPath),
          fit: BoxFit.contain,
          errorBuilder: (_, __, ___) => Icon(
            Icons.apartment_rounded,
            color: companyAccent,
            size: 30,
          ),
        ),
      ),
    );
  }

  ThemeData _companyPanelTheme(BuildContext context) {
    final base = Theme.of(context);
    final scheme = base.colorScheme.copyWith(
      primary: companyAccent,
      secondary: companyAccentDark,
    );
    return base.copyWith(
      colorScheme: scheme,
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          backgroundColor: companyAccent,
          foregroundColor:
              companyAccent.computeLuminance() > .56 ? Colors.black : Colors.white,
        ),
      ),
      progressIndicatorTheme: ProgressIndicatorThemeData(
        color: companyAccent,
        linearTrackColor: companyAccent.withValues(alpha: .14),
      ),
    );
  }

'''
if "Future<void> _loadCompanyIdentity() async" not in screen:
    if helper_anchor not in screen:
        raise RuntimeError('Âncora de helpers não localizada')
    screen = screen.replace(helper_anchor, helpers + helper_anchor, 1)

# Theme local ao Painel Gerencial.
old_return = """    return Scaffold(
      appBar: AppBar(title: const Text('Painel Gerencial')),
"""
new_return = """    return Theme(
      data: _companyPanelTheme(context),
      child: Scaffold(
        appBar: AppBar(title: const Text('Painel Gerencial')),
"""
if "data: _companyPanelTheme(context)," not in screen:
    if old_return not in screen:
        raise RuntimeError('Scaffold do painel não localizado')
    screen = screen.replace(old_return, new_return, 1)

old_end = """            ),
    );
  }

  Widget _header() {
"""
new_end = """            ),
      ),
    );
  }

  Widget _header() {
"""
if "child: Scaffold(" in screen and new_end not in screen:
    if old_end not in screen:
        raise RuntimeError('Fechamento do Scaffold não localizado')
    screen = screen.replace(old_end, new_end, 1)

# Cabeçalho com gradiente derivado da logo e logo real.
old_gradient = """        gradient: const LinearGradient(
          colors: [AuditarBrand.navy, AuditarBrand.navyDark],
        ),
"""
new_gradient = """        gradient: LinearGradient(
          colors: [_companyHeaderColor, _companyHeaderDark],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
"""
if "colors: [_companyHeaderColor, _companyHeaderDark]" not in screen:
    if old_gradient not in screen:
        raise RuntimeError('Gradiente do cabeçalho não localizado')
    screen = screen.replace(old_gradient, new_gradient, 1)

old_icon = """              Container(
                width: 48,
                height: 48,
                decoration: BoxDecoration(
                  color: Colors.white12,
                  borderRadius: BorderRadius.circular(14),
                ),
                child: const Icon(
                  Icons.monitor_heart_outlined,
                  color: AuditarBrand.green,
                  size: 28,
                ),
              ),
"""
if "_companyLogoWidget()" not in screen:
    if old_icon not in screen:
        raise RuntimeError('Ícone do cabeçalho não localizado')
    screen = screen.replace(old_icon, "              _companyLogoWidget(),\n", 1)

# Status ativo com identidade da empresa, mantendo contraste.
old_status = """                  color: enabled ? AuditarBrand.green : Colors.white24,
"""
new_status = """                  color: enabled
                      ? Colors.white.withValues(alpha: .94)
                      : Colors.white24,
"""
if "Colors.white.withValues(alpha: .94)" not in screen:
    screen = screen.replace(old_status, new_status, 1)

old_status_text = """                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 10,
                    fontWeight: FontWeight.w800,
                  ),
"""
new_status_text = """                  style: TextStyle(
                    color: enabled ? _companyHeaderColor : Colors.white,
                    fontSize: 10,
                    fontWeight: FontWeight.w900,
                  ),
"""
if "color: enabled ? _companyHeaderColor" not in screen:
    screen = screen.replace(old_status_text, new_status_text, 1)

# Marca sutil sob o subtítulo.
old_subtitle = """                    const Text(
                      'Acompanhamento gerencial SST',
                      style: TextStyle(color: Colors.white70, fontSize: 12),
                    ),
"""
new_subtitle = """                    Row(
                      children: [
                        const Text(
                          'Acompanhamento gerencial SST',
                          style: TextStyle(
                            color: Colors.white70,
                            fontSize: 12,
                          ),
                        ),
                        if (_hasCompanyLogo) ...[
                          const SizedBox(width: 7),
                          Container(
                            width: 5,
                            height: 5,
                            decoration: const BoxDecoration(
                              color: Colors.white70,
                              shape: BoxShape.circle,
                            ),
                          ),
                          const SizedBox(width: 7),
                          const Text(
                            'identidade da empresa',
                            style: TextStyle(
                              color: Colors.white54,
                              fontSize: 10.5,
                            ),
                          ),
                        ],
                      ],
                    ),
"""
if "'identidade da empresa'" not in screen:
    if old_subtitle not in screen:
        raise RuntimeError('Subtítulo do cabeçalho não localizado')
    screen = screen.replace(old_subtitle, new_subtitle, 1)

# Cores de identidade para seções neutras e sucessos; alertas vermelho/laranja permanecem.
screen = screen.replace(
"""                  const Text(
                    'O que a gerência acompanha',
                    style: TextStyle(
                      color: AuditarBrand.navy,
""",
"""                  Text(
                    'O que a gerência acompanha',
                    style: TextStyle(
                      color: companyAccentDark,
""",
1,
)

screen = screen.replace(
"""                        AuditarBrand.greenDark,
""",
"""                        companyAccent,
""",
1,
)

# Card da IA assume a identidade sem perder leitura.
screen = screen.replace(
"""                  Card(
                    color: AuditarBrand.navy.withValues(alpha: .05),
""",
"""                  Card(
                    color: _companySoft,
""",
1,
)
screen = screen.replace(
"""                          const Row(
                            children: [
                              Icon(
                                Icons.auto_awesome_rounded,
                                color: AuditarBrand.navy,
                              ),
""",
"""                          Row(
                            children: [
                              Icon(
                                Icons.auto_awesome_rounded,
                                color: companyAccent,
                              ),
""",
1,
)
screen = screen.replace(
"""                                  style: TextStyle(
                                    color: AuditarBrand.navy,
""",
"""                                  style: TextStyle(
                                    color: companyAccentDark,
""",
1,
)

# Desempenho por setor.
screen = screen.replace(
"""                      const Expanded(
                        child: Text(
                          'Desempenho por setor',
                          style: TextStyle(
                            color: AuditarBrand.navy,
""",
"""                      Expanded(
                        child: Text(
                          'Desempenho por setor',
                          style: TextStyle(
                            color: companyAccentDark,
""",
1,
)

# Privacidade com identidade visual.
screen = screen.replace(
"""                  const Card(
                    child: Padding(
                      padding: EdgeInsets.all(14),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Icon(Icons.privacy_tip_outlined, color: AuditarBrand.navy),
""",
"""                  Card(
                    child: Padding(
                      padding: const EdgeInsets.all(14),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Icon(
                            Icons.privacy_tip_outlined,
                            color: companyAccent,
                          ),
""",
1,
)
screen = screen.replace(
"""                          SizedBox(width: 10),
                          Expanded(
                            child: Text(
""",
"""                          const SizedBox(width: 10),
                          const Expanded(
                            child: Text(
""",
1,
)

# Link configurado passa a usar a identidade da empresa quando positivo.
screen = screen.replace(
"""                  color: configured ? AuditarBrand.greenDark : const Color(0xFFF29D18),
""",
"""                  color: configured ? companyAccent : const Color(0xFFF29D18),
""",
1,
)
screen = screen.replace(
"""                      color: AuditarBrand.navy,
""",
"""                      color: companyAccentDark,
""",
1,
)

# Card de treinamentos inserido na versão anterior.
screen = screen.replace(
"""                    color: AuditarBrand.green.withValues(alpha: .12),
""",
"""                    color: _companySoftStrong,
""",
1,
)
screen = screen.replace(
"""                    color: AuditarBrand.greenDark,
""",
"""                    color: companyAccent,
""",
1,
)
screen = screen.replace(
"""                          color: AuditarBrand.navy,
                          fontSize: 16,
""",
"""                          color: companyAccentDark,
                          fontSize: 16,
""",
1,
)
screen = screen.replace(
"""                    color: AuditarBrand.navy.withValues(alpha: .04),
""",
"""                    color: _companySoft,
""",
1,
)
screen = screen.replace(
"""                      color: AuditarBrand.navy.withValues(alpha: .08),
""",
"""                      color: companyAccent.withValues(alpha: .12),
""",
1,
)
screen = screen.replace(
"""                        color: AuditarBrand.navy,
""",
"""                        color: companyAccent,
""",
1,
)
screen = screen.replace(
"""                            ? AuditarBrand.green.withValues(alpha: .06)
                            : AuditarBrand.navy.withValues(alpha: .035),
""",
"""                            ? companyAccent.withValues(alpha: .07)
                            : companyAccent.withValues(alpha: .035),
""",
1,
)
screen = screen.replace(
"""                              ? AuditarBrand.green.withValues(alpha: .16)
                              : AuditarBrand.navy.withValues(alpha: .08),
""",
"""                              ? companyAccent.withValues(alpha: .18)
                              : companyAccent.withValues(alpha: .10),
""",
1,
)
screen = screen.replace(
"""                                ? AuditarBrand.green.withValues(alpha: .13)
""",
"""                                ? companyAccent.withValues(alpha: .13)
""",
1,
)
screen = screen.replace(
"""                                ? AuditarBrand.greenDark
""",
"""                                ? companyAccent
""",
1,
)

# Métricas pequenas do treinamento.
screen = screen.replace(
"""        color: AuditarBrand.navy.withValues(alpha: .035),
""",
"""        color: companyAccent.withValues(alpha: .045),
""",
1,
)
screen = screen.replace(
"""          Icon(icon, size: 18, color: AuditarBrand.navy),
""",
"""          Icon(icon, size: 18, color: companyAccent),
""",
1,
)
screen = screen.replace(
"""                    color: AuditarBrand.navy,
""",
"""                    color: companyAccentDark,
""",
1,
)

# Cores derivadas da logo são calculadas em runtime; widgets que eram const
# no layout antigo deixam de ser const apenas dentro desta tela.
screen = screen.replace('child: const Icon(', 'child: Icon(')
screen = screen.replace('const Expanded(', 'Expanded(')
screen = screen.replace('child: const Row(', 'child: Row(')
screen = screen.replace('style: const TextStyle(', 'style: TextStyle(')

pubp.write_text(pub, encoding='utf-8')
screenp.write_text(screen, encoding='utf-8')

assert 'version: '+target in pubp.read_text(encoding='utf-8')
assert 'Future<void> _loadCompanyIdentity() async' in screen
assert 'ui.instantiateImageCodec' in screen
assert '_companyLogoWidget()' in screen
assert 'colors: [_companyHeaderColor, _companyHeaderDark]' in screen
assert 'data: _companyPanelTheme(context)' in screen
assert "'identidade da empresa'" in screen
print('MANAGEMENT_PANEL_LOGO_THEME_OK', target, platform)
