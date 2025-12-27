import os
import ssl
import sys
import urllib.error
import urllib.request


def log(msg):
    print(f"[LOG] {msg}")


def run_diagnostics():
    print("=" * 60)
    print("SSL DIAGNOSTICS FOR OUTLOOK BOT")
    print("=" * 60)

    # --- TEST 1: Environment Inspection ---
    print("\n--- TEST 1: Environment Inspection ---")
    log(f"Python Executable: {sys.executable}")
    log(f"Python Version: {sys.version}")

    # Check for SSL-related environment variables
    ssl_vars = {k: v for k, v in os.environ.items() if "SSL" in k or "CERT" in k}
    if ssl_vars:
        log("Found SSL/CERT environment variables:")
        for k, v in ssl_vars.items():
            log(f"  {k} = {v}")
    else:
        log("No SSL_... or ...CERT... environment variables found.")

    # --- TEST 2: SSL Default Verify Paths ---
    print("\n--- TEST 2: SSL Default Verify Paths ---")
    try:
        paths = ssl.get_default_verify_paths()
        log(f"cafile: {paths.cafile}")
        log(f"capath: {paths.capath}")
        log(f"openssl_cafile_env: {paths.openssl_cafile_env}")
        log(f"openssl_cafile: {paths.openssl_cafile}")
        log(f"openssl_capath_env: {paths.openssl_capath_env}")
        log(f"openssl_capath: {paths.openssl_capath}")

        # Check if cafile actually exists
        if paths.cafile and os.path.exists(paths.cafile):
            log(f"SUCCESS: Default cafile exists at {paths.cafile}")
        else:
            log(f"WARNING: Default cafile does not exist at {paths.cafile}")

    except Exception as e:
        log(f"Error getting verify paths: {e}")

    # --- TEST 3: Certifi Availability ---
    print("\n--- TEST 3: Certifi Availability ---")
    certifi_path = None
    try:
        import certifi

        certifi_path = certifi.where()
        log(f"Certifi is installed. Path: {certifi_path}")
        if os.path.exists(certifi_path):
            log("SUCCESS: Certifi bundle file exists.")
        else:
            log("ERROR: Certifi bundle file missing on disk!")
    except ImportError:
        log("WARNING: 'certifi' package is NOT installed.")

    # --- TEST 4: Standard Connection Test ---
    print("\n--- TEST 4: Standard Connection Test (to Google API) ---")
    target_url = "https://generativelanguage.googleapis.com"
    try:
        log(f"Attempting valid CONNECT to {target_url}...")
        # Timeout 5s
        with urllib.request.urlopen(target_url, timeout=5) as response:
            log(f"SUCCESS: Connection established. Status: {response.status}")
    except urllib.error.HTTPError as e:
        log(f"SUCCESS: SSL Handshake worked! (Server returned {e.code}, expected for this URL)")
    except urllib.error.URLError as e:
        log(f"FAILURE: URL Error: {e.reason}")
    except Exception as e:
        log(f"FAILURE: Exception: {e}")

    # --- TEST 5: Connection with Explicit Certifi ---
    print("\n--- TEST 5: Connection Test using Certifi Explicitly ---")
    if certifi_path:
        try:
            log(f"Attempting CONNECT to {target_url} using cafile={certifi_path}...")
            context = ssl.create_default_context(cafile=certifi_path)
            with urllib.request.urlopen(target_url, context=context, timeout=5) as response:
                log(f"SUCCESS: Connection established with Certifi. Status: {response.status}")
        except urllib.error.HTTPError as e:
            log(f"SUCCESS: SSL Handshake worked with Certifi! (Server returned {e.code})")
        except urllib.error.URLError as e:
            log(f"FAILURE: URL Error with Certifi: {e.reason}")
        except Exception as e:
            log(f"FAILURE: Exception with Certifi: {e}")
    else:
        log("SKIP: Certifi not available to test.")

    print("\n" + "=" * 60)
    print("END DIAGNOSTICS")
    print("=" * 60)


if __name__ == "__main__":
    run_diagnostics()
