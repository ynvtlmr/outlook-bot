from main import process_replies


def test_process_replies_flow(mocker):
    # Mock candidates
    candidates = [{"thread": [], "target_msg": {"message_id": "123", "content": "Body"}, "subject": "Test Subj"}]

    # Mock LLM Service
    mock_llm = mocker.Mock()
    mock_llm.generate_batch_replies.return_value = {"123": "Generated Reply"}

    # Mock Outlook Client
    mock_client = mocker.Mock()
    mock_client.reply_to_message.return_value = "Draft Created"

    # Run
    process_replies(candidates, mock_client, "System Prompt", mock_llm)

    # Verify
    mock_llm.generate_batch_replies.assert_called_once()
    mock_client.reply_to_message.assert_called_once_with("123", "Generated Reply")  # wait, formatting logic
    # The code escapes HTML and replaces newlines.
    # If "Generated Reply" is simple, it matches.


def test_process_replies_no_candidates():
    # Should exit early - None values are intentional for testing early exit
    process_replies([], None, None, None)  # type: ignore[arg-type]
    # No crash means pass
