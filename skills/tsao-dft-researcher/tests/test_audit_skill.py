from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


class AuditSkillTests(unittest.TestCase):
    def test_package_static_audit_passes(self) -> None:
        skill = Path(__file__).resolve().parents[1]
        script = skill / "scripts" / "audit_skill.py"
        result = subprocess.run(
            [sys.executable, str(script), str(skill), "--json"],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('"ok": true', result.stdout)


if __name__ == "__main__":
    unittest.main()
