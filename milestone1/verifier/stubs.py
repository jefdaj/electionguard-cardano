def verify_manifest(results, pubdir):
    raise NotImplementedError

def verify_ceremony_details(results, pubdir):
    raise NotImplementedError

def verify_one_guardian_pubkey(results, pubdir):
    ceremony_details = verify(results, pubdir, 'ceremony_details')
    raise NotImplementedError

def verify_one_guardian_backup(results, pubdir):
    one_guardian_pubkey = verify(results, pubdir, 'one_guardian_pubkey')
    raise NotImplementedError

def verify_one_guardian_verification(results, pubdir):
    one_guardian_pubkey = verify(results, pubdir, 'one_guardian_pubkey')
    one_guardian_backup = verify(results, pubdir, 'one_guardian_backup')
    raise NotImplementedError

def verify_joint_key(results, pubdir):
    all_guardian_pubkeys = verify(results, pubdir, 'all_guardian_pubkeys')
    raise NotImplementedError

def verify_constants(results, pubdir):
    build_election = verify(results, pubdir, 'build_election')
    raise NotImplementedError

def verify_context(results, pubdir):
    build_election = verify(results, pubdir, 'build_election')
    raise NotImplementedError

def verify_one_device(results, pubdir):
    raise NotImplementedError

def verify_one_ballot_submitted(results, pubdir):
    one_device = verify(results, pubdir, 'one_device')
    raise NotImplementedError

def verify_one_cast_notice(results, pubdir):
    one_device = verify(results, pubdir, 'one_device')
    one_ballot_submitted = verify(results, pubdir, 'one_ballot_submitted')
    raise NotImplementedError

def verify_one_ballot_spoiled(results, pubdir):
    one_device = verify(results, pubdir, 'one_device')
    one_ballot_submitted = verify(results, pubdir, 'one_ballot_submitted')
    raise NotImplementedError

def verify_ciphertext_tally(results, pubdir):
    context = verify(results, pubdir, 'context')
    internal_manifest = verify(results, pubdir, 'internal_manifest')
    all_ballots_cast = verify(results, pubdir, 'all_ballots_cast')
    raise NotImplementedError

def verify_one_tally_share(results, pubdir):
    one_guardian_pubkey = verify(results, pubdir, 'one_guardian_pubkey')
    context = verify(results, pubdir, 'context')
    ciphertext_tally = verify(results, pubdir, 'ciphertext_tally')
    raise NotImplementedError

def verify_one_spoiled_share(results, pubdir):
    context = verify(results, pubdir, 'context')
    one_ballot_submitted = verify(results, pubdir, 'one_ballot_submitted')
    one_ballot_submitted = verify(results, pubdir, 'one_ballot_submitted')
    one_ballot_spoiled = verify(results, pubdir, 'one_ballot_spoiled')
    raise NotImplementedError

def verify_plaintext_tally(results, pubdir):
    manifest = verify(results, pubdir, 'manifest')
    context = verify(results, pubdir, 'context')
    ciphertext_tally = verify(results, pubdir, 'ciphertext_tally')
    all_tally_shares = verify(results, pubdir, 'all_tally_shares')
    raise NotImplementedError

def verify_one_spoiled_result(results, pubdir):
    manifest = verify(results, pubdir, 'manifest')
    context = verify(results, pubdir, 'context')
    one_ballot_spoiled = verify(results, pubdir, 'one_ballot_spoiled')
    one_ballot_spoiled = verify(results, pubdir, 'one_ballot_spoiled')
    one_spoiled_share = verify(results, pubdir, 'one_spoiled_share')
    one_spoiled_share = verify(results, pubdir, 'one_spoiled_share')
    raise NotImplementedError

def verify_all_guardian_pubkeys(results, pubdir):
    ceremony_details = verify(results, pubdir, 'ceremony_details')
    one_guardian_pubkey = verify(results, pubdir, 'one_guardian_pubkey')
    raise NotImplementedError

def verify_all_ballots_submitted(results, pubdir):
    one_ballot_submitted = verify(results, pubdir, 'one_ballot_submitted')
    raise NotImplementedError

def verify_all_ballots_spoiled(results, pubdir):
    one_ballot_spoiled = verify(results, pubdir, 'one_ballot_spoiled')
    raise NotImplementedError

