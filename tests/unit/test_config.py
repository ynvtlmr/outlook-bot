"""Tests for configuration management."""

from unittest.mock import patch

from outlook_bot.core.config import Config, CredentialManager, Paths


class TestPaths:
    def test_paths_source_mode(self):
        paths = Paths()
        assert paths.config_path.name == "config.yaml"
        assert paths.env_path.name == ".env"
        assert paths.output_dir.name == "output"

    def test_applescripts_dir(self):
        paths = Paths()
        assert paths.applescripts_dir.name == "apple_scripts"

    def test_ensure_output_dir(self, tmp_path):
        paths = Paths()
        paths.user_data_dir = tmp_path
        paths.ensure_output_dir()
        assert (tmp_path / "output").exists()


class TestCredentialManager:
    def test_get_gemini_key(self):
        with patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}):
            assert CredentialManager.get_gemini_key() == "test-key"

    def test_get_gemini_key_missing(self):
        with patch.dict("os.environ", {}, clear=True):
            assert CredentialManager.get_gemini_key() is None

    def test_get_openai_key(self):
        with patch.dict("os.environ", {"OPENAI_API_KEY": "oai-key"}):
            assert CredentialManager.get_openai_key() == "oai-key"

    def test_get_openrouter_key(self):
        with patch.dict("os.environ", {"OPENROUTER_API_KEY": "or-key"}):
            assert CredentialManager.get_openrouter_key() == "or-key"


class TestConfig:
    def test_default_values(self):
        config = Config()
        assert config.days_threshold == 5
        assert config.cold_outreach_enabled is False
        assert config.ssl_mode == "disabled"

    def test_load_from_yaml(self, tmp_path):
        config_file = tmp_path / "config.yaml"
        config_file.write_text("days_threshold: 10\npreferred_model: gpt-4\n")

        paths = Paths()
        paths.user_data_dir = tmp_path
        paths.resource_dir = tmp_path

        config = Config.load(paths)
        assert config.days_threshold == 10
        assert config.preferred_model == "gpt-4"

    def test_load_missing_file(self, tmp_path):
        paths = Paths()
        paths.user_data_dir = tmp_path
        paths.resource_dir = tmp_path
        config = Config.load(paths)
        assert config.days_threshold == 5  # default

    def test_save_and_reload(self, tmp_path):
        paths = Paths()
        paths.user_data_dir = tmp_path
        paths.resource_dir = tmp_path

        config = Config(days_threshold=14, preferred_model="gemini-flash")
        config.save(paths)

        loaded = Config.load(paths)
        assert loaded.days_threshold == 14
        assert loaded.preferred_model == "gemini-flash"

    def test_preserves_unknown_keys(self, tmp_path):
        config_file = tmp_path / "config.yaml"
        config_file.write_text("days_threshold: 7\ncustom_key: custom_value\n")

        paths = Paths()
        paths.user_data_dir = tmp_path
        paths.resource_dir = tmp_path

        config = Config.load(paths)
        config.save(paths)

        import yaml

        with open(config_file) as f:
            data = yaml.safe_load(f)

        assert data["custom_key"] == "custom_value"
        assert data["days_threshold"] == 7
