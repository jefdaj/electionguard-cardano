// Generated with static_records.py
// Consider editing and re-running that to make any changes.

use aiken/primitive/string.{to_bytearray}
use election/types/record as er

pub const manifest = er.PublicRecord {
  // orig base32: bafkreiat5mhmsrevctm43qlv6aokrli3cdoj2aqyb34wsf6idybuvzwtua
  ipfs_cid: #"0155122013eb0ec9449514d9cdc175f01ca8ad1b10dc9d02180ef96917c81e034ae6d3a0",
  metadata: er.Manifest
}

pub const ceremony_details = er.PublicRecord {
  // orig base32: bafkreiampwehpnmfwiexflsuqrmythwm5y7b375ypjt64qbwtx5altmrby
  ipfs_cid: #"015512200c7d8877b585b20972ae548459899eccee3e1dffb87a67ee40369dfa05cd910e",
  metadata: er.CeremonyDetails
}

pub const guardian3_pubkey = er.PublicRecord {
  // orig base32: bafkreifgfszdehl7ibjxlxa6crbwa5efjb54l42w6pinvxkaysq2jmd7rm
  ipfs_cid: #"01551220a62cb2321d7f405375dc1e1443607485487bc5f356f3d0dadd40c4a1a4b07f8b",
  metadata: er.GuardianPubkey { guardian_number: 3 }
}

pub const guardian2_pubkey = er.PublicRecord {
  // orig base32: bafkreigyyiyxo2azcluqyvjkawd2efcfxpxpdoma6slac4iczy6mld3gry
  ipfs_cid: #"01551220d8c23177681912e90c552a0587a21445bbeef1b980f496017102ce3cc58f668e",
  metadata: er.GuardianPubkey { guardian_number: 2 }
}

pub const guardian1_pubkey = er.PublicRecord {
  // orig base32: bafkreie7o7gqsmdpmxroyhjdv7kmdagdyldbjjka4c4wipnocmpzkv3y4y
  ipfs_cid: #"015512209f77cd09306f65e2ec1d23afd4c180c3c2c614a540e0b9643dae131f955778e6",
  metadata: er.GuardianPubkey { guardian_number: 1 }
}

pub const guardian3_backup1 = er.PublicRecord {
  // orig base32: bafkreifenb77eurcoizeqacvavt25jxpyc2hgvy2pmrldbjsyidbg6qyqu
  ipfs_cid: #"01551220a4687ff2522272324800550567aea6efc0b473571a7b22b18532c206137a1885",
  metadata: er.GuardianBackup { guardian_number: 3, backup_order: 1 }
}

pub const guardian2_backup1 = er.PublicRecord {
  // orig base32: bafkreihi6toi5noxmi2xcparo7v3qftb7o7d7qdya77ufm6ed6bpqzopwi
  ipfs_cid: #"01551220e8f4dc8eb5d76235713c1177ebb81661fbbe3fc07807ff42b3c41f82f865cfb2",
  metadata: er.GuardianBackup { guardian_number: 2, backup_order: 1 }
}

pub const guardian1_backup2 = er.PublicRecord {
  // orig base32: bafkreidx2d2fz6pnt7ijntvic7m45evsalaecmg3knsmgtufjjdxinbedm
  ipfs_cid: #"0155122077d0f45cf9ed9fd096cea817d9ce92b202c04130db5364c34e854a477434241b",
  metadata: er.GuardianBackup { guardian_number: 1, backup_order: 2 }
}

pub const guardian3_backup2 = er.PublicRecord {
  // orig base32: bafkreiezp6rxp3ln7ha7malo7ywwj3akwpznox74zez43lbtakmmnj643q
  ipfs_cid: #"01551220997fa377ed6df9c1f6016efe2d64ec0ab3f2d75ffcc933cdac330298c6a7dcdc",
  metadata: er.GuardianBackup { guardian_number: 3, backup_order: 2 }
}

pub const guardian1_backup3 = er.PublicRecord {
  // orig base32: bafkreiasorbdlynbjqdodidkcq5vybquuxyjiyfhy6u3fluzfalnrx7uiu
  ipfs_cid: #"0155122012744235e1a14c06e1a06a143b5c0614a5f09460a7c7a9b2ae992816d8dff445",
  metadata: er.GuardianBackup { guardian_number: 1, backup_order: 3 }
}

pub const guardian2_backup3 = er.PublicRecord {
  // orig base32: bafkreicyiqaeqtckhxzk7lebtkqobvanh55stoeup57lyf4a7hk6xhfpne
  ipfs_cid: #"01551220584400484c4a3df2afac819aa0e0d40d3f7b29b8947f7ebc1780f9d5eb9caf69",
  metadata: er.GuardianBackup { guardian_number: 2, backup_order: 3 }
}

pub const guardian1_verification2 = er.PublicRecord {
  // orig base32: bafkreigttkxiwi77w77wkoa22yqxtvngxwj7mceva2auuokxj4plaoyhw4
  ipfs_cid: #"01551220d39aae8b23ffb7ff65381ad62179d5a6bd93f6089506814a39574f1eb03b07b7",
  metadata: er.GuardianVerification { guardian_number: 1, backup_order: 2 }
}

pub const guardian2_verification1 = er.PublicRecord {
  // orig base32: bafkreiahc2ihahmjf47vi2xljttek6ew2drsbnzxoiqsscqeoiuj63d3qy
  ipfs_cid: #"01551220071690701d892f3f546aeb4ce6457896d0e320b7377221290a0472289f6c7b86",
  metadata: er.GuardianVerification { guardian_number: 2, backup_order: 1 }
}

pub const guardian1_verification3 = er.PublicRecord {
  // orig base32: bafkreifzmluosaq5i42wepacnjm5baep2ijdnc3rof3mo63ysp63sunrju
  ipfs_cid: #"01551220b962e8e9021d4735623c026a59d0808fd212368b717176c77b7893fdb951b14d",
  metadata: er.GuardianVerification { guardian_number: 1, backup_order: 3 }
}

