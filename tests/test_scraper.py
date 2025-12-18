import unittest
import sys
import os

# Add src to path so we can import scraper
sys.path.append(os.path.join(os.getcwd(), 'src'))

from scraper import parse_raw_data, group_into_threads

class TestScraper(unittest.TestCase):
    def test_parse_raw_data(self):
        # Mock raw data simulating AppleScript output
        raw_data = """ID: 123
From: John Doe <john@example.com>
Date: 2025-12-18 10:00:00
Subject: Test Thread
---BODY_START---
This is a test message.
---BODY_END---
///END_OF_MESSAGE///
ID: 123
From: Jane Doe <jane@example.com>
Date: 2025-12-18 11:00:00
Subject: Re: Test Thread
---BODY_START---
This is a reply.
---BODY_END---
///END_OF_MESSAGE///
"""
        messages = parse_raw_data(raw_data)
        self.assertEqual(len(messages), 2)
        
        self.assertEqual(messages[0]['id'], '123')
        self.assertEqual(messages[0]['from'], 'John Doe <john@example.com>')
        self.assertEqual(messages[0]['content'], 'This is a test message.')
        
        self.assertEqual(messages[1]['id'], '123')
        self.assertEqual(messages[1]['content'], 'This is a reply.')

    def test_group_into_threads(self):
        messages = [
            {'id': 'A', 'subject': 'Thread A', 'content': 'Msg 1'},
            {'id': 'B', 'subject': 'Thread B', 'content': 'Msg 2'},
            {'id': 'A', 'subject': 'Re: Thread A', 'content': 'Msg 3'}
        ]
        
        threads = group_into_threads(messages)
        self.assertEqual(len(threads), 2)
        
        # Verify grouping
        # Order depends on implementation, but likely insertion order of keys
        # We expect one thread with 2 messages (ID A) and one with 1 message (ID B)
        
        # Sort by ID to be deterministic in test
        threads.sort(key=lambda t: t[0]['id'])
        
        thread_A = threads[0]
        self.assertEqual(len(thread_A), 2)
        self.assertEqual(thread_A[0]['id'], 'A')
        
        thread_B = threads[1]
        self.assertEqual(len(thread_B), 1)
        self.assertEqual(thread_B[0]['id'], 'B')

    def test_fallback_grouping(self):
        # Test generic fallback when ID is NO_ID
        raw_data = """ID: NO_ID
From: Someone
Date: 2020-01-01
Subject: Important Topic
---BODY_START---
...
---BODY_END---
///END_OF_MESSAGE///
ID: NO_ID
From: Another
Date: 2020-01-02
Subject: Re: Important Topic
---BODY_START---
...
---BODY_END---
///END_OF_MESSAGE///
"""
        messages = parse_raw_data(raw_data)
        self.assertEqual(len(messages), 2)
        # Should have normalized ID to "Important Topic"
        self.assertEqual(messages[0]['id'], 'Important Topic')
        self.assertEqual(messages[1]['id'], 'Important Topic')
        
        threads = group_into_threads(messages)
        self.assertEqual(len(threads), 1)
        self.assertEqual(threads[0][0]['subject'], 'Important Topic')

if __name__ == '__main__':
    unittest.main()
