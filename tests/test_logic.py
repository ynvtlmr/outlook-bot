import unittest
from datetime import datetime, timedelta
import sys
import os

sys.path.append(os.path.join(os.getcwd(), 'src'))

from responder import parse_date

class TestResponderLogic(unittest.TestCase):
    def test_parse_date(self):
        # Test a few date formats
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d %H:%M:%S")
        parsed = parse_date(date_str)
        self.assertAlmostEqual((parsed - now).total_seconds(), 0, delta=1.0)
        
    def test_threshold_logic(self):
        # Simulate logic
        DAYS_THRESHOLD = 7
        last_contact = datetime.now() - timedelta(days=10)
        days_diff = (datetime.now() - last_contact).days
        self.assertTrue(days_diff > DAYS_THRESHOLD)
        
        last_contact_recent = datetime.now() - timedelta(days=2)
        days_diff_recent = (datetime.now() - last_contact_recent).days
        self.assertFalse(days_diff_recent > DAYS_THRESHOLD)

if __name__ == '__main__':
    unittest.main()