pub const guardian3_verification1 = er.PublicRecord {
  // orig base32: bafkreif76kzib6azzj6g5vjjllgotbloc5gjiyd4huwet243zlzs2jkhia
  ipfs_cid: #"01551220bff2b280f819ca7c6ed5295acce9856e174c94607c3d2c49eb9bcaf32d254740",
  metadata: er.GuardianVerification { guardian_number: 3, backup_order: 1 }
}

pub const guardian2_verification3 = er.PublicRecord {
  // orig base32: bafkreierpscqxdl53de3hwxxltnupfpze3ydmzylety5epq6s26cf5u2a4
  ipfs_cid: #"01551220917c850b8d7dd8c9b3daf75cdb4795f926f036670b24f1d23e1e96bc22f69a07",
  metadata: er.GuardianVerification { guardian_number: 2, backup_order: 3 }
}

pub const guardian3_verification2 = er.PublicRecord {
  // orig base32: bafkreiaazza6gn6parx2glf7brj64rckr3ixruw4h5negtxi3wvbiwxuye
  ipfs_cid: #"0155122000ce41e337cf046fa32cbf0c53ee444a8ed178d2dc3f5a434ee8ddaa145af4c1",
  metadata: er.GuardianVerification { guardian_number: 3, backup_order: 2 }
}

pub const joint_key = er.PublicRecord {
  // orig base32: bafkreiflosagia6a2m5rr2dx3jwgrw3fgz6evooliim32gi35drfe6j7ia
  ipfs_cid: #"01551220ab74806403c0d33b18e877da6c68db65367c4ab9cb4219bd191be8e252793f40",
  metadata: er.JointKey
}

pub const constants = er.PublicRecord {
  // orig base32: bafkreicnmehtjlzlm5sddglfrqg2zjmqlrje3g24uxxdgsjzscouqrxjoy
  ipfs_cid: #"015512204d610f34af2b67643199658c0daca5905c524d9b5ca5ee334939909d4846e976",
  metadata: er.Constants
}

pub const device1 = er.PublicRecord {
  // orig base32: bafkreif73tr5sgi2qm23r3l3ahmn5z73le7lh2mfw267jzeackvrvzacb4
  ipfs_cid: #"01551220bfdce3d9191a8335b8ed7b01d8dee7fb593eb3e985b6bdf4e48012ab1ae4020f",
  metadata: er.Device { device_number: 1 }
}

pub const ballot_submitted_476d9db6 = er.PublicRecord {
  // orig base32: bafkreihelpxclsgoej4a6yeinlw6nlondthnniwwml2tdsvwhollogqxey
  ipfs_cid: #"01551220e45bee25c8ce22780f60886aede6adcd1cced6a2d662f531cab63b96b71a1726",
  metadata: er.BallotSubmitted { ballot_id: to_bytearray(@"ballot-476d9db6-1d64-11f1-9625-768fd7ed4145") }
}

pub const ballot_submitted_480eed2e = er.PublicRecord {
  // orig base32: bafkreibttf67rmdea6gvgux7l4ongpd72cocduvmel65kevffiu5riahe4
  ipfs_cid: #"0155122033997df8b064078d5352ff5f1cd33c7fd09c21d2ac22fdd512a52a29d8a00727",
  metadata: er.BallotSubmitted { ballot_id: to_bytearray(@"ballot-480eed2e-1d64-11f1-ac1f-768fd7ed4145") }
}

pub const ballot_submitted_48b5dc74 = er.PublicRecord {
  // orig base32: bafkreiekw4hjgn2bslhg4qkiq7pckzo6lyvt53tbh6xmkqiammti6kbz4y
  ipfs_cid: #"015512208ab70e93374192ce6e414887de2565de5e2b3eee613faec5410063268f2839e6",
  metadata: er.BallotSubmitted { ballot_id: to_bytearray(@"ballot-48b5dc74-1d64-11f1-9b1b-768fd7ed4145") }
}

pub const ballot_submitted_4957f5fe = er.PublicRecord {
  // orig base32: bafkreibgrxxgpa6bticetqjcbv47sqxlsomww35r62uvgyftumyz4mrg4e
  ipfs_cid: #"01551220268dee6783c19a0449c1220d79f942eb93996b6fb1f6a95360b3a3319e3226e1",
  metadata: er.BallotSubmitted { ballot_id: to_bytearray(@"ballot-4957f5fe-1d64-11f1-9226-768fd7ed4145") }
}

pub const ballot_submitted_49fb726a = er.PublicRecord {
  // orig base32: bafkreibhnzwsht7deggi3kbktkbd6pyzgqvjdwz6byt253xusr23jq2r2a
  ipfs_cid: #"01551220276e6d23cfe3218c8da82a9a823f3f19342a91db3e0e27aeeef49475b4c351d0",
  metadata: er.BallotSubmitted { ballot_id: to_bytearray(@"ballot-49fb726a-1d64-11f1-ad12-768fd7ed4145") }
}

pub const ballot_submitted_4aa15ab8 = er.PublicRecord {
  // orig base32: bafkreigukp4lkf4i25do7uvwahjproph2wi25exiseekqeyr3vbnzs2n5q
  ipfs_cid: #"01551220d453f8b51788d746efd2b601d2f8b9e7d591ae92e89108a81311dd42dccb4dec",
  metadata: er.BallotSubmitted { ballot_id: to_bytearray(@"ballot-4aa15ab8-1d64-11f1-bc23-768fd7ed4145") }
}

