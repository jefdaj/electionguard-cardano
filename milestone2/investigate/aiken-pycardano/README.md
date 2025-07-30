# hello-pycardano

Following the [Aiken + PyCardano hello-world](https://aiken-lang.org/example--hello-world/end-to-end/pycardano)

```bash
nix develop

# only the first time
$ mkdir keys
$ python generate-credentials.py
$ tree keys
keys
├── me.addr
└── me.sk

1 directory, 2 files

$ # request test ADA from faucet page -> me.addr

$ ./hello-world-lock.py 
2 tADA locked into the contract
        Tx ID: 3a92c59992213eec9d6e976d4539e122b4eac144a7622efbcbfcc34064250049
        Datum: d8799f581ca4c617ec067044027bbb364474efa617bf13eddcde1909eef3d2d50bff

$ # wait say 30sec for tx to go through

$ ./hello-world-unlock.py 3a92c59992213eec9d6e976d4539e122b4eac144a7622efbcbfcc34064250049
2 tADA unlocked from the contract
        Tx ID: 7b929674e0b6a9a848fb7949e6c878c8178fe2b5bfd90d04c60f1f75f4a5da8a
        Redeemer: 840000d8799f4d48656c6c6f2c20576f726c6421ff821978fd1a009aedf9
```
