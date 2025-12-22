import pytest
import os
import sys

# Ensure 'src' is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

@pytest.fixture
def mock_raw_applescript_output():
    """Returns a sample string mimicking the output of get_flagged_threads.scpt"""
    # Important: Check config.py for MSG_DELIMITER. Usually "===END_MSG==="
    return """ID: 101
From: sender@example.com
Date: Thursday, December 18, 2025 at 12:45:49 PM
Subject: Re: Project Update
FlagStatus: Active
MessageID: <123@example.com>
---BODY_START---
This is the email body.
It has multiple lines.
---BODY_END---
///END_OF_MESSAGE///
ID: 102
From: boss@example.com
Date: Friday, December 19, 2025 at 09:00:00 AM
Subject: Urgent meeting
FlagStatus: Active
MessageID: <456@example.com>
---BODY_START---
Please reply asap.
---BODY_END---
///END_OF_MESSAGE///
"""

@pytest.fixture
def mock_thread_list():
    """Returns a pre-parsed list of threads for logic testing"""
    from datetime import datetime, timedelta
    now = datetime.now()
    
    # Thread 1: Active, Recent
    t1 = [{
        "id": "1",
        "subject": "Active Recent",
        "flag_status": "Active",
        "timestamp": now - timedelta(days=1),
        "content": "Recent message",
        "message_id": "msg1"
    }]
    
    # Thread 2: Active, Old
    t2 = [{
        "id": "2",
        "subject": "Active Old",
        "flag_status": "Active",
        "timestamp": now - timedelta(days=20),
        "content": "Old message",
        "message_id": "msg2"
    }]
    
    # Thread 3: No Active Flag
    t3 = [{
        "id": "3",
        "subject": "Completed",
        "flag_status": "Completed",
        "timestamp": now - timedelta(days=1),
        "content": "Done",
        "message_id": "msg3"
    }]
    
    return [t1, t2, t3]
