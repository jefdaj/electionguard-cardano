// Test posting public records from the admin channel or a subchannel.

use election/action
use tests/integration/happy_postpublicrecords
use tests/mock

test happy_postpublicrecords_admin() {
  mock.election_validate(
    happy_postpublicrecords.admin_tx(),
    action.PostPublicRecords
  )
}

test happy_postpublicrecords_subchannel() {
  mock.election_validate(
    happy_postpublicrecords.sub_tx(),
    action.PostPublicRecords
  )
}
