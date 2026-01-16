from datetime import datetime

from main import filter_threads_for_replies


# Mock constant in config if necessary, or patch it
def test_filter_threads(mock_thread_list):
    candidates = filter_threads_for_replies(mock_thread_list, days_threshold=7)

    # Input has 3 threads:
    # 1. Active, Recent (1 day ago) -> Should be ignored (Threshold <= 7 means "Recent is < 7 days old"??)
    #    Wait, Logic says: if days_ago <= DAYS_THRESHOLD: print "No reply needed yet".
    #    So we ONLY reply if activity is OLDER than X days?
    #    Let's check code: "if days_ago <= DAYS_THRESHOLD: continue"
    #    So YES, we reply to OLD inactive threads? Or is the logic inverted?
    #    Usually "Auto-Reply to neglected threads".

    # Thread 1: 1 day ago. 1 <= 7. IGNORED.
    # Thread 2: 20 days ago. 20 > 7. CANDIDATE.
    # Thread 3: No Active flag. IGNORED.

    assert len(candidates) == 1
    assert candidates[0]["subject"] == "Active Old"


def test_filter_threads_edge_case():
    """Test that threads exactly at the threshold boundary are NOT processed (boundary is inclusive)."""
    from datetime import timedelta

    now = datetime.now()
    # Thread exactly 7 days old (should NOT be processed - boundary is inclusive)
    thread_at_boundary = [
        {
            "id": "boundary",
            "subject": "Boundary Test",
            "flag_status": "Active",
            "timestamp": now - timedelta(days=7),
            "content": "Exactly 7 days old",
            "message_id": "msgB",
        }
    ]

    candidates = filter_threads_for_replies([thread_at_boundary], days_threshold=7)

    # 7 <= 7 means it's still "recent" and should be ignored
    assert len(candidates) == 0
