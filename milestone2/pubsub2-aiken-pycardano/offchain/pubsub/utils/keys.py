from pathlib import Path

def load_signing_key():
    sk_path = Path("./keys/old-me.sk")
    with open(sk_path, 'r') as f:
        return f.read()
