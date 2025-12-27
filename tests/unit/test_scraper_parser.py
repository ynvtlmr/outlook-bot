from scraper import group_into_threads, parse_raw_data


def test_parse_raw_data(mock_raw_applescript_output):
    msgs = parse_raw_data(mock_raw_applescript_output)

    assert len(msgs) == 2

    # Check Parsing
    m1 = msgs[0]
    assert m1["id"] == "101"
    assert m1["subject"] == "Re: Project Update"
    assert "This is the email body" in m1["content"]
    assert m1["message_id"] == "<123@example.com>"

    # Check Date Parsing correctness implicit in parser?
    # Yes, parse_raw_data calls parse_date_string
    assert m1["timestamp"].year == 2025


def test_parse_raw_data_empty():
    assert parse_raw_data("") == []


def test_group_into_threads():
    # Mock data: 2 messages same ID, 1 different
    msgs = [{"id": "A", "timestamp": 1}, {"id": "A", "timestamp": 2}, {"id": "B", "timestamp": 3}]

    threads = group_into_threads(msgs)
    assert len(threads) == 2

    # Sort threads by ID not guaranteed, but usually dict order.
    # Let's verify lengths
    lengths = sorted([len(t) for t in threads])
    assert lengths == [1, 2]  # One thread size 1, one size 2
