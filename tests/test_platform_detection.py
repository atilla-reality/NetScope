import unittest
from unittest.mock import patch

from netscope.platforms.detector import detect_platform


class PlatformTests(unittest.TestCase):

    @patch("netscope.platforms.detector.os.path.exists")
    @patch("netscope.platforms.detector.os.environ.get")
    def test_ish_detection(self, mock_env, mock_exists):
        mock_env.return_value = None
        mock_exists.side_effect = lambda path: path == "/proc/ish"

        self.assertEqual(detect_platform(), "ish")

    @patch("netscope.platforms.detector.os.path.exists")
    @patch("netscope.platforms.detector.os.environ.get")
    @patch("netscope.platforms.detector.platform.system")
    def test_linux_detection(
        self,
        mock_system,
        mock_env,
        mock_exists,
    ):
        mock_env.return_value = None
        mock_exists.return_value = False
        mock_system.return_value = "Linux"

        self.assertEqual(detect_platform(), "linux")


if __name__ == "__main__":
    unittest.main()