pub const ballot_submitted_4b4fb8a6 = er.PublicRecord {
  // orig base32: bafkreibd7hcur7h4jvwkwntfv2umdvflinwpfbhtifemzdbs6pym75nrmy
  ipfs_cid: #"0155122023f9c548fcfc4d6cab3665aea8c1d4ab436cf284f34148cc8c32f3f0cff5b166",
  metadata: er.BallotSubmitted { ballot_id: to_bytearray(@"ballot-4b4fb8a6-1d64-11f1-a997-768fd7ed4145") }
}

pub const ballot_submitted_4bf9df52 = er.PublicRecord {
  // orig base32: bafkreigvru7hi6xjpgeblb6megrckqvcsena3ngjm2jfzjbt3hzxhmaahi
  ipfs_cid: #"01551220d58d3e747ae979881587cc21a22542a2911a0db4c966925ca433d9f373b0003a",
  metadata: er.BallotSubmitted { ballot_id: to_bytearray(@"ballot-4bf9df52-1d64-11f1-8d0e-768fd7ed4145") }
}

pub const ballot_submitted_4c9f842a = er.PublicRecord {
  // orig base32: bafkreiax7wcfif7bph4kb6f3nh6khm6efcquvf5t236jqi4qunzcowwpzm
  ipfs_cid: #"0155122017fd845417e179f8a0f8bb69fca3b3c428a14a97b3d6fc982390a372275acfcb",
  metadata: er.BallotSubmitted { ballot_id: to_bytearray(@"ballot-4c9f842a-1d64-11f1-94d0-768fd7ed4145") }
}

pub const ballot_submitted_4d471122 = er.PublicRecord {
  // orig base32: bafkreidkum427y5ohffqhpo3gdxwuv5ziqt6kmkg36ziguj6fru5yyequu
  ipfs_cid: #"015512206aa339afe3ae394b03bddb30ef6a57b94427e53146dfb283513e2c69dc6090a5",
  metadata: er.BallotSubmitted { ballot_id: to_bytearray(@"ballot-4d471122-1d64-11f1-a9e3-768fd7ed4145") }
}

pub const ballot_submitted_4decea16 = er.PublicRecord {
  // orig base32: bafkreiabov3szzlddfispbpidljglek4chridkzdy6pqwlxr4ubroqbhfq
  ipfs_cid: #"015512200175772ce56319512785e81ad265915c11e281ab23c79f0b2ef1e5031740272c",
  metadata: er.BallotSubmitted { ballot_id: to_bytearray(@"ballot-4decea16-1d64-11f1-8c68-768fd7ed4145") }
}

pub const ballot_submitted_4e970104 = er.PublicRecord {
  // orig base32: bafkreihhsqshjmdhidlihnoc3tovk3nhokgmi7hdm3mbzfqajuxpuwmcqy
  ipfs_cid: #"01551220e7942474b06740d683b5c2dcdd556da7728cc47ce366d81c96004d2efa598286",
  metadata: er.BallotSubmitted { ballot_id: to_bytearray(@"ballot-4e970104-1d64-11f1-a8cd-768fd7ed4145") }
}

pub const ballot_spoiled_476d9db6 = er.PublicRecord {
  // orig base32: bafkreidroufhxajucas24tanlfgz7ujyyal5x2geg52nwnalsfibp2x3oq
  ipfs_cid: #"0155122071750a7b81341025ae4c0d594d9fd138c017dbe8c43774db340b915017eafb74",
  metadata: er.BallotSpoiled { ballot_id: to_bytearray(@"ballot-476d9db6-1d64-11f1-9625-768fd7ed4145") }
}

pub const ballot_spoiled_480eed2e = er.PublicRecord {
  // orig base32: bafkreifjn5g5az6vyrb5ywhnx7gyn6axmh7bzszebiw44g7m7duy7ebai4
  ipfs_cid: #"01551220a96f4dd067d5c443dc58edbfcd86f81761fe1ccb240a2dce1becf8e98f902047",
  metadata: er.BallotSpoiled { ballot_id: to_bytearray(@"ballot-480eed2e-1d64-11f1-ac1f-768fd7ed4145") }
}

pub const ballot_spoiled_48b5dc74 = er.PublicRecord {
  // orig base32: bafkreifs7zrddjb6umnatxyomj36r26kggphp4ej7iljau5cms3ktuj3tm
  ipfs_cid: #"01551220b2fe6231a43ea31a09df0e6277e8ebca319e77f089fa169053a264b6a9d13b9b",
  metadata: er.BallotSpoiled { ballot_id: to_bytearray(@"ballot-48b5dc74-1d64-11f1-9b1b-768fd7ed4145") }
}

pub const ballot_spoiled_49fb726a = er.PublicRecord {
  // orig base32: bafkreiavzjzgcw645hcshu7opwwc4fgrye5izithlpirymhkoaeogrptty
  ipfs_cid: #"0155122015ca72615bdce9c523d3ee7dac2e14d1c13a8ca2675bd11c30ea7008e345f39e",
  metadata: er.BallotSpoiled { ballot_id: to_bytearray(@"ballot-49fb726a-1d64-11f1-ad12-768fd7ed4145") }
}

pub const ballot_spoiled_4aa15ab8 = er.PublicRecord {
  // orig base32: bafkreicshqopt3jgh32b2siwymemsypa4v2p3ezjta2hn3tz7bkxybn53a
  ipfs_cid: #"01551220523c1cf9ed263ef41d4916c308c961e0e574fd9329983476ee79f8557c05bdd8",
  metadata: er.BallotSpoiled { ballot_id: to_bytearray(@"ballot-4aa15ab8-1d64-11f1-bc23-768fd7ed4145") }
}

pub const ballot_spoiled_4c9f842a = er.PublicRecord {
  // orig base32: bafkreiecjgwtcfhahxn4fz62ltnut3mnjf55uxqmri3svth4uiq3bsm43m
  ipfs_cid: #"015512208249ad3114e03ddbc2e7da5cdb49ed8d497bda5e0c8a372accfca221b0c99cdb",
  metadata: er.BallotSpoiled { ballot_id: to_bytearray(@"ballot-4c9f842a-1d64-11f1-94d0-768fd7ed4145") }
}

