#!/usr/bin/env python3
"""Contract test for static cross-screen destination inventory."""
from pathlib import Path
from tempfile import TemporaryDirectory
import json
from audit_navigation_destinations_v1 import scan, markdown

with TemporaryDirectory() as tmp:
    root = Path(tmp)
    screens = root / "lib" / "screens"
    screens.mkdir(parents=True)
    (screens / "home_screen.dart").write_text(
        "class HomeScreen extends StatelessWidget {}\n"
        "final a=RecordsScreen();\n"
        "final b=const RecordsScreen();\n", encoding="utf-8")
    (screens / "records_screen.dart").write_text(
        "class RecordsScreen extends StatefulWidget {\n"
        "const RecordsScreen();\n}\n", encoding="utf-8")
    (screens / "worksite_screen.dart").write_text(
        "class WorksiteScreen extends StatelessWidget {}\n"
        "final action=RecordsScreen();\n", encoding="utf-8")
    (screens / "unused_screen.dart").write_text(
        "class UnusedScreen extends StatelessWidget {}\n", encoding="utf-8")
    result = scan(root)
    assert result["screen_files_scanned"] == 4
    assert result["screen_classes_defined"] == 4
    shared = result["targets_referenced_from_multiple_screens"]
    assert len(shared) == 1, shared
    assert shared[0]["destination"] == "RecordsScreen"
    assert shared[0]["file_count"] == 2
    assert shared[0]["occurrences"] == 3
    within = result["targets_repeated_within_one_screen"]
    assert len(within) == 1
    assert within[0]["constructor_count"] == 2
    assert within[0]["source"] == "lib/screens/home_screen.dart"
    assert result["ambiguous_class_definitions"] == []
    assert "não prova" in markdown(result).lower()
    json.dumps(result, ensure_ascii=False)
print("AUDITAR_SHARED_DESTINATION_TEST_OK")
