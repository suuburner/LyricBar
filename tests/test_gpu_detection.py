import subprocess
import unittest
from unittest.mock import patch

from LyricBar.utils.gpu import detect_gpu_info


class GpuDetectionTests(unittest.TestCase):
    def test_detect_gpu_info_returns_empty_when_tools_missing(self):
        with patch("subprocess.run", side_effect=FileNotFoundError("wmic not found")):
            self.assertEqual(detect_gpu_info(), [])

    def test_detect_gpu_info_parses_names_from_output(self):
        fake_result = subprocess.CompletedProcess(args=[], returncode=0, stdout="Name\nNVIDIA GeForce RTX 4070\n", stderr="")
        with patch("subprocess.run", return_value=fake_result):
            self.assertEqual(detect_gpu_info(), ["NVIDIA GeForce RTX 4070"])


if __name__ == "__main__":
    unittest.main()
