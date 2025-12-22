"""
SSL Certificate Utilities for Zscaler and Corporate Proxy Support
"""
import os
import ssl
import certifi
from pathlib import Path
from typing import Optional, Union


def get_zscaler_cert_path() -> Optional[str]:
    """
    Attempts to find Zscaler root certificate in common locations.
    Returns path if found, None otherwise.
    """
    # Common Zscaler certificate locations on macOS
    possible_paths = [
        # macOS Keychain export location
        os.path.expanduser("~/Downloads/ZscalerRootCA.crt"),
        os.path.expanduser("~/Downloads/zscaler.crt"),
        # System certificate locations
        "/opt/homebrew/etc/openssl@3/cert.pem",
        "/usr/local/etc/openssl@3/cert.pem",
        # Environment variable override
        os.getenv("ZSCALER_CERT_PATH"),
    ]
    
    for path in possible_paths:
        if path and os.path.exists(path):
            return path
    
    return None


def create_merged_cert_bundle() -> str:
    """
    Creates a merged certificate bundle by combining certifi's bundle with Zscaler certificate.
    Returns path to merged bundle, or certifi default if creation fails.
    """
    zscaler_cert_path = get_zscaler_cert_path()
    
    if not zscaler_cert_path:
        # No Zscaler cert found, just use certifi
        return certifi.where()
    
    # Create merged bundle in project directory
    # We use a hidden file or specific name to avoid checking it into git easily if user isn't careful,
    # though it's generated code.
    project_root = Path(__file__).parent.parent
    merged_bundle_path = project_root / "zscaler_cert_bundle.pem"
    
    try:
        # Read certifi bundle
        with open(certifi.where(), "r") as f:
            certifi_content = f.read()
        
        # Read Zscaler certificate
        with open(zscaler_cert_path, "r") as f:
            zscaler_content = f.read()
        
        # Merge: certifi first, then Zscaler
        merged_content = certifi_content + "\n" + zscaler_content
        
        # Write merged bundle
        with open(merged_bundle_path, "w") as f:
            f.write(merged_content)
        
        return str(merged_bundle_path)
    except Exception as e:
        print(f"Warning: Failed to create merged certificate bundle: {e}")
        return certifi.where()


def get_ssl_verify_option(disable_ssl: bool = False) -> Union[ssl.SSLContext, str]:
    """
    Returns the SSL verify option to use for HTTP clients.
    
    Args:
        disable_ssl: If True, returns SSL context with CERT_NONE (disables verification)
        
    Returns:
        SSL context with CERT_NONE if SSL should be disabled
        Path to certificate bundle (merged with Zscaler if available) otherwise
    """
    if disable_ssl:
        # Create SSL context that completely disables verification
        # This is necessary because httpx doesn't always respect verify=False boolean
        no_verify_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        no_verify_context.check_hostname = False
        no_verify_context.verify_mode = ssl.CERT_NONE
        return no_verify_context
    
    # Try to create merged bundle using auto-discovery
    merged_bundle = create_merged_cert_bundle()
    return merged_bundle
