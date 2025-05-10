Multi-container election demo
=============================


This simulates an election locally using Docker containers.

The main script [election.py](./election.py) reads [election.json](./election.json),
spins up the containers using Arion,
and runs `docker exec` commands telling them what to do at each step.

The `data` directory is cleared when starting an election.
Each container can access its own private state in `data/private/<container>`,
and they communicate by saving and loading files in `data/public`.

[Asciinema demo here](https://asciinema.org/a/lloCjFW2LvnqdqKEbQGdySsRC).
Best viewed fullscreen.
It goes fast, but you can pause and scan back and forth as needed.


## Run an election!

Assuming you have Docker and Nix installed,
and Nix flakes enabled, this should work:

```bash
nix develop
time ./election.py
```

You can edit [election.json](./election.json),
re-run [election.py](./election.py) with no arguments,
and check that the final `data/public/3_results/3_summary.json` matches.
It should look something like this.

```json
{
  "Tally of all cast ballots": [
    {
      "question": "Should pineapple be banned on pizza?",
      "votes": {
        "Unsure": 3,
        "No": 2,
        "Yes": 1
      }
    }
  ],
  "Individual spoiled ballots": {
    "9bbf2f04-2d3e-11f0-8c87-0242ac170002": [
      {
        "Should pineapple be banned on pizza?": "Yes"
      }
    ],
    "a2f8bcb8-2d3e-11f0-bcce-0242ac170006": [
      {
        "Should pineapple be banned on pizza?": "Unsure"
      }
    ],
    "9e2db2b0-2d3e-11f0-a790-0242ac170006": [
      {
        "Should pineapple be banned on pizza?": "No"
      }
    ],
    "9f65852c-2d3e-11f0-ad8d-0242ac170003": [
      {
        "Should pineapple be banned on pizza?": "No"
      }
    ],
    "9a8e72de-2d3e-11f0-965b-0242ac170003": [
      {
        "Should pineapple be banned on pizza?": "Yes"
      }
    ],
    "996a0a62-2d3e-11f0-9ef6-0242ac170006": [
      {
        "Should pineapple be banned on pizza?": "Yes"
      }
    ]
  }
}
```

(When it asks for your password, that's to delete `./data`)

TODO can that be done without root?

The rest of the generated data should look something like this.
In [milestone 2](../../milestone2) I plan to post
everything under `data/public` to Cardano + IPFS.
Numbered files/folders will correspond to steps in the smart contract
state machine.

```
data
├── private
│   ├── admin_1
│   ├── device_1
│   │   └── plaintext_ballots
│   │       ├── ballot-50be7912-f2d1-11ef-904e-0242ac140004.json
│   │       ├── ballot-52b19470-f2d1-11ef-932e-0242ac140004.json
│   │       └── ballot-54a19d48-f2d1-11ef-b637-0242ac140004.json
│   ├── device_2
│   │   └── plaintext_ballots
│   │       ├── ballot-513b6936-f2d1-11ef-a4d5-0242ac140006.json
│   │       ├── ballot-532b99b4-f2d1-11ef-a31a-0242ac140006.json
│   │       └── ballot-551fc0a6-f2d1-11ef-b07a-0242ac140006.json
│   ├── device_3
│   │   └── plaintext_ballots
│   │       ├── ballot-51b821ec-f2d1-11ef-934a-0242ac140005.json
│   │       ├── ballot-53aaca0e-f2d1-11ef-9a82-0242ac140005.json
│   │       └── ballot-559b77e6-f2d1-11ef-9801-0242ac140005.json
│   ├── device_4
│   │   └── plaintext_ballots
│   │       ├── ballot-5234960a-f2d1-11ef-aad6-0242ac140009.json
│   │       ├── ballot-5427ab46-f2d1-11ef-b5b1-0242ac140009.json
│   │       └── ballot-561a03f4-f2d1-11ef-ac79-0242ac140009.json
│   ├── guardian_1
│   │   └── election_key_pair.json
│   ├── guardian_2
│   │   └── election_key_pair.json
│   └── guardian_3
│       └── election_key_pair.json
└── public
    ├── 1_announce
    │   ├── 1_manifest.json
    │   └── 2_ceremony.json
    ├── 2_ceremony
    │   ├── 1_pubkeys
    │   │   ├── guardian_1.json
    │   │   ├── guardian_2.json
    │   │   └── guardian_3.json
    │   ├── 2_backups
    │   │   ├── guardian_1_backup_2.json
    │   │   ├── guardian_1_backup_3.json
    │   │   ├── guardian_2_backup_1.json
    │   │   ├── guardian_2_backup_3.json
    │   │   ├── guardian_3_backup_1.json
    │   │   └── guardian_3_backup_2.json
    │   └── 3_verifications
    │       ├── guardian_1_backup_2.json
    │       ├── guardian_1_backup_3.json
    │       ├── guardian_2_backup_1.json
    │       ├── guardian_2_backup_3.json
    │       ├── guardian_3_backup_1.json
    │       └── guardian_3_backup_2.json
    ├── 3_election
    │   ├── constants.json
    │   ├── context.json
    │   └── joint_key.json
    ├── 4_devices
    │   ├── device_1.json
    │   ├── device_2.json
    │   ├── device_3.json
    │   └── device_4.json
    ├── 5_ballots
    │   ├── 1_submitted
    │   │   ├── ballot-50be7912-f2d1-11ef-904e-0242ac140004.json
    │   │   ├── ballot-513b6936-f2d1-11ef-a4d5-0242ac140006.json
    │   │   ├── ballot-51b821ec-f2d1-11ef-934a-0242ac140005.json
    │   │   ├── ballot-5234960a-f2d1-11ef-aad6-0242ac140009.json
    │   │   ├── ballot-52b19470-f2d1-11ef-932e-0242ac140004.json
    │   │   ├── ballot-532b99b4-f2d1-11ef-a31a-0242ac140006.json
    │   │   ├── ballot-53aaca0e-f2d1-11ef-9a82-0242ac140005.json
    │   │   ├── ballot-5427ab46-f2d1-11ef-b5b1-0242ac140009.json
    │   │   ├── ballot-54a19d48-f2d1-11ef-b637-0242ac140004.json
    │   │   ├── ballot-551fc0a6-f2d1-11ef-b07a-0242ac140006.json
    │   │   ├── ballot-559b77e6-f2d1-11ef-9801-0242ac140005.json
    │   │   └── ballot-561a03f4-f2d1-11ef-ac79-0242ac140009.json
    │   ├── 2_cast
    │   │   ├── ballot-513b6936-f2d1-11ef-a4d5-0242ac140006.json
    │   │   ├── ballot-51b821ec-f2d1-11ef-934a-0242ac140005.json
    │   │   ├── ballot-5234960a-f2d1-11ef-aad6-0242ac140009.json
    │   │   ├── ballot-53aaca0e-f2d1-11ef-9a82-0242ac140005.json
    │   │   ├── ballot-5427ab46-f2d1-11ef-b5b1-0242ac140009.json
    │   │   └── ballot-561a03f4-f2d1-11ef-ac79-0242ac140009.json
    │   └── 3_spoiled
    │       ├── ballot-50be7912-f2d1-11ef-904e-0242ac140004.json
    │       ├── ballot-52b19470-f2d1-11ef-932e-0242ac140004.json
    │       ├── ballot-532b99b4-f2d1-11ef-a31a-0242ac140006.json
    │       ├── ballot-54a19d48-f2d1-11ef-b637-0242ac140004.json
    │       ├── ballot-551fc0a6-f2d1-11ef-b07a-0242ac140006.json
    │       └── ballot-559b77e6-f2d1-11ef-9801-0242ac140005.json
    ├── 5_tally.json
    ├── 7_decrypt
    │   ├── 1_shares
    │   │   ├── 1_tally
    │   │   │   ├── tally_guardian_1.json
    │   │   │   ├── tally_guardian_2.json
    │   │   │   └── tally_guardian_3.json
    │   │   └── 2_spoiled
    │   │       ├── ballot-50be7912-f2d1-11ef-904e-0242ac140004_guardian_1.json
    │   │       ├── ballot-50be7912-f2d1-11ef-904e-0242ac140004_guardian_2.json
    │   │       ├── ballot-50be7912-f2d1-11ef-904e-0242ac140004_guardian_3.json
    │   │       ├── ballot-52b19470-f2d1-11ef-932e-0242ac140004_guardian_1.json
    │   │       ├── ballot-52b19470-f2d1-11ef-932e-0242ac140004_guardian_2.json
    │   │       ├── ballot-52b19470-f2d1-11ef-932e-0242ac140004_guardian_3.json
    │   │       ├── ballot-532b99b4-f2d1-11ef-a31a-0242ac140006_guardian_1.json
    │   │       ├── ballot-532b99b4-f2d1-11ef-a31a-0242ac140006_guardian_2.json
    │   │       ├── ballot-532b99b4-f2d1-11ef-a31a-0242ac140006_guardian_3.json
    │   │       ├── ballot-54a19d48-f2d1-11ef-b637-0242ac140004_guardian_1.json
    │   │       ├── ballot-54a19d48-f2d1-11ef-b637-0242ac140004_guardian_2.json
    │   │       ├── ballot-54a19d48-f2d1-11ef-b637-0242ac140004_guardian_3.json
    │   │       ├── ballot-551fc0a6-f2d1-11ef-b07a-0242ac140006_guardian_1.json
    │   │       ├── ballot-551fc0a6-f2d1-11ef-b07a-0242ac140006_guardian_2.json
    │   │       ├── ballot-551fc0a6-f2d1-11ef-b07a-0242ac140006_guardian_3.json
    │   │       ├── ballot-559b77e6-f2d1-11ef-9801-0242ac140005_guardian_1.json
    │   │       ├── ballot-559b77e6-f2d1-11ef-9801-0242ac140005_guardian_2.json
    │   │       └── ballot-559b77e6-f2d1-11ef-9801-0242ac140005_guardian_3.json
    │   └── 2_final
    │       ├── 1_tally.json
    │       └── 2_spoiled
    │           ├── ballot-50be7912-f2d1-11ef-904e-0242ac140004.json
    │           ├── ballot-52b19470-f2d1-11ef-932e-0242ac140004.json
    │           ├── ballot-532b99b4-f2d1-11ef-a31a-0242ac140006.json
    │           ├── ballot-54a19d48-f2d1-11ef-b637-0242ac140004.json
    │           ├── ballot-551fc0a6-f2d1-11ef-b07a-0242ac140006.json
    │           └── ballot-559b77e6-f2d1-11ef-9801-0242ac140005.json
    └── 8_summary.json

32 directories, 93 files
```


## Dev options

```bash
# run one step at a time
# good for debugging
nix develop
./election.py --single-step setup
./election.py --single-step build_manifest
./election.py --single-step ...
./election.py --single-step teardown
```

```bash
# for demos where you want to type on screen
nix develop
./election.py --pause-to-explain
```
