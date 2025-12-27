from llm import LLMService


def test_llm_init(mocker):
    # Mock OS environ
    mocker.patch.dict("os.environ", {"GEMINI_API_KEY": "fake_key"})

    # Mock genai.Client
    mock_genai = mocker.patch("llm.genai.Client")

    service = LLMService()
    assert service.gemini_client is not None
    mock_genai.assert_called_once()


def test_generate_reply_fallback(mocker):
    mocker.patch.dict("os.environ", {"GEMINI_API_KEY": "fake_key"})
    mocker.patch("llm.genai.Client")

    service = LLMService()

    # Mock available models
    service.available_models = [{"id": "gemini-1", "provider": "gemini"}]

    # Mock response
    mock_response = mocker.Mock()
    mock_response.text = "Generated Reply"

    # Mock the method capable of generating
    # Note: the real method is models.generate_content
    # Ideally we mock the client.models.generate_content chain.
    service.gemini_client.models.generate_content.return_value = mock_response  # type: ignore[union-attr]

    reply = service.generate_reply("prompt", "system")
    assert reply == "Generated Reply"
