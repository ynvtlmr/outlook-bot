"""SSL certificate utilities for Zscaler and corporate proxy support."""

from __future__ import annotations

import os
import ssl
from pathlib import Path

import certifi


def get_zscaler_cert_path() -> str | None:
    """Attempt to find a Zscaler root certificate in common locations."""
    possible_paths = [
        os.path.expanduser("~/Downloads/ZscalerRootCA.crt"),
        os.path.expanduser("~/Downloads/zscaler.crt"),
        "/opt/homebrew/etc/openssl@3/cert.pem",
        "/usr/local/etc/openssl@3/cert.pem",
        os.getenv("ZSCALER_CERT_PATH"),
    ]

    for path in possible_paths:
        if path and os.path.exists(path):
            return path

    return None


def create_merged_cert_bundle() -> str:
    """Create a merged certificate bundle combining certifi with Zscaler certificate.

    Returns path to merged bundle, or certifi default if creation fails.
    """
    zscaler_cert_path = get_zscaler_cert_path()

    if not zscaler_cert_path:
        return certifi.where()

    project_root = Path(__file__).parent.parent.parent.parent
    merged_bundle_path = project_root / "zscaler_cert_bundle.pem"

    try:
        with open(certifi.where()) as f:
            certifi_content = f.read()

        with open(zscaler_cert_path) as f:
            zscaler_content = f.read()

        merged_content = certifi_content + "\n" + zscaler_content

        with open(merged_bundle_path, "w") as f:
            f.write(merged_content)

        return str(merged_bundle_path)
    except OSError as e:
        print(f"Warning: Failed to create merged certificate bundle: {e}")
        return certifi.where()


def get_ssl_verify_option(ssl_mode: str = "disabled") -> ssl.SSLContext | str:
    """Return the SSL verify option based on configured mode.

    Args:
        ssl_mode: One of "disabled", "auto", "custom_bundle"

    Returns:
        SSL context with CERT_NONE if disabled, or path to certificate bundle.
    """
    if ssl_mode == "disabled":
        no_verify_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        no_verify_context.check_hostname = False
        no_verify_context.verify_mode = ssl.CERT_NONE
        return no_verify_context

    return create_merged_cert_bundle()


def setup_ssl_environment(verify_option: ssl.SSLContext | str) -> None:
    """Configure environment variables based on the SSL verify option."""
    if isinstance(verify_option, str) and os.path.exists(verify_option):
        print(f"[Info] Using certificate bundle: {verify_option}")
        os.environ["SSL_CERT_FILE"] = verify_option
        os.environ["REQUESTS_CA_BUNDLE"] = verify_option
    elif isinstance(verify_option, ssl.SSLContext):
        os.environ.pop("SSL_CERT_FILE", None)
        os.environ.pop("REQUESTS_CA_BUNDLE", None)
