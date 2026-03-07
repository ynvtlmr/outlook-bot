"""Tests for SSL utilities."""

import os
import ssl
from unittest.mock import patch

from outlook_bot.utils.ssl import (
    create_merged_cert_bundle,
    get_ssl_verify_option,
    get_zscaler_cert_path,
    setup_ssl_environment,
)


class TestGetZscalerCertPath:
    def test_finds_existing_path(self):
        with patch("os.path.exists") as mock_exists:
            mock_exists.side_effect = [False, True, False, False, False]
            result = get_zscaler_cert_path()
            assert result is not None

    def test_env_var_override(self):
        with (
            patch.dict(os.environ, {"ZSCALER_CERT_PATH": "/custom/zscaler.crt"}),
            patch("os.path.exists") as mock_exists,
        ):
            mock_exists.side_effect = lambda p: p == "/custom/zscaler.crt"
            result = get_zscaler_cert_path()
            assert result == "/custom/zscaler.crt"

    def test_none_when_not_found(self):
        with patch("os.path.exists", return_value=False):
            assert get_zscaler_cert_path() is None


class TestCreateMergedCertBundle:
    def test_returns_certifi_when_no_zscaler(self):
        with patch("outlook_bot.utils.ssl.get_zscaler_cert_path", return_value=None):
            result = create_merged_cert_bundle()
            assert result.endswith(".pem")

    def test_returns_certifi_on_error(self):
        with (
            patch("outlook_bot.utils.ssl.get_zscaler_cert_path", return_value="/fake/path"),
            patch("builtins.open", side_effect=OSError("read error")),
        ):
            result = create_merged_cert_bundle()
            assert result.endswith(".pem")


class TestGetSSLVerifyOption:
    def test_disabled_returns_context(self):
        result = get_ssl_verify_option(ssl_mode="disabled")
        assert isinstance(result, ssl.SSLContext)
        assert result.check_hostname is False
        assert result.verify_mode == ssl.CERT_NONE

    def test_auto_returns_bundle(self):
        with patch("outlook_bot.utils.ssl.create_merged_cert_bundle", return_value="/merged.pem"):
            result = get_ssl_verify_option(ssl_mode="auto")
            assert result == "/merged.pem"


class TestSetupSSLEnvironment:
    def test_sets_env_vars_with_path(self):
        with patch("os.path.exists", return_value=True), patch.dict(os.environ, {}, clear=True):
            setup_ssl_environment("/path/to/bundle.pem")
            assert os.environ.get("SSL_CERT_FILE") == "/path/to/bundle.pem"
            assert os.environ.get("REQUESTS_CA_BUNDLE") == "/path/to/bundle.pem"

    def test_clears_env_vars_with_context(self):
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        env_vars = {"SSL_CERT_FILE": "/some/path", "REQUESTS_CA_BUNDLE": "/other/path"}
        with patch.dict(os.environ, env_vars, clear=True):
            setup_ssl_environment(ctx)
            assert "SSL_CERT_FILE" not in os.environ
            assert "REQUESTS_CA_BUNDLE" not in os.environ
