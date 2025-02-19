# hello-pycardano

Following the [Aiken + PyCardano hello-world](https://aiken-lang.org/example--hello-world/end-to-end/pycardano)

```bash
nix develop
pip install pycardano

# only the first time to generate me.addr + me.sk
# then request test ADA from faucet page -> me.addr
mkdir keys
python generate-credentials.py
mv me.* keys/
```
