// Test posting public records from the admin channel or a subchannel.
// Separating the tests like this seems to get around Aiken's test module
// re-use restrictions.

// TODO ask about it and request they be removed?

use tests/integration/happy_postpublicrecords as hp

test happy_postpublicrecords_admin() {
  hp.test_happy_postpublicrecords_admin()
}

test happy_postpublicrecords_subchannel() {
  hp.test_happy_postpublicrecords_subchannel()
}