pub const cast_notice_4957f5fe = er.PublicRecord {
  // orig base32: bafkreihzxotfhtjm2wm3bwb25clfw5mw37cyoxro5yywd4g3re3h6haq4u
  ipfs_cid: #"01551220f9bba653cd2cd599b0d83ae8965b7596dfc5875e2eee3161f0db89367f1c10e5",
  metadata: er.CastNotice { ballot_id: to_bytearray(@"ballot-4957f5fe-1d64-11f1-9226-768fd7ed4145") }
}

pub const cast_notice_4b4fb8a6 = er.PublicRecord {
  // orig base32: bafkreiexcmw5652z45vkraqm2hycndci3mknx5l4cjs7rlh5ve3i2xn3ni
  ipfs_cid: #"0155122097132ddf7759e76aa8820cd1f0268c48db14dbf57c1265f8acfda9368d5dbb6a",
  metadata: er.CastNotice { ballot_id: to_bytearray(@"ballot-4b4fb8a6-1d64-11f1-a997-768fd7ed4145") }
}

pub const cast_notice_4bf9df52 = er.PublicRecord {
  // orig base32: bafkreidpttwq7stnwj5pchrrxbxfd6vaenfqeigejr645yodrqv5b77dhu
  ipfs_cid: #"015512206f9ced0fca6db27af11e31b86e51faa0234b0220c44c7dcee1c38c2bd0ffe33d",
  metadata: er.CastNotice { ballot_id: to_bytearray(@"ballot-4bf9df52-1d64-11f1-8d0e-768fd7ed4145") }
}

pub const cast_notice_4d471122 = er.PublicRecord {
  // orig base32: bafkreihgyyk74uquxnm7cldulhy6msyqaj6uqar2cl26db5aiuwbhzgceq
  ipfs_cid: #"01551220e6c615fe5214bb59f12c7459f1e64b10027d48023a12f5e187a0452c13e4c224",
  metadata: er.CastNotice { ballot_id: to_bytearray(@"ballot-4d471122-1d64-11f1-a9e3-768fd7ed4145") }
}

pub const cast_notice_4decea16 = er.PublicRecord {
  // orig base32: bafkreic5fv2pemgfbfoio72cmfwfqufaclkrsdofpv5m7jak6efpeiqthy
  ipfs_cid: #"015512205d2d74f230c5095c877f42616c5850a012d5190dc57d7acfa40af10af222133e",
  metadata: er.CastNotice { ballot_id: to_bytearray(@"ballot-4decea16-1d64-11f1-8c68-768fd7ed4145") }
}

pub const cast_notice_4e970104 = er.PublicRecord {
  // orig base32: bafkreibhj6cdhoczzsfaovsqhqp5xji554qkg52q735fffw2jkze2osasu
  ipfs_cid: #"01551220274f8433b859cc8a0756503c1fdba51def20a37750fefa5296da4ab24d3a4095",
  metadata: er.CastNotice { ballot_id: to_bytearray(@"ballot-4e970104-1d64-11f1-a8cd-768fd7ed4145") }
}

pub const ciphertext_tally = er.PublicRecord {
  // orig base32: bafkreievubwr4agxsswp4relq4qkmq4fvcwo74vximmlgrk3zbz6xbwpka
  ipfs_cid: #"0155122095a06d1e00d794acfe448b8720a64385a8aceff2b74318b3455bc873eb86cf50",
  metadata: er.CiphertextTally
}

pub const guardian1_tally_share = er.PublicRecord {
  // orig base32: bafkreihcug5vklujdx46a6rysjorrmyraastqlgh2ghxza4idmr4bbp7wa
  ipfs_cid: #"01551220e2a1bb552e891df9e07a38925d18b3110025382cc7d18f7c83881b23c085ffb0",
  metadata: er.TallyShare { guardian_number: 1 }
}

pub const guardian3_tally_share = er.PublicRecord {
  // orig base32: bafkreib5n5dqgpsbsmgfvrhjhsd5lrn4m6l24exjslkwiqev5rovfdvxna
  ipfs_cid: #"015512203d6f47033e41930c5ac4e93c87d5c5bc6797ae12e992d5644095ec5d528eb768",
  metadata: er.TallyShare { guardian_number: 3 }
}

pub const guardian2_tally_share = er.PublicRecord {
  // orig base32: bafkreia64mxrrklbazfwr5t6gthkya4oxf6xkwvgrttwzewursa3fbswuq
  ipfs_cid: #"015512201ee32f18a961064b68f67e34ceac038eb97d755aa68ce76c92d48c81b28656a4",
  metadata: er.TallyShare { guardian_number: 2 }
}

pub const guardian1_spoiled_share_476d9db6 = er.PublicRecord {
  // orig base32: bafkreifvnrplnw2bmydu4khwkpk4lpjndukz6jxfm7lp2vs43yf55up2bm
  ipfs_cid: #"01551220b56c5eb6db4166074e28f653d5c5bd2d1d159f26e567d6fd565cde0bded1fa0b",
  metadata: er.SpoiledShare {
    guardian_number: 1,
    spoiled_id: to_bytearray(@"ballot-476d9db6-1d64-11f1-9625-768fd7ed4145"),
  }
}

pub const guardian1_spoiled_share_480eed2e = er.PublicRecord {
  // orig base32: bafkreiffqfwkwlaqycw6snghprjfor4tpihhmfydwkejvphmrn2iwu2cv4
  ipfs_cid: #"01551220a5816cab2c10c0ade934c77c525747937a0e761703b2889abcec8b748b5342af",
  metadata: er.SpoiledShare {
    guardian_number: 1,
    spoiled_id: to_bytearray(@"ballot-480eed2e-1d64-11f1-ac1f-768fd7ed4145"),
  }
}

