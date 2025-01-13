# electionguard-python tests

After ironing out a couple minor kinks in [the dev setup](./02-electionguard-python-dev-setup.md), all of the tests pass! :partying_face:

I'm also very pleased with the code quality so far.
Probably should have expected that from Microsoft...

```bash
[jefdaj@nixos:~/myrepos/electionguard-python]$ ./makefile-docker-env.sh 2>&1 | tee test.log 
#0 building with "default" instance using docker driver

#1 [internal] load build definition from Dockerfile
#1 transferring dockerfile: 419B done
#1 DONE 0.0s

#2 [internal] load metadata for docker.io/library/python:3.9-bullseye
#2 DONE 1.4s

#3 [internal] load .dockerignore
#3 transferring context: 2B done
#3 DONE 0.0s

#4 [1/6] FROM docker.io/library/python:3.9-bullseye@sha256:1323a0125d30e4acc2d9cb713fefde3dbd931bcf512a0658e71f6e216461786d
#4 DONE 0.0s

#5 [5/6] RUN mkdir /repo
#5 CACHED

#6 [2/6] RUN apt update && apt-get install -y     libgmp-dev     libmpfr-dev     libmpc-dev     graphviz     jq
#6 CACHED

#7 [3/6] RUN apt-get clean &&     rm -rf /var/lib/apt/lists/*
#7 CACHED

#8 [4/6] RUN pip install 'poetry==1.1.14'
#8 CACHED

#9 [6/6] WORKDIR /repo
#9 CACHED

#10 exporting to image
#10 exporting layers done
#10 writing image sha256:61102dd398ea56f43d0906ed424e14d0b7a64730211ca205905171e1ce9bd4fe done
#10 naming to docker.io/library/electionguard-python-makefile-docker-env done
#10 DONE 0.0s

root@29187e5fa3d0:/repo# make | tee -a test.log
🔧 ENVIRONMENT SETUP
make install-gmp
make[1]: Entering directory '/repo'
📦 Install gmp
Operating System identified as Linux
make install-gmp-linux
make[2]: Entering directory '/repo'
🐧 LINUX INSTALL
# only install if needed
ldconfig -p | grep libgmp  || sudo apt-get install libgmp-dev
	libgmpxx.so.4 (libc6,x86-64) => /usr/lib/x86_64-linux-gnu/libgmpxx.so.4
	libgmpxx.so (libc6,x86-64) => /usr/lib/x86_64-linux-gnu/libgmpxx.so
	libgmp.so.10 (libc6,x86-64) => /usr/lib/x86_64-linux-gnu/libgmp.so.10
	libgmp.so (libc6,x86-64) => /usr/lib/x86_64-linux-gnu/libgmp.so
ldconfig -p | grep libmpfr || sudo apt-get install libmpfr-dev
	libmpfr.so.6 (libc6,x86-64) => /usr/lib/x86_64-linux-gnu/libmpfr.so.6
	libmpfr.so (libc6,x86-64) => /usr/lib/x86_64-linux-gnu/libmpfr.so
ldconfig -p | grep libmpc  || sudo apt-get install libmpc-dev
	libmpc.so.3 (libc6,x86-64) => /usr/lib/x86_64-linux-gnu/libmpc.so.3
	libmpc.so (libc6,x86-64) => /usr/lib/x86_64-linux-gnu/libmpc.so
make[2]: Leaving directory '/repo'
make[1]: Leaving directory '/repo'
pip3 --version || python3 -m pip install -U pip
pip 23.0.1 from /usr/local/lib/python3.9/site-packages/pip (python 3.9)
poetry --version | grep '1.1.14' || pip3 install 'poetry==1.1.14'
Poetry version 1.1.14
poetry config virtualenvs.in-project true 
make install
make[1]: Entering directory '/repo'
🔧 INSTALL
# TODO is this really necessary to get around network errors?
for n in {1..3}; do poetry install && break || sleep 3; done
Installing dependencies from lock file

No dependencies to install or update

Installing the current project: electionguard (1.4.0)
make[1]: Leaving directory '/repo'
🚨 Be sure to add poetry to PATH
make fetch-sample-data
make[1]: Entering directory '/repo'
⬇️ FETCH Sample Data
# only download if needed
test -f sample-data.zip || wget -O sample-data.zip https://github.com/microsoft/electionguard/releases/download/v1.0/sample-data.zip
unzip -o sample-data.zip
Archive:  sample-data.zip
  inflating: data/1.0/sample/full/election_private_data/ciphertext_ballots/ciphertext_ballot_ballot-cb3535db-1a4e-11ed-95c2-04d9f5218a21.json  
...
  inflating: data/1.0/schema/submitted_ballot.schema.json  
make[1]: Leaving directory '/repo'
🔧 INSTALL
# TODO is this really necessary to get around network errors?
for n in {1..3}; do poetry install && break || sleep 3; done
Installing dependencies from lock file

No dependencies to install or update

Installing the current project: electionguard (1.4.0)
🔨 BUILD
poetry build
Building electionguard (1.4.0)
  - Building sdist
  - Built electionguard-1.4.0.tar.gz
  - Building wheel
  - Built electionguard-1.4.0-py3-none-any.whl
make install 
make[1]: Entering directory '/repo'
🔧 INSTALL
# TODO is this really necessary to get around network errors?
for n in {1..3}; do poetry install && break || sleep 3; done
Installing dependencies from lock file

No dependencies to install or update

Installing the current project: electionguard (1.4.0)
make[1]: Leaving directory '/repo'
✅ VALIDATE
electionguard successfully imported
💚 AUTO LINT
Auto-generating __init__
poetry run mkinit src/electionguard --write --black
poetry run mkinit src/electionguard_tools --write --recursive --black
poetry run mkinit src/electionguard_verify --write --black
poetry run mkinit src/electionguard_cli --write --recursive --black
poetry run mkinit src/electionguard_gui --write --recursive --black
Reformatting using Black
make blackformat
make[1]: Entering directory '/repo'
poetry run black .
All done! ✨ 🍰 ✨
223 files left unchanged.
make[1]: Leaving directory '/repo'
make lint
make[1]: Entering directory '/repo'
💚 LINT
1.Pylint
make pylint
make[2]: Entering directory '/repo'
poetry run pylint --extension-pkg-allow-list=dependency_injector ./src ./tests

------------------------------------
Your code has been rated at 10.00/10

make[2]: Leaving directory '/repo'
2.Black Formatting
make blackcheck
make[2]: Entering directory '/repo'
poetry run black --check .
All done! ✨ 🍰 ✨
223 files would be left unchanged.
make[2]: Leaving directory '/repo'
3.Mypy Static Typing
make mypy
make[2]: Entering directory '/repo'
poetry run mypy src/electionguard src/electionguard_tools src/electionguard_cli src/electionguard_gui stubs
Success: no issues found in 170 source files
make[2]: Leaving directory '/repo'
4.Package Metadata
poetry build
Building electionguard (1.4.0)
  - Building sdist
  - Built electionguard-1.4.0.tar.gz
  - Building wheel
  - Built electionguard-1.4.0-py3-none-any.whl
poetry run twine check dist/*
Checking dist/electionguard-1.4.0-py3-none-any.whl: [32mPASSED[0m
Checking dist/electionguard-1.4.0.tar.gz: [32mPASSED[0m
5.Documentation
poetry run mkdocs build --strict
INFO     -  Cleaning site directory
INFO     -  Building documentation to directory: /repo/site
INFO     -  The following pages exist in the docs directory, but are not included in the "nav" configuration:
  - Tablet Setup.md
INFO     -  Converting notebook (execute=False): /repo/docs/0_Configure_Election.ipynb
INFO     -  Documentation built in 0.51 seconds
make[1]: Leaving directory '/repo'
✅ COVERAGE
poetry run coverage run -m pytest
============================= test session starts ==============================
platform linux -- Python 3.9.21, pytest-7.1.1, pluggy-1.0.0
rootdir: /repo
plugins: hypothesis-6.41.0, mock-3.8.2, xdoctest-1.0.0
collected 223 items

tests/integration/test_create_schema.py .                                [  0%]
tests/integration/test_end_to_end_election.py .                          [  0%]
tests/integration/test_functional_key_ceremony.py .                      [  1%]
tests/integration/test_hamilton_county_election.py .                     [  1%]
tests/property/test_ballot.py ...                                        [  3%]
tests/property/test_chaum_pedersen.py ..........                         [  7%]
tests/property/test_decrypt_with_secrets.py .......                      [ 10%]
tests/property/test_decryption_mediator.py ....                          [ 12%]
tests/property/test_discrete_log.py .........                            [ 16%]
tests/property/test_elgamal.py .............                             [ 22%]
tests/property/test_encrypt.py ......s........                           [ 29%]
tests/property/test_encrypt_hypotheses.py ..                             [ 30%]
tests/property/test_group.py ......................                      [ 39%]
tests/property/test_hash.py ............                                 [ 45%]
tests/property/test_nonces.py .....                                      [ 47%]
tests/property/test_schnorr.py ......                                    [ 50%]
tests/property/test_tally.py ...                                         [ 51%]
tests/property/test_verify.py ...                                        [ 52%]
tests/unit/electionguard/test_ballot.py ....                             [ 54%]
tests/unit/electionguard/test_ballot_box.py ......                       [ 57%]
tests/unit/electionguard/test_ballot_code.py .                           [ 57%]
tests/unit/electionguard/test_ballot_compact.py ..                       [ 58%]
tests/unit/electionguard/test_constants.py ..                            [ 59%]
tests/unit/electionguard/test_decrypt_with_shares.py ...                 [ 60%]
tests/unit/electionguard/test_decryption.py ........                     [ 64%]
tests/unit/electionguard/test_election_polynomial.py ...                 [ 65%]
tests/unit/electionguard/test_elgamal.py ..                              [ 66%]
tests/unit/electionguard/test_encrypt.py .....                           [ 69%]
tests/unit/electionguard/test_guardian.py ..............                 [ 75%]
tests/unit/electionguard/test_hmac.py .                                  [ 75%]
tests/unit/electionguard/test_key_ceremony.py .......                    [ 78%]
tests/unit/electionguard/test_key_ceremony_mediator.py .....             [ 81%]
tests/unit/electionguard/test_logs.py ..                                 [ 82%]
tests/unit/electionguard/test_manifest.py ...........                    [ 86%]
tests/unit/electionguard/test_scheduler.py ..                            [ 87%]
tests/unit/electionguard/test_singleton.py ..                            [ 88%]
tests/unit/electionguard/test_utils.py ....                              [ 90%]
tests/unit/electionguard_gui/test_decryption_dto.py .......              [ 93%]
tests/unit/electionguard_gui/test_eel_utils.py ..                        [ 94%]
tests/unit/electionguard_gui/test_election_dto.py ...                    [ 95%]
tests/unit/electionguard_gui/test_plaintext_ballot_service.py .........  [100%]

=============================== warnings summary ===============================
.venv/lib/python3.9/site-packages/eel/__init__.py:16
  /repo/.venv/lib/python3.9/site-packages/eel/__init__.py:16: DeprecationWarning: pkg_resources is deprecated as an API. See https://setuptools.pypa.io/en/latest/pkg_resources.html
    import pkg_resources as pkg

.venv/lib/python3.9/site-packages/pkg_resources/__init__.py:3149
.venv/lib/python3.9/site-packages/pkg_resources/__init__.py:3149
  /repo/.venv/lib/python3.9/site-packages/pkg_resources/__init__.py:3149: DeprecationWarning: Deprecated call to `pkg_resources.declare_namespace('zope')`.
  Implementing implicit namespace packages (as specified in PEP 420) is preferred to `pkg_resources.declare_namespace`. See https://setuptools.pypa.io/en/latest/references/keywords.html#keyword-namespace-packages
    declare_namespace(pkg)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
============ 222 passed, 1 skipped, 3 warnings in 87.65s (0:01:27) =============
poetry run coverage report --fail-under=90
Name                                         Stmts   Miss Branch BrPart  Cover
------------------------------------------------------------------------------
src/electionguard/__init__.py                   82      2      0      0    98%
src/electionguard/ballot.py                    288     31    138     22    88%
src/electionguard/ballot_box.py                 37      2     10      2    91%
src/electionguard/ballot_code.py                 6      0      0      0   100%
src/electionguard/ballot_compact.py             69      1     20      1    98%
src/electionguard/ballot_validator.py           50      3     32      2    94%
src/electionguard/big_integer.py                53      3      4      0    95%
src/electionguard/byte_padding.py               28      1     10      1    95%
src/electionguard/chaum_pedersen.py            172      0     16      0   100%
src/electionguard/constants.py                  30      0     12      0   100%
src/electionguard/data_store.py                 43     14      8      0    65%
src/electionguard/decrypt_with_secrets.py      100     14     48      8    85%
src/electionguard/decrypt_with_shares.py        57     10     34      7    81%
src/electionguard/decryption.py                136      7     62     10    91%
src/electionguard/decryption_mediator.py       139     16     56     10    83%
src/electionguard/decryption_share.py           80     10     36      5    87%
src/electionguard/discrete_log.py               88     16     38      9    79%
src/electionguard/election.py                   30      3  Name                                         Stmts   Miss Branch BrPart  Cover
------------------------------------------------------------------------------
src/electionguard/__init__.py                   82      2      0      0    98%
src/electionguard/ballot.py                    288     31    138     22    88%
src/electionguard/ballot_box.py                 37      2     10      2    91%
src/electionguard/ballot_code.py                 6      0      0      0   100%
src/electionguard/ballot_compact.py             69      1     20      1    98%
src/electionguard/ballot_validator.py           50      3     32      2    94%
src/electionguard/big_integer.py                53      3      4      0    95%
src/electionguard/byte_padding.py               28      1     10      1    95%
src/electionguard/chaum_pedersen.py            172      0     16      0   100%
src/electionguard/constants.py                  30      0     12      0   100%
src/electionguard/data_store.py                 43     14      8      0    65%
src/electionguard/decrypt_with_secrets.py      100     14     48      8    85%
src/electionguard/decrypt_with_shares.py        57     10     34      7    81%
src/electionguard/decryption.py                136      7     62     10    91%
src/electionguard/decryption_mediator.py       139     16     56     10    83%
src/electionguard/decryption_share.py           80     10     36      5    87%
src/electionguard/discrete_log.py               88     16     38      9    79%
src/electionguard/election.py                   30      3      6      0    86%
src/electionguard/election_object_base.py       14      0      8      0   100%
src/electionguard/election_polynomial.py        55      0     20      0   100%
src/electionguard/elgamal.py                   107      4     30      3    93%
src/electionguard/encrypt.py                   166     17     66     13    87%
src/electionguard/group.py                     126      9     20      0    94%
src/electionguard/guardian.py                  167     14     42      9    89%
src/electionguard/hash.py                       36      1     18      1    96%
src/electionguard/hmac.py                       12      0      2      0   100%
src/electionguard/key_ceremony.py               93      0     20      0   100%
src/electionguard/key_ceremony_mediator.py     111      7     46      9    90%
src/electionguard/logs.py                       74      8      2      0    89%
src/electionguard/manifest.py                  384     18    138     18    93%
src/electionguard/nonces.py                     27      2     12      0    95%
src/electionguard/proof.py                      12      0      4      0   100%
src/electionguard/scheduler.py                  58      6     10      2    88%
src/electionguard/schnorr.py                    35      0      4      0   100%
src/electionguard/serialize.py                  66     12      8      0    78%
src/electionguard/singleton.py                  11      1      6      1    88%
src/electionguard/tally.py                     176     15    102     14    89%
src/electionguard/type.py                        6      0      0      0   100%
src/electionguard/utils.py                      60      1     18      0    99%
------------------------------------------------------------------------------
TOTAL                                         3284    248   1106    147    90%
```

