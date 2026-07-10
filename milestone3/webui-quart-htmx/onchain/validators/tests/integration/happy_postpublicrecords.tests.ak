// Test posting public records from the admin channel or a subchannel.

use tests/integration/happy_postpublicrecords

test happy_postpublicrecords_admin()      { happy_postpublicrecords.test_admin()      }
test happy_postpublicrecords_subchannel() { happy_postpublicrecords.test_subchannel() }