def verify_all_cast_notices(results, pubdir):
    one_cast_notice = verify(results, pubdir, 'one_cast_notice')
    raise NotImplementedError

def verify_all_spoiled_shares(results, pubdir):
    one_spoiled_share = verify(results, pubdir, 'one_spoiled_share')
    all_guardian_pubkeys = verify(results, pubdir, 'all_guardian_pubkeys')
    raise NotImplementedError

def verify_all_spoiled_results(results, pubdir):
    one_spoiled_result = verify(results, pubdir, 'one_spoiled_result')
    all_guardian_pubkeys = verify(results, pubdir, 'all_guardian_pubkeys')
    raise NotImplementedError

def verify_all_tally_shares(results, pubdir):
    one_tally_share = verify(results, pubdir, 'one_tally_share')
    all_guardian_pubkeys = verify(results, pubdir, 'all_guardian_pubkeys')
    raise NotImplementedError

def verify_build_election(results, pubdir):
    manifest = verify(results, pubdir, 'manifest')
    ceremony_details = verify(results, pubdir, 'ceremony_details')
    joint_key = verify(results, pubdir, 'joint_key')
    raise NotImplementedError

def verify_internal_manifest(results, pubdir):
    build_election = verify(results, pubdir, 'build_election')
    raise NotImplementedError

def verify_all_guardian_backups(results, pubdir):
    ceremony_details = verify(results, pubdir, 'ceremony_details')
    one_guardian_backup = verify(results, pubdir, 'one_guardian_backup')
    raise NotImplementedError

def verify_all_guardian_verifications(results, pubdir):
    ceremony_details = verify(results, pubdir, 'ceremony_details')
    one_guardian_verification = verify(results, pubdir, 'one_guardian_verification')
    raise NotImplementedError

def verify_all_devices(results, pubdir):
    one_device = verify(results, pubdir, 'one_device')
    raise NotImplementedError

def verify_all_ballots_cast(results, pubdir):
    raise NotImplementedError

def verify_gather_announce(results, pubdir):
    manifest = verify(results, pubdir, 'manifest')
    ceremony_details = verify(results, pubdir, 'ceremony_details')
    raise NotImplementedError

def verify_gather_ceremony(results, pubdir):
    ceremony_details = verify(results, pubdir, 'ceremony_details')
    joint_key = verify(results, pubdir, 'joint_key')
    all_guardian_pubkeys = verify(results, pubdir, 'all_guardian_pubkeys')
    all_guardian_backups = verify(results, pubdir, 'all_guardian_backups')
    all_guardian_verifications = verify(results, pubdir, 'all_guardian_verifications')
    raise NotImplementedError

def verify_gather_constants(results, pubdir):
    joint_key = verify(results, pubdir, 'joint_key')
    constants = verify(results, pubdir, 'constants')
    context = verify(results, pubdir, 'context')
    raise NotImplementedError

def verify_gather_config(results, pubdir):
    all_devices = verify(results, pubdir, 'all_devices')
    gather_announce = verify(results, pubdir, 'gather_announce')
    gather_ceremony = verify(results, pubdir, 'gather_ceremony')
    gather_constants = verify(results, pubdir, 'gather_constants')
    raise NotImplementedError

def verify_gather_ballots(results, pubdir):
    all_ballots_submitted = verify(results, pubdir, 'all_ballots_submitted')
    all_ballots_spoiled = verify(results, pubdir, 'all_ballots_spoiled')
    all_cast_notices = verify(results, pubdir, 'all_cast_notices')
    all_spoiled_results = verify(results, pubdir, 'all_spoiled_results')
    raise NotImplementedError

def verify_gather_decryptions(results, pubdir):
    plaintext_tally = verify(results, pubdir, 'plaintext_tally')
    all_spoiled_results = verify(results, pubdir, 'all_spoiled_results')
    raise NotImplementedError

def verify_gather_election(results, pubdir):
    gather_config = verify(results, pubdir, 'gather_config')
    gather_ballots = verify(results, pubdir, 'gather_ballots')
    gather_decryptions = verify(results, pubdir, 'gather_decryptions')
    raise NotImplementedError

