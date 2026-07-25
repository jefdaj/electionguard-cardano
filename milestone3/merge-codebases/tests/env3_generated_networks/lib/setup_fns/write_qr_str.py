from ..config import ResolvedTestConfig

OLD_QR_STRS = [

    # TODO add back a max blocks to wait before calling an election done
    # TODO and detect + show burns properly

    # init_election only
    # '''egc:election:3:d8799f5820be3f80b1c83cc2445fae4b2157a4bcf34f5a4b6d5e032f1deedb3
    # f067dffdf6400ff:2:addr_test1vr93qqyu30r5c7snd4wp8wu243st2xz8605yea78hgyg6uckjak
    # k5:118296189:11b99ea65fd54e194dc32fb4fbb4b76402175c24fab997db2e8861513be9c113''',

    # happy_subchannels
    # '''egc:election:3:d8799f5820b2106681301173bebf1568dffde6e8bdf5b76517e51d17b527370
    # ccb3ed14e2500ff:2:addr_test1vr93qqyu30r5c7snd4wp8wu243st2xz8605yea78hgyg6uckjak
    # k5:118296353:5a2e81d54ad3efb5da12f46cea5fb4f22e26e09e5a5b6b18336e148236146ec0''',

    # happy_election
    '''egc:election:3:d8799f5820c81cf66e6e2c118f96d1e9b064b693d6def8a451e8b030372dd69
    c172a90c9e800ff:2:addr_test1vr93qqyu30r5c7snd4wp8wu243st2xz8605yea78hgyg6uckjak
    k5:118296546:b23e0378ce52c791f9c449be3f1f44ab3a79be15adb309ccfb9751ab5f2f8392''',

    # happy_election that failed at test_phase3_voting
    # '''egc:election:3:d8799f58204cca2173550004a8dcec570207df48d1fff499a46c81179
    # 26a77de7819d51dd900ff:2:addr_test1vr93qqyu30r5c7snd4wp8wu243st2xz8605yea78h
    # gyg6uckjakk5:118299682:fd83f5ed90881b30542e7c868fc0eb1f79d79046723c10e5572c
    # cd28b022a1bd''',

]

def write_qr_str(cfg: ResolvedTestConfig, drawn: int):
    """Write a random election qr str in the qrcodes dir.
    `drawn` as a generic int prevents having to export `OLD_QR_STRS`."""
    qr_idx = drawn % len(OLD_QR_STRS)
    qr_str = OLD_QR_STRS[qr_idx]
    for node_name in cfg.node_names():
        qr_path = cfg.qrcodes_path() / 'election.txt'
        qr_path.write_text(qr_str)
        assert qr_path.exists()
