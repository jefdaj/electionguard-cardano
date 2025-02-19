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
│   └── plaintext_ballots
│       ├── ballot-ebd5fc18-ed63-11ef-978c-0242ac110002.json
│       ├── ballot-ec39f9de-ed63-11ef-a185-0242ac110002.json
│       ├── ballot-ec9c72b2-ed63-11ef-bb4a-0242ac110002.json
│       └── ballot-ecfdb900-ed63-11ef-9cb5-0242ac110002.json
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
    ├── 5_ballots
    │   ├── ballot-ebd5fc18-ed63-11ef-978c-0242ac110002.json
    │   ├── ballot-ec39f9de-ed63-11ef-a185-0242ac110002.json
    │   ├── ballot-ec9c72b2-ed63-11ef-bb4a-0242ac110002.json
    │   └── ballot-ecfdb900-ed63-11ef-9cb5-0242ac110002.json
    └── 6_spoiled
        ├── ballot-ec9c72b2-ed63-11ef-bb4a-0242ac110002.json
        └── ballot-ecfdb900-ed63-11ef-9cb5-0242ac110002.json
```

The session output should look something like this.

```
2025-02-19 16:19:55,586
poetry run /repo/multiscript_election/admin.py build-manifest --public-records-dir /repo/multiscript_election/public_record --referendum-question Are pineapples still cool?

2025-02-19 16:19:56,058
poetry run /repo/multiscript_election/admin.py announce-key-ceremony --guardian-count 3 --quorum 2 --public-records-dir /repo/multiscript_election/public_record

2025-02-19 16:19:56,544
poetry run /repo/multiscript_election/guardian.py key-ceremony --guardian-count 3 --quorum 2 --public-records-dir /repo/multiscript_election/public_record --private-records-dir /repo/multiscript_election/private_records --guardian-id guardian_1 --guardian-sequence-order 1 --current-round 1

2025-02-19 16:19:56,954
poetry run /repo/multiscript_election/guardian.py key-ceremony --guardian-count 3 --quorum 2 --public-records-dir /repo/multiscript_election/public_record --private-records-dir /repo/multiscript_election/private_records --guardian-id guardian_2 --guardian-sequence-order 2 --current-round 1

2025-02-19 16:19:57,355
poetry run /repo/multiscript_election/guardian.py key-ceremony --guardian-count 3 --quorum 2 --public-records-dir /repo/multiscript_election/public_record --private-records-dir /repo/multiscript_election/private_records --guardian-id guardian_3 --guardian-sequence-order 3 --current-round 1

2025-02-19 16:19:57,773
poetry run /repo/multiscript_election/guardian.py key-ceremony --guardian-count 3 --quorum 2 --public-records-dir /repo/multiscript_election/public_record --private-records-dir /repo/multiscript_election/private_records --guardian-id guardian_1 --guardian-sequence-order 1 --current-round 2

2025-02-19 16:19:58,192
poetry run /repo/multiscript_election/guardian.py key-ceremony --guardian-count 3 --quorum 2 --public-records-dir /repo/multiscript_election/public_record --private-records-dir /repo/multiscript_election/private_records --guardian-id guardian_2 --guardian-sequence-order 2 --current-round 2

2025-02-19 16:19:58,614
poetry run /repo/multiscript_election/guardian.py key-ceremony --guardian-count 3 --quorum 2 --public-records-dir /repo/multiscript_election/public_record --private-records-dir /repo/multiscript_election/private_records --guardian-id guardian_3 --guardian-sequence-order 3 --current-round 2

2025-02-19 16:19:59,048
poetry run /repo/multiscript_election/guardian.py key-ceremony --guardian-count 3 --quorum 2 --public-records-dir /repo/multiscript_election/public_record --private-records-dir /repo/multiscript_election/private_records --guardian-id guardian_1 --guardian-sequence-order 1 --current-round 3

2025-02-19 16:19:59,472
poetry run /repo/multiscript_election/guardian.py key-ceremony --guardian-count 3 --quorum 2 --public-records-dir /repo/multiscript_election/public_record --private-records-dir /repo/multiscript_election/private_records --guardian-id guardian_2 --guardian-sequence-order 2 --current-round 3

2025-02-19 16:19:59,892
poetry run /repo/multiscript_election/guardian.py key-ceremony --guardian-count 3 --quorum 2 --public-records-dir /repo/multiscript_election/public_record --private-records-dir /repo/multiscript_election/private_records --guardian-id guardian_3 --guardian-sequence-order 3 --current-round 3

2025-02-19 16:20:00,312
poetry run /repo/multiscript_election/admin.py publish-joint-key --public-records-dir /repo/multiscript_election/public_record

2025-02-19 16:20:00,818
poetry run /repo/multiscript_election/admin.py build-election --guardian-count 3 --quorum 2 --public-records-dir /repo/multiscript_election/public_record

2025-02-19 16:20:01,321
poetry run /repo/multiscript_election/device.py add-device --public-records-dir /repo/multiscript_election/public_record

2025-02-19 16:20:01,831
poetry run /repo/multiscript_election/device.py vote --guardian-count 3 --quorum 2 --public-records-dir /repo/multiscript_election/public_record --private-records-dir /repo/multiscript_election/private_records --candidate-id referendum-question-affirmative-selection --spoil False

