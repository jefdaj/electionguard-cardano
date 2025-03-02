# Smart Contract Architecture

Just some initial ideas.

Phase 1, setup:
    - Admin announces election
        - mints admin state NFT
        - mints election state NFT
    - Admin adds guardians
        - gets cardano addresses from QR codes or pasted into CLI
        - mints one state NFT per guardian
        - sends some tADA to the NFT to pay the guardian's fees
        - can also revoke guardians here?
        - require guardians to announce presence?
        - admin has to do the initial transitino into the ceremony phase before guardian can use theirs
    - Admin announces ceremony details
        - require n guardians ≤ n guardian state NFTs
        - require 1 ≤ quorum ≤ n guardians?
    - Key ceremony
        - round 1: guardians publish pubkeys
        - round 2: guardians publish backup shares
        - round 3: guardians confirm backup shares
    - Admin publishes election details
    - Admin adds encryption devices
        - mints one state NFT per device
        - same basic idea as with guardians above
        - admin has to do initial transition into voting phase before devices can post anything
        - amount sent for fees should scale with the expected votes each device will service
        - when can this be done? any time during the setup phase?

Phase 2, voting:
    - devices post ballots:
        - submitted
        - cast/spoiled
        - mark as timed out if voter makes no cast/spoil decision
        - can guardians decrypt spoiled ones in real time here?
    - admin closes voting
        - can be early, but only if everyone has voted
        - if they don't, should it just progress after the deadline anyway?
        - burns device state NFTs
        - what happens to any pending votes?

Phase 3, tally:
    - guardians post decryption shares
        - of final tally
        - of each spoiled ballot
    - admin combines them
        - posts final decrypted tally
        - posts short summary too

Phase 4, dispute resolution:
    - observers (anyone) post verifications
        - obviously needs to have some collateral later, or something
    - will this also end up being dispute resolution time?
        - no need to hold up the votes for disputes, unless there are large irregularities
        - but do need to decide who gets money for various things
    - and it can also be risk limiting audit time if needed
    - no need for anything in the demo other than a simple verification
    - simple incentives for a first draft later:
        - first N people to post certifications get rewards
            - unless they miss a failure, then it costs them their collateral to not have checked
        - first N people to post irregularities/failure get rewards
            - but only if they correctly identify the failure, not for generically saying it failed
            - and not if it actually succeeded of course

All the NFTs are "state NFTs" (may not be the right word?): their owners are
coded in the datum and can't be changed, and the NFT just tracks which UTXO
carries the current state. So they aren't really sent, just created and then
used by their owners.

Cool idea but out of scope for now: run a simultaneous prediction market on the results being valid!
Leave it to the narrow technical definition of valid that could be checked by observers to incentivize running an observer node.

Also for later: come up with a list of provable, slashable offenses.
Some ideas:
- guardian decyrption share of something they weren't supposed to decrypt
- any message signed by an encryption device which isn't on chain by the end of the voting process
    - would include messages shown to a voter but not actually posted on chain
    - only if they've posted something else afterward? to catch the case when they just fail/go offline
        - except maybe that should be slashable too?
- contradictory ballot messages from encryption device (challenge/spoil/timeout)
- guardian failure to appear for decryption
- for any device, failure to share the IPFS file corresponding to a CID they signed
    - but how to enforce this? i guess it needs a challenge and response period or something?
- for any device, uploading an IPFS file that doesn't fit one of the valid schemas
    - needs some sort of DON or "disciplinary council" or something to enforce?
