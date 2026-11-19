#!/usr/bin/env python3
"""Regressão de rotas sem Flutter, sem banco e sem rede."""
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from home_visit_routing_20261119 import reroute_home_new_inspections


class HomeVisitRoutingTests(unittest.TestCase):
    def test_android_home_multiline_routes(self):
        original = """
          onPressed:
              () => _open(
                const NewInspectionScreen(),
                tutorialId: 'new_inspection',
              ),
          onPressed: () => _open(
                        const NewInspectionScreen(),
                        tutorialId: 'new_inspection',
                      ),
        """
        patched, count = reroute_home_new_inspections(original)
        self.assertEqual(2, count)
        self.assertEqual(2, patched.count('const AuditarVisitTypeChooserScreen()'))
        self.assertEqual(2, patched.count("tutorialId: 'new_inspection'"))
        self.assertNotIn('const NewInspectionScreen()', patched)

    def test_inline_route_preserves_unrelated_navigation(self):
        original = (
            '() => _open(const NewInspectionScreen(), tutorialId: "new_inspection")\n'
            '() => Navigator.push(context, NewInspectionScreen())\n'
        )
        patched, count = reroute_home_new_inspections(original)
        self.assertEqual(1, count)
        self.assertIn('const AuditarVisitTypeChooserScreen()', patched)
        self.assertIn('Navigator.push(context, NewInspectionScreen())', patched)

    def test_unknown_home_fails_closed(self):
        with self.assertRaisesRegex(RuntimeError, '0'):
            reroute_home_new_inspections('_open(const SettingsScreen())')

    def test_more_than_four_routes_fails_closed(self):
        src = '_open(const NewInspectionScreen(), tutorialId: "new_inspection")\n'
        with self.assertRaisesRegex(RuntimeError, '5'):
            reroute_home_new_inspections(src * 5)

    def test_other_tutorial_routes_are_not_rewritten(self):
        with self.assertRaisesRegex(RuntimeError, '0'):
            reroute_home_new_inspections(
                '_open(const NewInspectionScreen(), tutorialId: "other")'
            )


if __name__ == '__main__':
    unittest.main()
