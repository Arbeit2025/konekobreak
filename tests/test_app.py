import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import app as app_module  # noqa: E402


class KonekoBreakTest(unittest.TestCase):
    def setUp(self):
        self.client = app_module.app.test_client()

    def test_healthz(self):
        res = self.client.get("/healthz")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json(), {"status": "ok"})

    def test_index_ok_and_title(self):
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)
        self.assertIn("こねこ休憩リマインダー", html)

    def test_index_has_presets_and_controls(self):
        html = self.client.get("/").get_data(as_text=True)
        for minutes in (25, 50, 90):
            self.assertIn(f'data-minutes="{minutes}"', html)
            self.assertIn(f"{minutes}分", html)
        self.assertIn('id="customMinutes"', html)
        self.assertIn('id="setCustom"', html)
        self.assertIn('id="startBtn"', html)
        self.assertIn("開始", html)
        self.assertIn('id="pauseBtn"', html)
        self.assertIn("一時停止", html)
        self.assertIn('id="resetBtn"', html)
        self.assertIn("リセット", html)
        self.assertIn('id="timer"', html)

    def test_index_has_cat(self):
        html = self.client.get("/").get_data(as_text=True)
        self.assertIn("🐱", html)
        self.assertIn('id="speech"', html)

    def test_preset_minutes_value(self):
        self.assertEqual(app_module.PRESET_MINUTES, [25, 50, 90])

    def test_break_messages_multiple_and_embedded(self):
        self.assertGreaterEqual(len(app_module.BREAK_MESSAGES), 5)
        html = self.client.get("/").get_data(as_text=True)
        for msg in app_module.BREAK_MESSAGES:
            self.assertIn(msg, html)

    def test_work_quotes_multiple_and_embedded(self):
        self.assertGreaterEqual(len(app_module.WORK_QUOTES), 3)
        html = self.client.get("/").get_data(as_text=True)
        for quote in app_module.WORK_QUOTES:
            self.assertIn(quote, html)


if __name__ == "__main__":
    unittest.main()