2025-02-19 16:20:02,440
poetry run /repo/multiscript_election/device.py vote --guardian-count 3 --quorum 2 --public-records-dir /repo/multiscript_election/public_record --private-records-dir /repo/multiscript_election/private_records --candidate-id referendum-question-negative-selection --spoil False

2025-02-19 16:20:03,046
poetry run /repo/multiscript_election/device.py vote --guardian-count 3 --quorum 2 --public-records-dir /repo/multiscript_election/public_record --private-records-dir /repo/multiscript_election/private_records --candidate-id referendum-question-affirmative-selection --spoil True

2025-02-19 16:20:03,649
poetry run /repo/multiscript_election/device.py vote --guardian-count 3 --quorum 2 --public-records-dir /repo/multiscript_election/public_record --private-records-dir /repo/multiscript_election/private_records --candidate-id referendum-question-negative-selection --spoil True

{[37m[39;49;00m
[37m  [39;49;00m[94m"guardian_count"[39;49;00m:[37m [39;49;00m[34m3[39;49;00m,[37m[39;49;00m
[37m  [39;49;00m[94m"quorum"[39;49;00m:[37m [39;49;00m[34m2[39;49;00m,[37m[39;49;00m
[37m  [39;49;00m[94m"public_records_dir"[39;49;00m:[37m [39;49;00m[33m"/repo/multiscript_election/public_record"[39;49;00m,[37m[39;49;00m
[37m  [39;49;00m[94m"private_records_dir"[39;49;00m:[37m [39;49;00m[33m"/repo/multiscript_election/private_records"[39;49;00m,[37m[39;49;00m
[37m  [39;49;00m[94m"candidate_id"[39;49;00m:[37m [39;49;00m[33m"referendum-question-affirmative-selection"[39;49;00m,[37m[39;49;00m
[37m  [39;49;00m[94m"spoil"[39;49;00m:[37m [39;49;00m[34mfalse[39;49;00m[37m[39;49;00m
}[37m[39;49;00m

{[37m[39;49;00m
[37m  [39;49;00m[94m"guardian_count"[39;49;00m:[37m [39;49;00m[34m3[39;49;00m,[37m[39;49;00m
[37m  [39;49;00m[94m"quorum"[39;49;00m:[37m [39;49;00m[34m2[39;49;00m,[37m[39;49;00m
[37m  [39;49;00m[94m"public_records_dir"[39;49;00m:[37m [39;49;00m[33m"/repo/multiscript_election/public_record"[39;49;00m,[37m[39;49;00m
[37m  [39;49;00m[94m"private_records_dir"[39;49;00m:[37m [39;49;00m[33m"/repo/multiscript_election/private_records"[39;49;00m,[37m[39;49;00m
[37m  [39;49;00m[94m"candidate_id"[39;49;00m:[37m [39;49;00m[33m"referendum-question-negative-selection"[39;49;00m,[37m[39;49;00m
[37m  [39;49;00m[94m"spoil"[39;49;00m:[37m [39;49;00m[34mfalse[39;49;00m[37m[39;49;00m
}[37m[39;49;00m

{[37m[39;49;00m
[37m  [39;49;00m[94m"guardian_count"[39;49;00m:[37m [39;49;00m[34m3[39;49;00m,[37m[39;49;00m
[37m  [39;49;00m[94m"quorum"[39;49;00m:[37m [39;49;00m[34m2[39;49;00m,[37m[39;49;00m
[37m  [39;49;00m[94m"public_records_dir"[39;49;00m:[37m [39;49;00m[33m"/repo/multiscript_election/public_record"[39;49;00m,[37m[39;49;00m
[37m  [39;49;00m[94m"private_records_dir"[39;49;00m:[37m [39;49;00m[33m"/repo/multiscript_election/private_records"[39;49;00m,[37m[39;49;00m
[37m  [39;49;00m[94m"candidate_id"[39;49;00m:[37m [39;49;00m[33m"referendum-question-affirmative-selection"[39;49;00m,[37m[39;49;00m
[37m  [39;49;00m[94m"spoil"[39;49;00m:[37m [39;49;00m[34mtrue[39;49;00m[37m[39;49;00m
}[37m[39;49;00m

{[37m[39;49;00m
[37m  [39;49;00m[94m"guardian_count"[39;49;00m:[37m [39;49;00m[34m3[39;49;00m,[37m[39;49;00m
[37m  [39;49;00m[94m"quorum"[39;49;00m:[37m [39;49;00m[34m2[39;49;00m,[37m[39;49;00m
[37m  [39;49;00m[94m"public_records_dir"[39;49;00m:[37m [39;49;00m[33m"/repo/multiscript_election/public_record"[39;49;00m,[37m[39;49;00m
[37m  [39;49;00m[94m"private_records_dir"[39;49;00m:[37m [39;49;00m[33m"/repo/multiscript_election/private_records"[39;49;00m,[37m[39;49;00m
[37m  [39;49;00m[94m"candidate_id"[39;49;00m:[37m [39;49;00m[33m"referendum-question-negative-selection"[39;49;00m,[37m[39;49;00m
[37m  [39;49;00m[94m"spoil"[39;49;00m:[37m [39;49;00m[34mtrue[39;49;00m[37m[39;49;00m
}[37m[39;49;00m
```