pub const guardian1_spoiled_share_48b5dc74 = er.PublicRecord {
  // orig base32: bafkreiagowiardipcmvxgoj5lo5bahk337bxtdyyvth4akbppshyxia5ia
  ipfs_cid: #"01551220067590088d0f132b73393d5bba101d5bdfc3798f18accfc0282f7c8f8ba01d40",
  metadata: er.SpoiledShare {
    guardian_number: 1,
    spoiled_id: to_bytearray(@"ballot-48b5dc74-1d64-11f1-9b1b-768fd7ed4145"),
  }
}

pub const guardian1_spoiled_share_49fb726a = er.PublicRecord {
  // orig base32: bafkreig7zc3plmc45xcsamnsmf5bywi3fofuxp4moqdu4ndmkgdhohkigi
  ipfs_cid: #"01551220dfc8b6f5b05cedc52031b2617a1c591b2b8b4bbf8c74074e346c5186771d4832",
  metadata: er.SpoiledShare {
    guardian_number: 1,
    spoiled_id: to_bytearray(@"ballot-49fb726a-1d64-11f1-ad12-768fd7ed4145"),
  }
}

pub const guardian2_spoiled_share_476d9db6 = er.PublicRecord {
  // orig base32: bafkreihc4oucffse55225dmfz4b2ybtn6yoi6ipxu3ra5ydworckxtthgy
  ipfs_cid: #"01551220e2e3a8229644ef75ae8d85cf03ac066df61c8f21f7a6e20ee0767444abce6736",
  metadata: er.SpoiledShare {
    guardian_number: 2,
    spoiled_id: to_bytearray(@"ballot-476d9db6-1d64-11f1-9625-768fd7ed4145"),
  }
}

pub const guardian3_spoiled_share_476d9db6 = er.PublicRecord {
  // orig base32: bafkreibwcjoghauq7w3s3h5z2ov4gb6ffwyzct5ac4sa6a3wsv3hnarxfm
  ipfs_cid: #"0155122036125c638290fdb72d9fb9d3abc307c52db1914fa017240f037695767682372b",
  metadata: er.SpoiledShare {
    guardian_number: 3,
    spoiled_id: to_bytearray(@"ballot-476d9db6-1d64-11f1-9625-768fd7ed4145"),
  }
}

pub const guardian1_spoiled_share_4aa15ab8 = er.PublicRecord {
  // orig base32: bafkreielhlqobw35aa4ztdaeooetidizhxcojxo46yngj67354wuw3npgy
  ipfs_cid: #"015512208b3ae0e0db7d0039998c047389340d193dc4e4dddcf61a64fbfbef2d4b6daf36",
  metadata: er.SpoiledShare {
    guardian_number: 1,
    spoiled_id: to_bytearray(@"ballot-4aa15ab8-1d64-11f1-bc23-768fd7ed4145"),
  }
}

pub const guardian2_spoiled_share_480eed2e = er.PublicRecord {
  // orig base32: bafkreibqpsa5ouitox5vlty23wallbjf2rtul547o7kxnz2c33gegaat6m
  ipfs_cid: #"01551220307c81d7511375fb55cf1add80b58525d46745f79f77d576e742decc430013f3",
  metadata: er.SpoiledShare {
    guardian_number: 2,
    spoiled_id: to_bytearray(@"ballot-480eed2e-1d64-11f1-ac1f-768fd7ed4145"),
  }
}

pub const guardian3_spoiled_share_480eed2e = er.PublicRecord {
  // orig base32: bafkreias7eapemxb4d6xlfnhbl6qg6o7h2nnxor4p3coi22fe3xb2lyege
  ipfs_cid: #"0155122012f900f232e1e0fd7595a70afd0379df3e9adbba3c7ec4e46b4526ee1d2f0431",
  metadata: er.SpoiledShare {
    guardian_number: 3,
    spoiled_id: to_bytearray(@"ballot-480eed2e-1d64-11f1-ac1f-768fd7ed4145"),
  }
}

pub const guardian1_spoiled_share_4c9f842a = er.PublicRecord {
  // orig base32: bafkreib2mw2u2fmg5crie622g52fi7b7bydkzean7opgbr3xajlboizewu
  ipfs_cid: #"015512203a65b54d1586e8a2827b5a3774547c3f0e06ac900dfb9e60c7770256172324b5",
  metadata: er.SpoiledShare {
    guardian_number: 1,
    spoiled_id: to_bytearray(@"ballot-4c9f842a-1d64-11f1-94d0-768fd7ed4145"),
  }
}

pub const guardian3_spoiled_share_48b5dc74 = er.PublicRecord {
  // orig base32: bafkreid4jkivfh2ib3hbyx4iwjaocn745n4i5u7ii2rbpc3icmvepgeq4m
  ipfs_cid: #"015512207c4a91529f480ece1c5f88b240e137fceb788ed3e846a2178b68132a479890e3",
  metadata: er.SpoiledShare {
    guardian_number: 3,
    spoiled_id: to_bytearray(@"ballot-48b5dc74-1d64-11f1-9b1b-768fd7ed4145"),
  }
}

pub const guardian3_spoiled_share_49fb726a = er.PublicRecord {
  // orig base32: bafkreidtm4kr65lbx3zkdhefbvgwy2ec4lhx5x2idy4nc3cdmx3wmso54e
  ipfs_cid: #"015512207367151f7561bef2a19c850d4d6c6882e2cf7edf481e38d16c4365f76649dde1",
  metadata: er.SpoiledShare {
    guardian_number: 3,
    spoiled_id: to_bytearray(@"ballot-49fb726a-1d64-11f1-ad12-768fd7ed4145"),
  }
}