Apart from the test suite, there are also a couple one-off `make` targets that demonstrate a simple election. They look good too!
Note that they also print all the ciphertexts, but I had to omit those lines to avoid breaking Github's markdown rendering.

```bash
root@29187e5fa3d0:/repo# make eg-setup-simple-election 2>&1 | tee test.log

poetry run eg setup --guardian-count=2 --quorum=2 --manifest=data/election_manifest_simple.json  --package-dir=../data/out/public_encryption_package --keys-dir=../data/out/test_data_private_guardian_data

----------------------------------------
Retrieving Inputs
----------------------------------------
Name: Jefferson County Spring Primary
Scope: jefferson-county-primary
Geopolitical Units: 4
Parties: 3
Candidates: 6
Contests: 2
Ballot Styles: 4

----------------------------------------
Performing key ceremony
----------------------------------------
...
Joint Key: 10C835F6D8F7CE1F30EB62652914908F86EA9E5C8C4C25763FA4C6BC00886944A7801532668339869E1ACBC2B80C0EE72B38FD9031B630A05543A4E889CED9324950FDA7C3EF1EAD46FF8065B6C87797CF4C3EDF24DFC76DDDC476A274E358A6E2FED248AE7FA4EAA1791AD6DDB4A1E972FC063ADCC302D589EAC0406B0C639F3A8FC4BE8B901B4E21780DE20042A11649F21E77E75E1AF787DE4C808D644AFC7F025B2B8E6B3C5B5E0A200EBB21E85D7C376D428E2CEF9032C76CCBA9E0B7D87169A6DEE5D1F21B04FDA0C64CC49B68D220CC0F1FD6D486173B588AC6E5AF94B04ABE4D05276C198F6290079F7A4DA6299919B040F64C57C84596C210773352C1159400A4B39767D597CCEEEF004C687F3F163E2E4D9E0F21C645D056A3FB8E7E8E3D7003AF78AE3ADDF75126377C9506A99D6A34337A97C838B42C5533EEDF4A9151B842A569115F247C54C6BE78440FB8DF9140A5F616D3A12E377B1E48814ECFD34F89B44865DC8D0649AA230ECE125EDE01DCD296A262F5384D21F7240AA3CFF59091A624DF50097CA8AE31EE168897F4BCEBC39C314DAA1192D136BE9B8F5A2635574CBF0B34DAEF70EB3BC7340DB464136A7EC888A3CD7CA44BC31CEFF5102FF14AE0CC84681F3F2BBB30252E4EB22A659F553E2F92C7392F7D74AA130304B35D0B0891E152EC4051419F562B27050BD0C72F7C76818194429A97EDBE

----------------------------------------
Building election
----------------------------------------
Initializing public key and commitment hash
Creating context and internal manifest

----------------------------------------
Generating Output
----------------------------------------
Context: /data/out/public_encryption_package/context.json
Constants: /data/out/public_encryption_package/constants.json
Manifest: /data/out/public_encryption_package/manifest.json
Guardian records: /data/out/public_encryption_package/guardians
Guardian private keys: /data/out/test_data_private_guardian_data
WARNING: The files in /data/out/test_data_private_guardian_data are secret and should be protected securely and not shared.
...

----------------------------------------
Retrieving Inputs
----------------------------------------
Name: Jefferson County Spring Primary
Scope: jefferson-county-primary
Geopolitical Units: 4
Parties: 3
Candidates: 6
Contests: 2
Ballot Styles: 4

----------------------------------------
Performing key ceremony
----------------------------------------
...
Joint Key: 10C835F6D8F7CE1F30EB62652914908F86EA9E5C8C4C25763FA4C6BC00886944A7801532668339869E1ACBC2B80C0EE72B38FD9031B630A05543A4E889CED9324950FDA7C3EF1EAD46FF8065B6C87797CF4C3EDF24DFC76DDDC476A274E358A6E2FED248AE7FA4EAA1791AD6DDB4A1E972FC063ADCC302D589EAC0406B0C639F3A8FC4BE8B901B4E21780DE20042A11649F21E77E75E1AF787DE4C808D644AFC7F025B2B8E6B3C5B5E0A200EBB21E85D7C376D428E2CEF9032C76CCBA9E0B7D87169A6DEE5D1F21B04FDA0C64CC49B68D220CC0F1FD6D486173B588AC6E5AF94B04ABE4D05276C198F6290079F7A4DA6299919B040F64C57C84596C210773352C1159400A4B39767D597CCEEEF004C687F3F163E2E4D9E0F21C645D056A3FB8E7E8E3D7003AF78AE3ADDF75126377C9506A99D6A34337A97C838B42C5533EEDF4A9151B842A569115F247C54C6BE78440FB8DF9140A5F616D3A12E377B1E48814ECFD34F89B44865DC8D0649AA230ECE125EDE01DCD296A262F5384D21F7240AA3CFF59091A624DF50097CA8AE31EE168897F4BCEBC39C314DAA1192D136BE9B8F5A2635574CBF0B34DAEF70EB3BC7340DB464136A7EC888A3CD7CA44BC31CEFF5102FF14AE0CC84681F3F2BBB30252E4EB22A659F553E2F92C7392F7D74AA130304B35D0B0891E152EC4051419F562B27050BD0C72F7C76818194429A97EDBE

----------------------------------------
Building election
----------------------------------------
Initializing public key and commitment hash
Creating context and internal manifest

----------------------------------------
Generating Output
----------------------------------------
Context: /data/out/public_encryption_package/context.json
Constants: /data/out/public_encryption_package/constants.json
Manifest: /data/out/public_encryption_package/manifest.json
Guardian records: /data/out/public_encryption_package/guardians
Guardian private keys: /data/out/test_data_private_guardian_data
WARNING: The files in /data/out/test_data_private_guardian_data are secret and should be protected securely and not shared.
```

