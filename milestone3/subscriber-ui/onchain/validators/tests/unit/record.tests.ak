use aiken/collection/list
use election/types/record as er
use tests/data/static_records as sr

test all_static_election_metadata_valid() {
  let metas: List<er.PublicRecordMetadata> =
    list.map(sr.all_records, fn(r) { r.metadata })
  list.all(metas, er.validate_metadata)
}

test all_static_election_records_valid() {
  list.all(sr.all_records, er.validate_record)
}