pub const guardian3_spoiled_share_4aa15ab8 = er.PublicRecord {
  // orig base32: bafkreic5zs7g7pnsad3yglkfs6wacofi3h63gwhxskolraxfko5waeqsoy
  ipfs_cid: #"015512205dccbe6fbdb200f7832d4597ac0138a8d9fdb358f7929cb882e553bb60121276",
  metadata: er.SpoiledShare {
    guardian_number: 3,
    spoiled_id: to_bytearray(@"ballot-4aa15ab8-1d64-11f1-bc23-768fd7ed4145"),
  }
}

pub const guardian3_spoiled_share_4c9f842a = er.PublicRecord {
  // orig base32: bafkreihctuwj7jxhlp2qashvfw4k6ijjnv7ayhgqfuekil66gysoxwvcsm
  ipfs_cid: #"01551220e29d2c9fa6e75bf50048f52db8af21296d7e0c1cd02d08a42fde3624ebdaa293",
  metadata: er.SpoiledShare {
    guardian_number: 3,
    spoiled_id: to_bytearray(@"ballot-4c9f842a-1d64-11f1-94d0-768fd7ed4145"),
  }
}

pub const guardian2_spoiled_share_48b5dc74 = er.PublicRecord {
  // orig base32: bafkreidn32rhehcugcfw4eq7byy5w5xyhzb26oonel3nkqia7en6lu6bse
  ipfs_cid: #"015512206ddea2721c54308b6e121f0e31db76f83e43af39cd22f6d54100f91be5d3c191",
  metadata: er.SpoiledShare {
    guardian_number: 2,
    spoiled_id: to_bytearray(@"ballot-48b5dc74-1d64-11f1-9b1b-768fd7ed4145"),
  }
}

pub const guardian2_spoiled_share_49fb726a = er.PublicRecord {
  // orig base32: bafkreidphlabwc6yjc43eb332szf5qq4rl54c5muyevakmp6tokxdwh2xe
  ipfs_cid: #"015512206f3ac01b0bd848b9b2077bd4b25ec21c8afbc17594c12a0531fe9b9571d8fab9",
  metadata: er.SpoiledShare {
    guardian_number: 2,
    spoiled_id: to_bytearray(@"ballot-49fb726a-1d64-11f1-ad12-768fd7ed4145"),
  }
}

pub const guardian2_spoiled_share_4aa15ab8 = er.PublicRecord {
  // orig base32: bafkreiga37rtmlmjja66th2mmykrsqqqrjkgrforkdoucfrw5skgaqhyoa
  ipfs_cid: #"01551220c0dfe3362d89483de99f4c66151942108a546895d150dd411636ec946040f870",
  metadata: er.SpoiledShare {
    guardian_number: 2,
    spoiled_id: to_bytearray(@"ballot-4aa15ab8-1d64-11f1-bc23-768fd7ed4145"),
  }
}

pub const guardian2_spoiled_share_4c9f842a = er.PublicRecord {
  // orig base32: bafkreige667qcooppyj5pkhvc3djuobyq3by6kc6hp4jwplspqlx2ihzp4
  ipfs_cid: #"01551220c4f7bf0139cf7e13d7a8f516c69a383886c38f285e3bf89b3d727c177d20f97f",
  metadata: er.SpoiledShare {
    guardian_number: 2,
    spoiled_id: to_bytearray(@"ballot-4c9f842a-1d64-11f1-94d0-768fd7ed4145"),
  }
}

pub const plaintext_tally = er.PublicRecord {
  // orig base32: bafkreicy6dgis5ro4cwe7khlj53b575frfsrrydhu6cxu2vrlwstcwkyyu
  ipfs_cid: #"0155122058f0cc89762ee0ac4fa8eb4f761effa5896518e067a7857a6ab15da5315958c5",
  metadata: er.PlaintextTally
}

pub const spoiled_result_476d9db6 = er.PublicRecord {
  // orig base32: bafkreihjz3q65b3yfyjvjf6m7rbhw7zsuqevlzjdate6ojuqx7mhug3x5m
  ipfs_cid: #"01551220e9cee1ee87782e135497ccfc427b7f32a40955e52304c9e72690bfd87a1b77eb",
  metadata: er.SpoiledResult { ballot_id: to_bytearray(@"ballot-476d9db6-1d64-11f1-9625-768fd7ed4145") }
}

pub const spoiled_result_480eed2e = er.PublicRecord {
  // orig base32: bafkreicvgvz2rfc2ktqgunso2rs7w2uw6caifbq4ecbbgyg5ewpkxicutq
  ipfs_cid: #"01551220553573a8945a54e06a364ed465fb6a96f08082861c20821360dd259eaba0549c",
  metadata: er.SpoiledResult { ballot_id: to_bytearray(@"ballot-480eed2e-1d64-11f1-ac1f-768fd7ed4145") }
}

pub const spoiled_result_48b5dc74 = er.PublicRecord {
  // orig base32: bafkreibn2c3oqsozx36kwnopf52e225vdi7ft2zxprv4frwojfeqrjnvhy
  ipfs_cid: #"015512202dd0b6e849d9befcab35cf2f744d6bb51a3e59eb377c6bc2c6ce494908a5b53e",
  metadata: er.SpoiledResult { ballot_id: to_bytearray(@"ballot-48b5dc74-1d64-11f1-9b1b-768fd7ed4145") }
}

pub const spoiled_result_49fb726a = er.PublicRecord {
  // orig base32: bafkreiea23ycqgsptmpgckbpudwekyt6jgiqlt2klky5nkr7dvzotdd6vy
  ipfs_cid: #"0155122080d6f0281a4f9b1e61282fa0ec45627e499105cf4a5ab1d6aa3f1d72e98c7eae",
  metadata: er.SpoiledResult { ballot_id: to_bytearray(@"ballot-49fb726a-1d64-11f1-ad12-768fd7ed4145") }
}

