<div align="center">

![](.github/electionguard-cardano-logo-v4-transparent.png)

ElectionGuard + Cardano
=======================
</div>

Work in progress on the Catalyst Fund13 project. See [catalyst/](catalyst/) for details.

## Dev QuickStart

First you need a dev wallet with funds from the faucet.

```
$ nix develop
$ python
Python 3.13.16 (main, Sep 30 2026, 18:57:20) [GCC 16.2.0] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>> import egc
>>> egc.create_wallet(name='dev')
Running in test mode, so all keys will be logged to /home/jefdaj/myrepos/electionguard-cardano/keys/wallets.log

    Your new Preview testnet key "dev (Generated EGC wallet)" is here:

    /home/jefdaj/myrepos/electionguard-cardano/keys/dev.sk

    You can load it in Python like this:

    wallet = Wallet.from_sk_path("/home/jefdaj/myrepos/electionguard-cardano/keys/dev.sk")

    Its public address is: addr_test1vz5aqmhnvpg7g7l8jy40cxmhrf6p94h8k0k3ufgljwerdwqgdshu6

    If this is your main dev wallet, go fund that address with tADA from the
    faucet before running any tests:
    https://docs.cardano.org/cardano-testnets/tools/faucet

    If you don't, local tests will still work but testnet tests will fail.

Wallet(addr=addr_test1vz5aqmhnvpg7g7l8jy40cxmhrf6p94h8k0k3ufgljwerdwqgdshu6, vkh=581ca9d06ef3…)
```