```bash
root@29187e5fa3d0:/repo# make eg-e2e-simple-election 2>&1 | tee test.loG

poetry run eg e2e --guardian-count=2 --quorum=2 --manifest=data/election_manifest_simple.json --ballots=data/plaintext_ballots_simple.json --spoil-id=25a7111b-4334-425a-87c1-f7a49f42b3a2 --output-record="./election_record.zip"

----------------------------------------
Retrieving Inputs
----------------------------------------
Name: Jefferson County Spring Primary
Scope: jefferson-county-primary
Geopolitical Units: 4
Parties: 3
Candidates: 6
Contests: 2
Ballot Styles: 4
Guardians: 2
Quorum: 2

----------------------------------------
Performing key ceremony
----------------------------------------
...
Joint Key: E26736623D109FF41983D61923C1F6315B188BCBD76AC71F5B663A504FB4ADEB0A0CDE91D69BBD9797073295F74C2F1D666C419DA6F0B11AA8D5063DA179F3EFB81269CB8D83876BCD69B9147A8AE5346EBF7D8364CCE1FF6E2D68F6BB87C40EA8F54AB1EC3DED43C7F2933E8FCB13B1068F9E24C7B1D66DC2C43B799F2A0CDDB89F6D874E9C221E9B06C848FBCAB2C1011744BACF0B5B467E3CB620C37C37F13026EC957B0CF9DCC0FFA1E1C46BC18DF562E0506E00309378C0CD3D473AD55DB899420468571FF632DA5FCFD85D8DB55CC958BB354766878CBC9E6AFDEBFD0F81CB28ED59EABFC97DCDAF5DBE5CEF9B501AA10F04DAD532A675582262F1820C5F863E41FC06F6EEC1D236D4C2EB4238676E3FE30F18DF8DF82C65F5AF211481756F8FCF041842DE0AE238383845C706E0000DF18FFF50246496714600004675BD96506C5696D771FB304E22A5009808017EAFC75974570E32CD949C98E1F00B82C7B101658D9E613373DC19366062211F8F03B24D79115E3EC91DE813F6C8B6E99E560552F896EDDBA8E1005178D8CD2C25EEEBAE04063787A7A3B6D6A1BC9916BEB813B883910924EFBA3031DBD4A689D399A0121DBAA9981B011AD86F6F6112C2912E20FBE0CF2E45AACF56AC59B6F5FEFE8045E7B503785D906C5FB80C78ED5449B5E19B740F7639BFE35FBAD5D8F8FE81681B7A654D84E65F49FEDE28C8

----------------------------------------
Building election
----------------------------------------
Initializing public key and commitment hash
Creating context and internal manifest

----------------------------------------
Encrypting Ballots
----------------------------------------
Ballots to encrypt: 6
Device location: polling-place
Encrypting ballot: 1048ce32-f1b1-4b05-b7fb-8c615ac842ee
[5888:2025-01-13 15:22:45,640]:INFO:encrypt.py.encrypt:#L123:  encrypt: objectId: 1048ce32-f1b1-4b05-b7fb-8c615ac842ee
[5888:2025-01-13 15:22:45,641]:INFO:encrypt.py.encrypt_ballot:#L477: : manifest_hash : 33A2F06E743408F44DDDC5C9DDA0FCBA867A981C8340ECC272C02D19F4BC6BF5
[5888:2025-01-13 15:22:45,642]:INFO:encrypt.py.encrypt_ballot:#L478: : encryption_seed : C5F8FE9D8C3361D859DB488B480DBB0ED31E4BE1E545592473C63E21BFE6CBAC
[5888:2025-01-13 15:22:45,643]:INFO:encrypt.py.encrypt_selection:#L213: : encrypt_selection: for john-adams-selection hash: 5F67EC2702E62231B840746BF6578453580AFE765C4ADC5C92F67925AE554906
...
Encrypting ballot: 03a29d15-667c-4ac8-afd7-549f19b8e4eb
[5888:2025-01-13 15:22:45,719]:INFO:encrypt.py.encrypt:#L123:  encrypt: objectId: 03a29d15-667c-4ac8-afd7-549f19b8e4eb
[5888:2025-01-13 15:22:45,720]:INFO:encrypt.py.encrypt_ballot:#L477: : manifest_hash : 33A2F06E743408F44DDDC5C9DDA0FCBA867A981C8340ECC272C02D19F4BC6BF5
[5888:2025-01-13 15:22:45,721]:INFO:encrypt.py.encrypt_ballot:#L478: : encryption_seed : C0D357D2FFF3232327FD8E8DCAF21DD751550518970C5B3D8A5395A750305199
[5888:2025-01-13 15:22:45,722]:INFO:encrypt.py.encrypt_selection:#L213: : encrypt_selection: for john-adams-selection hash: 5F67EC2702E62231B840746BF6578453580AFE765C4ADC5C92F67925AE554906
...
Encrypting ballot: 25a7111b-4334-425a-87c1-f7a49f42b3a2
[5888:2025-01-13 15:22:45,796]:INFO:encrypt.py.encrypt:#L123:  encrypt: objectId: 25a7111b-4334-425a-87c1-f7a49f42b3a2
[5888:2025-01-13 15:22:45,797]:INFO:encrypt.py.encrypt_ballot:#L477: : manifest_hash : 33A2F06E743408F44DDDC5C9DDA0FCBA867A981C8340ECC272C02D19F4BC6BF5
[5888:2025-01-13 15:22:45,798]:INFO:encrypt.py.encrypt_ballot:#L478: : encryption_seed : B74F12481C8736136931716871B48ED8C937E714DD930CCAAB529FCD95840ABA
[5888:2025-01-13 15:22:45,800]:INFO:encrypt.py.encrypt_selection:#L213: : encrypt_selection: for john-adams-selection hash: 5F67EC2702E62231B840746BF6578453580AFE765C4ADC5C92F67925AE554906
...
[5888:2025-01-13 15:22:45,868]:INFO:elgamal.py.hashed_elgamal_encrypt:#L260: : mac: 62F358369110D1CAA1312D3BCC2F6265517BC4B2FF9669C0F1B8B531C8E9956F
Encrypting ballot: 69aeacb4-64c6-4205-9bb2-5fb6b3b3ea58
[5888:2025-01-13 15:22:45,873]:INFO:encrypt.py.encrypt:#L123:  encrypt: objectId: 69aeacb4-64c6-4205-9bb2-5fb6b3b3ea58
[5888:2025-01-13 15:22:45,873]:INFO:encrypt.py.encrypt_ballot:#L477: : manifest_hash : 33A2F06E743408F44DDDC5C9DDA0FCBA867A981C8340ECC272C02D19F4BC6BF5
[5888:2025-01-13 15:22:45,874]:INFO:encrypt.py.encrypt_ballot:#L478: : encryption_seed : 7798F0C9A946BC57B73CE74DFE52BEAE9B5F685A06C122B7EC92BA5F4D35C8D7
[5888:2025-01-13 15:22:45,876]:INFO:encrypt.py.encrypt_selection:#L213: : encrypt_selection: for john-adams-selection hash: 5F67EC2702E62231B840746BF6578453580AFE765C4ADC5C92F67925AE554906
...
Encrypting ballot: 5a150c74-a2cb-47f6-b575-165ba8a4ce53
[5888:2025-01-13 15:22:45,991]:INFO:encrypt.py.encrypt:#L123:  encrypt: objectId: 5a150c74-a2cb-47f6-b575-165ba8a4ce53
[5888:2025-01-13 15:22:45,992]:INFO:encrypt.py.encrypt_ballot:#L477: : manifest_hash : 33A2F06E743408F44DDDC5C9DDA0FCBA867A981C8340ECC272C02D19F4BC6BF5
[5888:2025-01-13 15:22:45,993]:INFO:encrypt.py.encrypt_ballot:#L478: : encryption_seed : 6D5A0C77781F18A976BB4DDFCB682FAFF51CC614AA8543CF18004D85E8E662
[5888:2025-01-13 15:22:45,994]:INFO:encrypt.py.encrypt_selection:#L213: : encrypt_selection: for john-adams-selection hash: 5F67EC2702E62231B840746BF6578453580AFE765C4ADC5C92F67925AE554906
...
Encrypting ballot: 9fee0e77-cfd2-401a-a210-93bbc4dd30ef
[5888:2025-01-13 15:22:46,110]:INFO:encrypt.py.encrypt:#L123:  encrypt: objectId: 9fee0e77-cfd2-401a-a210-93bbc4dd30ef
[5888:2025-01-13 15:22:46,110]:INFO:encrypt.py.encrypt_ballot:#L477: : manifest_hash : 33A2F06E743408F44DDDC5C9DDA0FCBA867A981C8340ECC272C02D19F4BC6BF5
[5888:2025-01-13 15:22:46,111]:INFO:encrypt.py.encrypt_ballot:#L478: : encryption_seed : FBE90E1EB3D6D520936FD75595FBB7434CB6FF2C0FC054BF41DD35FFDC5C30F0
[5888:2025-01-13 15:22:46,112]:INFO:encrypt.py.encrypt_selection:#L213: : encrypt_selection: for john-adams-selection hash: 5F67EC2702E62231B840746BF6578453580AFE765C4ADC5C92F67925AE554906
...

----------------------------------------
Submitting Ballots
----------------------------------------
Submitted Ballot Id: 1048ce32-f1b1-4b05-b7fb-8c615ac842ee state: BallotBoxState.CAST
Submitted Ballot Id: 03a29d15-667c-4ac8-afd7-549f19b8e4eb state: BallotBoxState.CAST
Submitted Ballot Id: 25a7111b-4334-425a-87c1-f7a49f42b3a2 state: BallotBoxState.SPOILED
Submitted Ballot Id: 69aeacb4-64c6-4205-9bb2-5fb6b3b3ea58 state: BallotBoxState.CAST
Submitted Ballot Id: 5a150c74-a2cb-47f6-b575-165ba8a4ce53 state: BallotBoxState.CAST
Submitted Ballot Id: 9fee0e77-cfd2-401a-a210-93bbc4dd30ef state: BallotBoxState.CAST

----------------------------------------
Creating Tally
----------------------------------------
Ballots in tally: 6
Spoiled ballots: 1

----------------------------------------
Decrypting tally
----------------------------------------
Cast ballots: 5
Spoiled ballots: 1
Total ballots: 6
Guardian Present: 1
Guardian Present: 2
Lagrange coefficients retrieved: 2

----------------------------------------
Decrypted tally
----------------------------------------

Justice of the Supreme Court
  John Adams: 5
  Benjamin Franklin: 0
  John Hancock: 2
  Write-In: 3

The Pineapple Question
  Pineapple should be banned on pizza: 1
  Pineapple should not be banned on pizza: 1

----------------------------------------
Spoiled ballot '25a7111b-4334-425a-87c1-f7a49f42b3a2'
----------------------------------------

Justice of the Supreme Court
  John Adams: 1
  Benjamin Franklin: 1
  John Hancock: 0
  Write-In: 0

----------------------------------------
Election Record
----------------------------------------
Exported election record to './election_record.zip'
...

----------------------------------------
Retrieving Inputs
----------------------------------------
Name: Jefferson County Spring Primary
Scope: jefferson-county-primary
Geopolitical Units: 4
Parties: 3
Candidates: 6
Contests: 2
Ballot Styles: 4
Guardians: 2
Quorum: 2

----------------------------------------
Performing key ceremony
----------------------------------------
...
Joint Key: E26736623D109FF41983D61923C1F6315B188BCBD76AC71F5B663A504FB4ADEB0A0CDE91D69BBD9797073295F74C2F1D666C419DA6F0B11AA8D5063DA179F3EFB81269CB8D83876BCD69B9147A8AE5346EBF7D8364CCE1FF6E2D68F6BB87C40EA8F54AB1EC3DED43C7F2933E8FCB13B1068F9E24C7B1D66DC2C43B799F2A0CDDB89F6D874E9C221E9B06C848FBCAB2C1011744BACF0B5B467E3CB620C37C37F13026EC957B0CF9DCC0FFA1E1C46BC18DF562E0506E00309378C0CD3D473AD55DB899420468571FF632DA5FCFD85D8DB55CC958BB354766878CBC9E6AFDEBFD0F81CB28ED59EABFC97DCDAF5DBE5CEF9B501AA10F04DAD532A675582262F1820C5F863E41FC06F6EEC1D236D4C2EB4238676E3FE30F18DF8DF82C65F5AF211481756F8FCF041842DE0AE238383845C706E0000DF18FFF50246496714600004675BD96506C5696D771FB304E22A5009808017EAFC75974570E32CD949C98E1F00B82C7B101658D9E613373DC19366062211F8F03B24D79115E3EC91DE813F6C8B6E99E560552F896EDDBA8E1005178D8CD2C25EEEBAE04063787A7A3B6D6A1BC9916BEB813B883910924EFBA3031DBD4A689D399A0121DBAA9981B011AD86F6F6112C2912E20FBE0CF2E45AACF56AC59B6F5FEFE8045E7B503785D906C5FB80C78ED5449B5E19B740F7639BFE35FBAD5D8F8FE81681B7A654D84E65F49FEDE28C8

----------------------------------------
Building election
----------------------------------------
Initializing public key and commitment hash
Creating context and internal manifest

----------------------------------------
Encrypting Ballots
----------------------------------------
Ballots to encrypt: 6
Device location: polling-place
Encrypting ballot: 1048ce32-f1b1-4b05-b7fb-8c615ac842ee
...
Encrypting ballot: 03a29d15-667c-4ac8-afd7-549f19b8e4eb
[5888:2025-01-13 15:22:45,719]:INFO:encrypt.py.encrypt:#L123:  encrypt: objectId: 03a29d15-667c-4ac8-afd7-549f19b8e4eb
[5888:2025-01-13 15:22:45,720]:INFO:encrypt.py.encrypt_ballot:#L477: : manifest_hash : 33A2F06E743408F44DDDC5C9DDA0FCBA867A981C8340ECC272C02D19F4BC6BF5
[5888:2025-01-13 15:22:45,721]:INFO:encrypt.py.encrypt_ballot:#L478: : encryption_seed : C0D357D2FFF3232327FD8E8DCAF21DD751550518970C5B3D8A5395A750305199
[5888:2025-01-13 15:22:45,722]:INFO:encrypt.py.encrypt_selection:#L213: : encrypt_selection: for john-adams-selection hash: 5F67EC2702E62231B840746BF6578453580AFE765C4ADC5C92F67925AE554906
...
Encrypting ballot: 25a7111b-4334-425a-87c1-f7a49f42b3a2
[5888:2025-01-13 15:22:45,796]:INFO:encrypt.py.encrypt:#L123:  encrypt: objectId: 25a7111b-4334-425a-87c1-f7a49f42b3a2
[5888:2025-01-13 15:22:45,797]:INFO:encrypt.py.encrypt_ballot:#L477: : manifest_hash : 33A2F06E743408F44DDDC5C9DDA0FCBA867A981C8340ECC272C02D19F4BC6BF5
[5888:2025-01-13 15:22:45,798]:INFO:encrypt.py.encrypt_ballot:#L478: : encryption_seed : B74F12481C8736136931716871B48ED8C937E714DD930CCAAB529FCD95840ABA
[5888:2025-01-13 15:22:45,800]:INFO:encrypt.py.encrypt_selection:#L213: : encrypt_selection: for john-adams-selection hash: 5F67EC2702E62231B840746BF6578453580AFE765C4ADC5C92F67925AE554906
...
Encrypting ballot: 69aeacb4-64c6-4205-9bb2-5fb6b3b3ea58
[5888:2025-01-13 15:22:45,873]:INFO:encrypt.py.encrypt:#L123:  encrypt: objectId: 69aeacb4-64c6-4205-9bb2-5fb6b3b3ea58
[5888:2025-01-13 15:22:45,873]:INFO:encrypt.py.encrypt_ballot:#L477: : manifest_hash : 33A2F06E743408F44DDDC5C9DDA0FCBA867A981C8340ECC272C02D19F4BC6BF5
[5888:2025-01-13 15:22:45,874]:INFO:encrypt.py.encrypt_ballot:#L478: : encryption_seed : 7798F0C9A946BC57B73CE74DFE52BEAE9B5F685A06C122B7EC92BA5F4D35C8D7
[5888:2025-01-13 15:22:45,876]:INFO:encrypt.py.encrypt_selection:#L213: : encrypt_selection: for john-adams-selection hash: 5F67EC2702E62231B840746BF6578453580AFE765C4ADC5C92F67925AE554906
...
Encrypting ballot: 5a150c74-a2cb-47f6-b575-165ba8a4ce53
[5888:2025-01-13 15:22:45,991]:INFO:encrypt.py.encrypt:#L123:  encrypt: objectId: 5a150c74-a2cb-47f6-b575-165ba8a4ce53
[5888:2025-01-13 15:22:45,992]:INFO:encrypt.py.encrypt_ballot:#L477: : manifest_hash : 33A2F06E743408F44DDDC5C9DDA0FCBA867A981C8340ECC272C02D19F4BC6BF5
[5888:2025-01-13 15:22:45,993]:INFO:encrypt.py.encrypt_ballot:#L478: : encryption_seed : 6D5A0C77781F18A976BB4DDFCB682FAFF51CC614AA8543CF18004D85E8E662
[5888:2025-01-13 15:22:45,994]:INFO:encrypt.py.encrypt_selection:#L213: : encrypt_selection: for john-adams-selection hash: 5F67EC2702E62231B840746BF6578453580AFE765C4ADC5C92F67925AE554906
...
Encrypting ballot: 9fee0e77-cfd2-401a-a210-93bbc4dd30ef
[5888:2025-01-13 15:22:46,110]:INFO:encrypt.py.encrypt:#L123:  encrypt: objectId: 9fee0e77-cfd2-401a-a210-93bbc4dd30ef
[5888:2025-01-13 15:22:46,110]:INFO:encrypt.py.encrypt_ballot:#L477: : manifest_hash : 33A2F06E743408F44DDDC5C9DDA0FCBA867A981C8340ECC272C02D19F4BC6BF5
[5888:2025-01-13 15:22:46,111]:INFO:encrypt.py.encrypt_ballot:#L478: : encryption_seed : FBE90E1EB3D6D520936FD75595FBB7434CB6FF2C0FC054BF41DD35FFDC5C30F0
[5888:2025-01-13 15:22:46,112]:INFO:encrypt.py.encrypt_selection:#L213: : encrypt_selection: for john-adams-selection hash: 5F67EC2702E62231B840746BF6578453580AFE765C4ADC5C92F67925AE554906
...

----------------------------------------
Submitting Ballots
----------------------------------------
Submitted Ballot Id: 1048ce32-f1b1-4b05-b7fb-8c615ac842ee state: BallotBoxState.CAST
Submitted Ballot Id: 03a29d15-667c-4ac8-afd7-549f19b8e4eb state: BallotBoxState.CAST
Submitted Ballot Id: 25a7111b-4334-425a-87c1-f7a49f42b3a2 state: BallotBoxState.SPOILED
Submitted Ballot Id: 69aeacb4-64c6-4205-9bb2-5fb6b3b3ea58 state: BallotBoxState.CAST
Submitted Ballot Id: 5a150c74-a2cb-47f6-b575-165ba8a4ce53 state: BallotBoxState.CAST
Submitted Ballot Id: 9fee0e77-cfd2-401a-a210-93bbc4dd30ef state: BallotBoxState.CAST

----------------------------------------
Creating Tally
----------------------------------------
Ballots in tally: 6
Spoiled ballots: 1

----------------------------------------
Decrypting tally
----------------------------------------
Cast ballots: 5
Spoiled ballots: 1
Total ballots: 6
Guardian Present: 1
Guardian Present: 2
Lagrange coefficients retrieved: 2

----------------------------------------
Decrypted tally
----------------------------------------

Justice of the Supreme Court
  John Adams: 5
  Benjamin Franklin: 0
  John Hancock: 2
  Write-In: 3

The Pineapple Question
  Pineapple should be banned on pizza: 1
  Pineapple should not be banned on pizza: 1

----------------------------------------
Spoiled ballot '25a7111b-4334-425a-87c1-f7a49f42b3a2'
----------------------------------------

Justice of the Supreme Court
  John Adams: 1
  Benjamin Franklin: 1
  John Hancock: 0
  Write-In: 0

----------------------------------------
Election Record
----------------------------------------
Exported election record to './election_record.zip'
```

And here are the contents of the generated `election_record.zip`:

```bash
[jefdaj@nixos:~/myrepos/electionguard-python]$ tree election_record
election_record
├── coefficients.json
├── constants.json
├── context.json
├── encrypted_tally.json
├── encryption_devices
│   └── device_2485377892354.json
├── guardians
│   ├── guardian_1.json
│   └── guardian_2.json
├── manifest.json
├── spoiled_ballots
│   └── spoiled_ballot_25a7111b-4334-425a-87c1-f7a49f42b3a2.json
├── submitted_ballots
│   ├── submitted_ballot_03a29d15-667c-4ac8-afd7-549f19b8e4eb.json
│   ├── submitted_ballot_1048ce32-f1b1-4b05-b7fb-8c615ac842ee.json
│   ├── submitted_ballot_25a7111b-4334-425a-87c1-f7a49f42b3a2.json
│   ├── submitted_ballot_5a150c74-a2cb-47f6-b575-165ba8a4ce53.json
│   ├── submitted_ballot_69aeacb4-64c6-4205-9bb2-5fb6b3b3ea58.json
│   └── submitted_ballot_9fee0e77-cfd2-401a-a210-93bbc4dd30ef.json
└── tally.json

5 directories, 16 files
```
