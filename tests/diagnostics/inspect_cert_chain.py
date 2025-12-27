import socket
import ssl


def get_cert_chain(host, port=443):
    print(f"Connecting to {host}:{port}...")
    context = ssl.create_default_context()

    # We want to see the error if validation fails, but verify_mode=CERT_NONE would hide it.
    # However, to inspect the cert even if it fails validation, we might need a custom approach
    # OR we just catch the error and try to inspect what we can.
    # But usually, if handshake fails, we can't get the peer cert easily
    # via high-level SSLSocket without suppressing the error.

    # Strategy: Connect with CERT_NONE to fetch the cert, then print its details.
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    try:
        with socket.create_connection((host, port)) as sock:
            with context.wrap_socket(sock, server_hostname=host) as ssock:
                _cert = ssock.getpeercert(binary_form=True)  # Intentionally unused
                # Parse binary cert using OpenSSL (if available via python standard ssl?)
                # Standard 'ssl' module can parse DER to dict ONLY if we didn't use CERT_NONE?
                # Actually, ssock.getpeercert() returns {} if CERT_NONE, unless binary_form=True.

                # We need to parse the DER.
                # Since we want to avoid extra dependencies like pyopenssl or cryptography for the user if possible,
                # we can try to rely on the error message from the *strict* connection to tell us the issuer,
                # or just use 'ssl' module's capabilities.

                pass

    except Exception as e:
        print(f"Connection failed: {e}")

    # Better Strategy:
    # Just try to get the cert in a way that gives us the text.
    # If we use verify_mode=CERT_REQUIRED (default), it throws.
    # If we catch the error, we might be able to extract info? No.

    # Let's use the 'binary_form=True' + CERT_NONE, then try to decode basic info if possible
    # Or just use the fact that the user HAS 'pip installed' dependencies.
    # But this script should be lightweight.

    # Let's fallback to just printing the 'ssl.get_server_certificate' output?
    # That returns PEM. We can print the issuer from the PEM if we parse it.
    pass


# Re-thinking: The user HAS the error log "unable to get local issuer certificate".
# We want to show WHO the issuer IS.
# We can use `ssl.get_server_certificate` which fetches it without validating?


def inspect_chain():
    target_host = "generativelanguage.googleapis.com"
    print(f"--- INSPECTING CERTIFICATE FOR {target_host} ---")

    try:
        cert_pem = ssl.get_server_certificate((target_host, 443))
        # This function fetches the leaf certificate in PEM format.
        # It doesn't validate.
        print("Successfully fetched server certificate (PEM).")

        # Now, how to parse PEM to show Issuer without 3rd party libs?
        # Python's `ssl` module does not expose a public PEM parser easily.
        # BUT we can create a temp context, load this cert? No.

        # Let's just dump the PEM. The user sent us logs, so they know how to copy paste.
        # If we can see the PEM, we can decode it locally or ask them to.
        # better: print the Issuer line if it's in text (it's not, it's Base64).

        # Okay, let's try to load it into a context to parse it?
        import os
        import tempfile

        with tempfile.NamedTemporaryFile(delete=False) as tf:
            tf.write(cert_pem.encode())
            tf_path = tf.name

        # Create a context that trusts THIS cert (as a CA? No, it's a leaf).
        # We can use _ssl.Method specific?

        # actually, context.load_verify_locations(cafile=...) usually loads roots.

        print("\nCertificate PEM:")
        print(cert_pem)
        print("\nPaste this PEM into a decoder (like report-uri.com/home/pem-decoder) to see the Issuer.")
        print("If the issuer is 'Zscaler' or your company name, that confirms the proxy issue.")

        os.remove(tf_path)

    except Exception as e:
        print(f"Failed to fetch cert: {e}")


if __name__ == "__main__":
    inspect_chain()