pub const spoiled_result_4aa15ab8 = er.PublicRecord {
  // orig base32: bafkreifvqpg4fiw5lfpt7pzgzwb5snnhayagyzbsbtectxw2ulaof6s2vi
  ipfs_cid: #"01551220b583cdc2a2dd595f3fbf26cd83d935a706006c64320cc829dedaa2c0e2fa5aaa",
  metadata: er.SpoiledResult { ballot_id: to_bytearray(@"ballot-4aa15ab8-1d64-11f1-bc23-768fd7ed4145") }
}

pub const spoiled_result_4c9f842a = er.PublicRecord {
  // orig base32: bafkreihesgn7p3n2nt6tjcfduezo66ywphat3s75dxtqakrolootf2xpby
  ipfs_cid: #"01551220e4919bf7edba6cfd3488a3a132ef7b1679c13dcbfd1de7002a2e5b9d32eaef0e",
  metadata: er.SpoiledResult { ballot_id: to_bytearray(@"ballot-4c9f842a-1d64-11f1-94d0-768fd7ed4145") }
}

pub const guardian2_summary = er.PublicRecord {
  // orig base32: bafkreifvzqqtpbiln42xeu3bxgstcy3wnabh3vnxroxfwkhkai6fvidjtq
  ipfs_cid: #"01551220b5cc2137850b6f35725361b9a531637668027dd5b78bae5b28ea023c5aa0699c",
  metadata: er.Summary { verifier_id: to_bytearray(@"guardian2") }
}

pub const guardian3_summary = er.PublicRecord {
  // orig base32: bafkreifvzqqtpbiln42xeu3bxgstcy3wnabh3vnxroxfwkhkai6fvidjtq
  ipfs_cid: #"01551220b5cc2137850b6f35725361b9a531637668027dd5b78bae5b28ea023c5aa0699c",
  metadata: er.Summary { verifier_id: to_bytearray(@"guardian3") }
}

pub const admin1_summary = er.PublicRecord {
  // orig base32: bafkreifvzqqtpbiln42xeu3bxgstcy3wnabh3vnxroxfwkhkai6fvidjtq
  ipfs_cid: #"01551220b5cc2137850b6f35725361b9a531637668027dd5b78bae5b28ea023c5aa0699c",
  metadata: er.Summary { verifier_id: to_bytearray(@"admin1") }
}

pub const verifier1_summary = er.PublicRecord {
  // orig base32: bafkreifvzqqtpbiln42xeu3bxgstcy3wnabh3vnxroxfwkhkai6fvidjtq
  ipfs_cid: #"01551220b5cc2137850b6f35725361b9a531637668027dd5b78bae5b28ea023c5aa0699c",
  metadata: er.Summary { verifier_id: to_bytearray(@"verifier1") }
}

pub const guardian1_summary = er.PublicRecord {
  // orig base32: bafkreifvzqqtpbiln42xeu3bxgstcy3wnabh3vnxroxfwkhkai6fvidjtq
  ipfs_cid: #"01551220b5cc2137850b6f35725361b9a531637668027dd5b78bae5b28ea023c5aa0699c",
  metadata: er.Summary { verifier_id: to_bytearray(@"guardian1") }
}

pub const admin_records = [
  manifest,
  ceremony_details,
  joint_key,
  constants,
  ciphertext_tally,
  plaintext_tally,
  spoiled_result_476d9db6,
  spoiled_result_480eed2e,
  spoiled_result_48b5dc74,
  spoiled_result_49fb726a,
  spoiled_result_4aa15ab8,
  spoiled_result_4c9f842a,
  admin1_summary,
]

pub const guardian1_records = [
  guardian1_pubkey,
  guardian1_backup2,
  guardian1_backup3,
  guardian1_verification2,
  guardian1_verification3,
  guardian1_tally_share,
  guardian1_spoiled_share_476d9db6,
  guardian1_spoiled_share_480eed2e,
  guardian1_spoiled_share_48b5dc74,
  guardian1_spoiled_share_49fb726a,
  guardian1_spoiled_share_4aa15ab8,
  guardian1_spoiled_share_4c9f842a,
  guardian1_summary,
]

pub const guardian2_records = [
  guardian2_pubkey,
  guardian2_backup1,
  guardian2_backup3,
  guardian2_verification1,
  guardian2_verification3,
  guardian2_tally_share,
  guardian2_spoiled_share_476d9db6,
  guardian2_spoiled_share_480eed2e,
  guardian2_spoiled_share_48b5dc74,
  guardian2_spoiled_share_49fb726a,
  guardian2_spoiled_share_4aa15ab8,
  guardian2_spoiled_share_4c9f842a,
  guardian2_summary,
]

pub const guardian3_records = [
  guardian3_pubkey,
  guardian3_backup1,
  guardian3_backup2,
  guardian3_verification1,
  guardian3_verification2,
  guardian3_tally_share,
  guardian3_spoiled_share_476d9db6,
  guardian3_spoiled_share_480eed2e,
  guardian3_spoiled_share_48b5dc74,
  guardian3_spoiled_share_49fb726a,
  guardian3_spoiled_share_4aa15ab8,
  guardian3_spoiled_share_4c9f842a,
  guardian3_summary,
]

pub const ballot_submitted_records = [
  ballot_submitted_476d9db6,
  ballot_submitted_480eed2e,
  ballot_submitted_48b5dc74,
  ballot_submitted_4957f5fe,
  ballot_submitted_49fb726a,
  ballot_submitted_4aa15ab8,
  ballot_submitted_4b4fb8a6,
  ballot_submitted_4bf9df52,
  ballot_submitted_4c9f842a,
  ballot_submitted_4d471122,
  ballot_submitted_4decea16,
  ballot_submitted_4e970104,
]

