// Second integration test: simplest happy path through the lifecycle of a subchannel.
// Builds on the admin channel tests in validators/tests/integration/minimal.tests.ak.

use tests/integration/happy_subchannel

test happy_subchannel_single_add() { happy_subchannel.test_single_add() }
test happy_subchannel_single_rm()  { happy_subchannel.test_single_rm()  }
test happy_subchannel_multi_add()  { happy_subchannel.test_multi_add()  }
test happy_subchannel_multi_rm()   { happy_subchannel.test_multi_rm()   }
