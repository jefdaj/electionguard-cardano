# multiscript election

This has one script per party and they coordinate via a shared `public_record`
folder on the local filesystem.

In this first version, I'll just have the main script call the others
repeatedly and tell them which phase/round of the protocol to run each time.
Later they should all be running at the same time and figuring it out
themselves as files are added to the shared folder. Then eventually the Cardano
blockchain will replace the shared folder.

I've skipped round 4 of the ceremony (backup verification challenges) for now.
I'm not sure it needs to be done for this demo at all, because 1) the guardians
aren't going to be properly decentralized anyway, and 2) if one of the
verifications fails we can just restart the ceremony. The ElectionGuard authors
did the same thing (TODO find citation).

Anyway, you run `main.py` like this.

```bash
# from the host system
./makefile-docker-env.sh

# from the container shell
./multiscript_election/main.py
```

And it should generate files like these:

```
multiscript_election/
├── private_records
│   ├── guardian_keys
│   │   ├── guardian_1.json
│   │   ├── guardian_2.json
│   │   └── guardian_3.json
│   ├── plaintext_ballots
│   │   ├── ballot-fed89c46-ed61-11ef-a311-0242ac110002.json
│   │   ├── ballot-ff375498-ed61-11ef-b48e-0242ac110002.json
│   │   ├── ballot-ff9876e2-ed61-11ef-89c5-0242ac110002.json
│   │   └── ballot-fff9985a-ed61-11ef-8e77-0242ac110002.json
│   └── spoiled_ballot_nonces
│       ├── ballot-ff9876e2-ed61-11ef-89c5-0242ac110002.json
│       └── ballot-fff9985a-ed61-11ef-8e77-0242ac110002.json
└── public_record
    ├── 1_manifest.json
    ├── 2_ceremony
    │   ├── 0_announce.json
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
    │   ├── 3_verifications
    │   │   ├── guardian_1_backup_2.json
    │   │   ├── guardian_1_backup_3.json
    │   │   ├── guardian_2_backup_1.json
    │   │   ├── guardian_2_backup_3.json
    │   │   ├── guardian_3_backup_1.json
    │   │   └── guardian_3_backup_2.json
    │   └── 5_joint_key.json
    ├── 3_election
    │   ├── constants.json
    │   └── context.json
    ├── 4_devices
    │   └── device_2485377892354.json
    └── 5_ballots
        ├── ballot-fed89c46-ed61-11ef-a311-0242ac110002.json
        ├── ballot-ff375498-ed61-11ef-b48e-0242ac110002.json
        ├── ballot-ff9876e2-ed61-11ef-89c5-0242ac110002.json
        └── ballot-fff9985a-ed61-11ef-8e77-0242ac110002.json
```