pub const ballot_spoiled_records = [
  ballot_spoiled_476d9db6,
  ballot_spoiled_480eed2e,
  ballot_spoiled_48b5dc74,
  ballot_spoiled_49fb726a,
  ballot_spoiled_4aa15ab8,
  ballot_spoiled_4c9f842a,
]

pub const cast_notice_records = [
  cast_notice_4957f5fe,
  cast_notice_4b4fb8a6,
  cast_notice_4bf9df52,
  cast_notice_4d471122,
  cast_notice_4decea16,
  cast_notice_4e970104,
]

pub const spoiled_share_records = [
  guardian1_spoiled_share_476d9db6,
  guardian1_spoiled_share_480eed2e,
  guardian1_spoiled_share_48b5dc74,
  guardian1_spoiled_share_49fb726a,
  guardian2_spoiled_share_476d9db6,
  guardian3_spoiled_share_476d9db6,
  guardian1_spoiled_share_4aa15ab8,
  guardian2_spoiled_share_480eed2e,
  guardian3_spoiled_share_480eed2e,
  guardian1_spoiled_share_4c9f842a,
  guardian3_spoiled_share_48b5dc74,
  guardian3_spoiled_share_49fb726a,
  guardian3_spoiled_share_4aa15ab8,
  guardian3_spoiled_share_4c9f842a,
  guardian2_spoiled_share_48b5dc74,
  guardian2_spoiled_share_49fb726a,
  guardian2_spoiled_share_4aa15ab8,
  guardian2_spoiled_share_4c9f842a,
]

pub const spoiled_result_records = [
  spoiled_result_476d9db6,
  spoiled_result_480eed2e,
  spoiled_result_48b5dc74,
  spoiled_result_49fb726a,
  spoiled_result_4aa15ab8,
  spoiled_result_4c9f842a,
]

pub const device1_records = [
  device1,
  ballot_submitted_476d9db6,
  ballot_submitted_480eed2e,
  ballot_submitted_48b5dc74,
  ballot_submitted_4957f5fe,
  ballot_submitted_49fb726a,
  ballot_submitted_4aa15ab8,
  ballot_submitted_4b4fb8a6,
  ballot_submitted_4bf9df52,
  ballot_submitted_4c9f842a,
  ballot_submitted_4d471122,
  ballot_submitted_4decea16,
  ballot_submitted_4e970104,
  ballot_spoiled_476d9db6,
  ballot_spoiled_480eed2e,
  ballot_spoiled_48b5dc74,
  ballot_spoiled_49fb726a,
  ballot_spoiled_4aa15ab8,
  ballot_spoiled_4c9f842a,
  cast_notice_4957f5fe,
  cast_notice_4b4fb8a6,
  cast_notice_4bf9df52,
  cast_notice_4d471122,
  cast_notice_4decea16,
  cast_notice_4e970104,
]

pub const verifier1_records = [
  verifier1_summary,
]

pub const summary_records = [
  guardian2_summary,
  guardian3_summary,
  admin1_summary,
  verifier1_summary,
  guardian1_summary,
]

pub const all_records = [
  manifest,
  ceremony_details,
  guardian3_pubkey,
  guardian2_pubkey,
  guardian1_pubkey,
  guardian3_backup1,
  guardian2_backup1,
  guardian1_backup2,
  guardian3_backup2,
  guardian1_backup3,
  guardian2_backup3,
  guardian1_verification2,
  guardian2_verification1,
  guardian1_verification3,
  guardian3_verification1,
  guardian2_verification3,
  guardian3_verification2,
  joint_key,
  constants,
  device1,
  ballot_submitted_476d9db6,
  ballot_submitted_480eed2e,
  ballot_submitted_48b5dc74,
  ballot_submitted_4957f5fe,
  ballot_submitted_49fb726a,
  ballot_submitted_4aa15ab8,
  ballot_submitted_4b4fb8a6,
  ballot_submitted_4bf9df52,
  ballot_submitted_4c9f842a,
  ballot_submitted_4d471122,
  ballot_submitted_4decea16,
  ballot_submitted_4e970104,
  ballot_spoiled_476d9db6,
  ballot_spoiled_480eed2e,
  ballot_spoiled_48b5dc74,
  ballot_spoiled_49fb726a,
  ballot_spoiled_4aa15ab8,
  ballot_spoiled_4c9f842a,
  cast_notice_4957f5fe,
  cast_notice_4b4fb8a6,
  cast_notice_4bf9df52,
  cast_notice_4d471122,
  cast_notice_4decea16,
  cast_notice_4e970104,
  ciphertext_tally,
  guardian1_tally_share,
  guardian3_tally_share,
  guardian2_tally_share,
  guardian1_spoiled_share_476d9db6,
  guardian1_spoiled_share_480eed2e,
  guardian1_spoiled_share_48b5dc74,
  guardian1_spoiled_share_49fb726a,
  guardian2_spoiled_share_476d9db6,
  guardian3_spoiled_share_476d9db6,
  guardian1_spoiled_share_4aa15ab8,
  guardian2_spoiled_share_480eed2e,
  guardian3_spoiled_share_480eed2e,
  guardian1_spoiled_share_4c9f842a,
  guardian3_spoiled_share_48b5dc74,
  guardian3_spoiled_share_49fb726a,
  guardian3_spoiled_share_4aa15ab8,
  guardian3_spoiled_share_4c9f842a,
  guardian2_spoiled_share_48b5dc74,
  guardian2_spoiled_share_49fb726a,
  guardian2_spoiled_share_4aa15ab8,
  guardian2_spoiled_share_4c9f842a,
  plaintext_tally,
  spoiled_result_476d9db6,
  spoiled_result_480eed2e,
  spoiled_result_48b5dc74,
  spoiled_result_49fb726a,
  spoiled_result_4aa15ab8,
  spoiled_result_4c9f842a,
  guardian2_summary,
  guardian3_summary,
  admin1_summary,
  verifier1_summary,
  guardian1_summary,
]
