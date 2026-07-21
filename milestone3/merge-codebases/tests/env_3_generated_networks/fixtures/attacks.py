# name of an attack function
# AttackFnName = str

# class AttackConfig(list):
#     def __init__(self, attacks: List[AttackFnName]):
#         super(AttackConfig, self).__init__()
#         for fn_name in attacks:
#             self.append(fn_name)


# TODO rewrite these to work with current codebase
# This has to be defined in a separate file from the actual attack functions
# (they live in egpy_scripts/attack.py) because they run in electionguard-python
# containers, whereas this runs on the host system and will not necessarily be
# able to import the electionguard module.
# ATTACKS = {
#
#     'admin_ghost_after_vote'           : {'who': 'admin', 'when': ['tally', 'decrypt_results']},
#     'admin_withhold_manifest'          : {'who': 'admin', 'when': ['build_manifest']},
#     'device_mutate_spoiled_ballot'     : {'who': 'device', 'when': ['vote_reveal_all']},
#     'device_mutate_submitted_ballot'   : {'who': 'device', 'when': ['vote_commit_all']},
#     'device_withhold_cast_ballot'      : {'who': 'device', 'when': ['vote_reveal_all']},
#     'device_withhold_spoiled_ballot'   : {'who': 'device', 'when': ['vote_reveal_all']},
#     'device_withhold_submitted_ballot' : {'who': 'device', 'when': ['vote_commit_all']},
#     'guardian_withhold_spoiled_share'  : {'who': 'guardian', 'when': ['decrypt_shares']},
#     'guardian_withhold_tally_share'    : {'who': 'guardian', 'when': ['decrypt_shares']},
#
#     # Things NOT checked/caught in the current implementation:
#     # 'admin_mutate_constants' : {'who': 'admin' , 'when': ['build_election']},
#
# }



