MockChain + Local IPFS (Parallel)
=================================

This is kind of a bonus quest: can the [mockchain + local IPFS demo](../mockchain-local-ipfs) be made parallel?
It isn't required for anything in the fund13 project, but will be useful for testing scaling later.
I'm making a little detour to work on it now because I suspect it will also help clarify the [smart contract](../smart-contract) design.

The answer is... yes!
It turns out to be pretty straightforward and works the way I expected: all
containers can do a given protocol step in parallel, as long as they wait
before doing the next step. There are some actions (for example minting
channels and posting cast/spoil notices) that could also be extended outside
their given step, but that's for later.

```
============================= test session starts ==============================
...

election.py::test_json_voteconfig <- config.py PASSED                    [  2%]
election.py::test_json_contestconfig <- config.py PASSED                 [  5%]
election.py::test_json_electionconfig <- config.py PASSED                [  7%]
election.py::test_json_honestrun <- config.py PASSED                     [ 10%]
election.py::test_honest_always_verified PASSED                          [ 13%]
election.py::test_honest_all_verifiers_agree_exactly PASSED              [ 15%]
election.py::test_honest_n_verifications_matches_cfg PASSED              [ 18%]
election.py::test_honest_cast_votes_match_config PASSED                  [ 21%]
election.py::test_honest_spoiled_votes_match_config PASSED               [ 23%]
election.py::test_honest_manifest_verified PASSED                        [ 26%]
election.py::test_honest_ceremony_details_verified PASSED                [ 28%]
election.py::test_honest_gather_announce_verified PASSED                 [ 31%]
election.py::test_honest_all_guardian_backups_verified PASSED            [ 34%]
election.py::test_honest_all_guardian_verifications_verified PASSED      [ 36%]
election.py::test_honest_gather_ceremony_verified PASSED                 [ 39%]
election.py::test_honest_joint_key_verified PASSED                       [ 42%]
election.py::test_honest_build_election_verified PASSED                  [ 44%]
election.py::test_honest_constants_verified PASSED                       [ 47%]
election.py::test_honest_context_verified PASSED                         [ 50%]
election.py::test_honest_gather_constants_verified PASSED                [ 52%]
election.py::test_honest_all_devices_verified PASSED                     [ 55%]
election.py::test_honest_gather_config_verified PASSED                   [ 57%]
election.py::test_honest_all_ballots_submitted_verified PASSED           [ 60%]
election.py::test_honest_all_ballots_cast_verified PASSED                [ 63%]
election.py::test_honest_all_ballots_spoiled_verified PASSED             [ 65%]
election.py::test_honest_all_spoiled_results_verified PASSED             [ 68%]
election.py::test_honest_n_spoiled_decrypted_verified PASSED             [ 71%]
election.py::test_honest_n_cast_spoiled_submitted_verified PASSED        [ 73%]
election.py::test_honest_set_spoiled_decrypted_verified PASSED           [ 76%]
election.py::test_honest_set_cast_spoiled_submitted_verified PASSED      [ 78%]
election.py::test_honest_ballot_sets_verified PASSED                     [ 81%]
election.py::test_honest_ciphertext_tally_verified PASSED                [ 84%]
election.py::test_honest_tally_aggregation_verified PASSED               [ 86%]
election.py::test_honest_plaintext_tally_verified PASSED                 [ 89%]
election.py::test_honest_tally_decryption_verified PASSED                [ 92%]
election.py::test_honest_gather_tally_verified PASSED                    [ 94%]
election.py::test_honest_gather_decryptions_verified PASSED              [ 97%]
election.py::test_honest_gather_election_verified PASSED                 [100%]

======================= 38 passed in 2029.72s (0:33:49) ========================
```
