// The first integration test. It'll take the simplest happy path through the
// admin channel lifecycle, not bothering to post valid election artifacts:
//
// - InitElection
// - AdvancePhase (7X)
// - EndElection
//

use tests/integration/happy_adminchannel

test happy_adminchannel_initelection()   { happy_adminchannel.test_initelection()   }
test happy_adminchannel_advancephase_2() { happy_adminchannel.test_advancephase_2() }
test happy_adminchannel_advancephase_3() { happy_adminchannel.test_advancephase_3() }
test happy_adminchannel_advancephase_4() { happy_adminchannel.test_advancephase_4() }
test happy_adminchannel_advancephase_5() { happy_adminchannel.test_advancephase_5() }
test happy_adminchannel_advancephase_6() { happy_adminchannel.test_advancephase_6() }
test happy_adminchannel_advancephase_7() { happy_adminchannel.test_advancephase_7() }
test happy_adminchannel_advancephase_8() { happy_adminchannel.test_advancephase_8() }
test happy_adminchannel_advancephase_9() { happy_adminchannel.test_advancephase_9() }
test happy_adminchannel_endelection()    { happy_adminchannel.test_endelection()    }
