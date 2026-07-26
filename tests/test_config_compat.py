import os
import tempfile
import unittest
from pathlib import Path

import yaml

from LyricBar import config as config_module


class ConfigCompatTests(unittest.TestCase):
    def setUp(self):
        self._cwd = Path.cwd()
        self._tmpdir = tempfile.TemporaryDirectory()
        os.chdir(self._tmpdir.name)

    def tearDown(self):
        os.chdir(self._cwd)
        self._tmpdir.cleanup()

    def test_update_and_persist_refreshes_runtime_settings(self):
        settings = config_module.settings

        settings.update_and_persist({
            "Themes": {"Default": "Everforest"},
            "Display": {"Progress Bar": False},
        })

        self.assertEqual(settings.default_theme, "Everforest")
        self.assertFalse(settings.show_progress_bar)

        settings_path = Path("settings.yaml")
        self.assertTrue(settings_path.exists())
        persisted = yaml.safe_load(settings_path.read_text(encoding="utf-8"))
        self.assertEqual(persisted["Themes"]["Default"], "Everforest")
        self.assertFalse(persisted["Display"]["Progress Bar"])


if __name__ == "__main__":
    unittest.main()
