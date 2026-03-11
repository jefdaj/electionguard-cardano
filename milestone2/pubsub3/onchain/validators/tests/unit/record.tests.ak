use aiken/collection/list
use election/cid as ec
use election/record as er
use tests/data/static_election_records as sr

test all_static_election_cids_valid() {
  let cids: List<ec.CIDv1> =
    list.map(sr.all_records, fn(r) { r.cid })
  list.all(cids, ec.validate_cid)
}

test all_static_election_metadata_valid() {
  let metas: List<er.PublicRecordMetadata> =
    list.map(sr.all_records, fn(r) { r.metadata })
  list.all(metas, er.validate_metadata)
}

test all_static_election_records_valid() {
  list.all(sr.all_records, er.validate_record)
}
