import sys
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from crimesense_ai.analyzer import analyze_complaint


class OfflineProvider:
    available = False
    unavailable_reason = "offline smoke test"
    engine_name = "local_fallback"


class CrimeSenseSmokeTest(unittest.TestCase):
    def test_hinglish_upi_fraud_pipeline(self):
        report = analyze_complaint(
            "Mujhe KYC update ke naam par fake link bheja gaya aur OTP maang kar Rs. 55000 nikal liye. UPI ID scammer@paytm tha.",
            provider=OfflineProvider(),
        )

        self.assertEqual(report["priority"], "High")
        self.assertEqual(report["language"], "Hinglish")
        self.assertIn("Rs. 55000", report["entities"]["amounts"])
        self.assertIn("scammer@paytm", report["entities"]["upi_ids"])
        self.assertIn("preprocessing", report)

    def test_repeated_otp_count_extraction(self):
        report = analyze_complaint(
            "i am getting 100 otps daily without my consent",
            provider=OfflineProvider(),
        )

        self.assertIn("100 otps daily", report["entities"]["counts"])


if __name__ == "__main__":
    result = unittest.main(exit=False)
    if not result.result.wasSuccessful():
        raise SystemExit(1)
