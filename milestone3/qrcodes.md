QR Codes
========

It's suprisingly easy to print them!
This is just some random asset minted recently on AdaStat:

```
nix-shell -p qrencode
[nix-shell:~]$ qrencode -t ANSIUTF8 "https://adastat.net/policies/6580f133eca5bf88db273545bd62c568c276c01ac574a79945374fc6"
█████████████████████████████████████████████
█████████████████████████████████████████████
████ ▄▄▄▄▄ █▀█ █▄   ▀█▄▀▀▀█▀▄█▄▀██ ▄▄▄▄▄ ████
████ █   █ █▀▀▀█ ▄▀ █▄▀█▄ ▀█▄▀▀▄▀█ █   █ ████
████ █▄▄▄█ █▀ █▀▀██▄▄▄▄▀▄ ▄█▄▀▀▀▀█ █▄▄▄█ ████
████▄▄▄▄▄▄▄█▄▀ ▀▄█ █ ▀ █▄▀▄█ █▄▀ █▄▄▄▄▄▄▄████
████  ▄  █▄▄ ▄▀▄▀▀▀▀████▀  ▄▀▄▀▄▄ █ █ ▀ █████
████▀▄█▀██▄▀▄▀ █▀ ▄ █▀▀▄▀▄ █ █▀▄▀▄  █ ▄▀▄████
████▄   █▀▄▀▄▀▀█▄█▄ ▀▀█▄█▄██▀▄▀▄▄█▄▀▄▄ ▀▄████
████ ▀▄▄▀▀▄   ▄ ▄█▀█▀▀▀▄▄▄▀▀ ▄▀▄  █▀ ▀▄▄ ████
████▀  █▀ ▄██▄ ▄▀▀▀▄▀██▄  ▀▀▄▄▀██ ▄▀▄▄ ▀▄████
███████▀ ▄▄ ▄ ██▀ ▄ ▀▀▄▄▀▄██▄▄▀▄▄█ ▀ █▄▄ ████
████ █▀▀█▄▄▀ ▀ █▄█▄▀▀█ ▄ ▄ ▀▄▄▄▄ ▄▄█▄ ▄ ▄████
████  █   ▄█▀   ▄█▀▀▀█▀▄█▄██ █    █▀███▄ ████
████ ▀▀▄▄▄▄▀ ██▄▀▀▀█▀█▀▄▀▄▄ ▀▄▄▄▀▄▄ ▄▄▄ ▄████
████ █  ██▄█▄ ▄█▀ ▄ █▀ ▄▀▄▀█ ▄▀ ▄▄▀▄█▄█▄ ████
████▄███▄█▄█▀▄ █▄█▄ █▀ ▄█▄█ ▀▄▄▀ ▄▄▄  ▄██████
████ ▄▄▄▄▄ █▄█  ▄█▀▀▀█▀▄▄▄▄▀▄█▀█ █▄█ ██ ▄████
████ █   █ █  █▄▀▀▀ ▄ █▀▀  ▀▄▄▀▄   ▄ ▀▄▄█████
████ █▄▄▄█ █ ▀ █▀ ▄▀ ▀█▄█▄▄▀ █  ▀██▄██▄█ ████
████▄▄▄▄▄▄▄█▄█▄█▄█▄▄███▄▄▄▄█▄▄▄██▄▄▄██▄▄▄████
█████████████████████████████████████████████
█████████████████████████████████████████████
```

(This looks good in the terminal; it's only messed up in the markdown render.)

Reading them is a little weirder, but not bad.
I had to try a bunch of variations before finding one that will reliably kill it after one line:

```
nix-shell -p zbar
{ zbarcam --raw --quiet & pid=$!; echo $pid >&3; } 3>/tmp/zbarpid.tmp | head -n1; kill -9 $(cat /tmp/zbarpid.tmp); rm /tmp/zbarpid.tmp
https://adastat.net/policies/6580f133eca5bf88db273545bd62c568c276c01ac574a79945374fc6
```

And this does a similar thing using Python.
It should be easy to integrate into an ElectionGuard CLI:

```python
#!/usr/bin/env python3

import subprocess
import sys

try:
    process = subprocess.Popen(
        ['zbarcam'],
        stdout=subprocess.PIPE, text=True, bufsize=1
    )
    line = process.stdout.readline()
    if line:
        print(line.rstrip())
finally:
    process.kill()
    process.wait()
```
