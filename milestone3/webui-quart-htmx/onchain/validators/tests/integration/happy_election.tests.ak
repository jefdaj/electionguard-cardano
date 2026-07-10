// Happy path through a full election, posting statically generated CIDs.

use tests/integration/happy_election

test happy_election_admin_tx0() { happy_election.test_admin_tx0() }
test happy_election_admin_tx1() { happy_election.test_admin_tx1() }
test happy_election_admin_tx2() { happy_election.test_admin_tx2() }
test happy_election_admin_tx3() { happy_election.test_admin_tx3() }
test happy_election_admin_tx4() { happy_election.test_admin_tx4() }
test happy_election_admin_tx5() { happy_election.test_admin_tx5() }
test happy_election_admin_tx6() { happy_election.test_admin_tx6() }
test happy_election_admin_tx7() { happy_election.test_admin_tx7() }

test happy_election_guardian1_tx1() { happy_election.test_guardian1_tx1() }
test happy_election_guardian1_tx2() { happy_election.test_guardian1_tx2() }
test happy_election_guardian1_tx3() { happy_election.test_guardian1_tx3() }
test happy_election_guardian1_tx4() { happy_election.test_guardian1_tx4() }
test happy_election_guardian1_tx5() { happy_election.test_guardian1_tx5() }

test happy_election_guardian2_tx1() { happy_election.test_guardian2_tx1() }
test happy_election_guardian2_tx2() { happy_election.test_guardian2_tx2() }
test happy_election_guardian2_tx3() { happy_election.test_guardian2_tx3() }
test happy_election_guardian2_tx4() { happy_election.test_guardian2_tx4() }
test happy_election_guardian2_tx5() { happy_election.test_guardian2_tx5() }

test happy_election_guardian3_tx1() { happy_election.test_guardian3_tx1() }
test happy_election_guardian3_tx2() { happy_election.test_guardian3_tx2() }
test happy_election_guardian3_tx3() { happy_election.test_guardian3_tx3() }
test happy_election_guardian3_tx4() { happy_election.test_guardian3_tx4() }
test happy_election_guardian3_tx5() { happy_election.test_guardian3_tx5() }

test happy_election_device1_tx1() { happy_election.test_device1_tx1() }
test happy_election_device1_tx2() { happy_election.test_device1_tx2() }
test happy_election_device1_tx3() { happy_election.test_device1_tx3() }

test happy_election_verifier1_tx1() { happy_election.test_verifier1_tx1() }

test happy_election_admin_tx8() { happy_election.test_admin_tx8() }
test happy_election_admin_tx9() { happy_election.test_admin_tx9() }
