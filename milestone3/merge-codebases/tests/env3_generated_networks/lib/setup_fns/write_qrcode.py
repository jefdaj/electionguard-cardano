from ..config import ResolvedTestConfig

OLD_QR_STRS = [

# init_election only
'''egc:election:3:d8799f5820be3f80b1c83cc2445fae4b2157a4bcf34f5a4b6d5e032f1de
edb3f067dffdf6400ff:2:addr_test1vr93qqyu30r5c7snd4wp8wu243st2xz8605yea78hgyg6
uckjakk5:118296189:11b99ea65fd54e194dc32fb4fbb4b76402175c24fab997db2e8861513b
e9c113''',

# happy_subchannels
'''egc:election:3:d8799f5820b2106681301173bebf1568dffde6e8bdf5b76517e51d17b52
7370ccb3ed14e2500ff:2:addr_test1vr93qqyu30r5c7snd4wp8wu243st2xz8605yea78hgyg6
uckjakk5:118296353:5a2e81d54ad3efb5da12f46cea5fb4f22e26e09e5a5b6b18336e148236
146ec0''',

# happy_election
'''egc:election:3:d8799f5820c81cf66e6e2c118f96d1e9b064b693d6def8a451e8b030372
dd69c172a90c9e800ff:2:addr_test1vr93qqyu30r5c7snd4wp8wu243st2xz8605yea78hgyg6
uckjakk5:118296546:b23e0378ce52c791f9c449be3f1f44ab3a79be15adb309ccfb9751ab5f
2f8392''',

# happy_election that failed at test_phase3_voting
# TODO will this fail until a default slot timeout is added?
'''egc:election:3:d8799f58204cca2173550004a8dcec570207df48d1fff499a46c8117926
a77de7819d51dd900ff:2:addr_test1vr93qqyu30r5c7snd4wp8wu243st2xz8605yea78hgyg6
uckjakk5:118299682:fd83f5ed90881b30542e7c868fc0eb1f79d79046723c10e5572ccd28b0
22a1bd''',

'''egc:election:3:d8799f58203dda221dc5708ba75728e862d60822aeda9438f402ec01f83
c0abdfc94c1dea502ff:2:addr_test1vr93qqyu30r5c7snd4wp8wu243st2xz8605yea78hgyg6
uckjakk5:118393849:77c2cf1bca3035248597f169980c660f389f21eddd970bcee0464dc49b
dd469c''',

'''egc:election:3:d8799f5820fdd93a2598d48c49218f82f416b73839f89ff697dd6575d27
b135382670c736900ff:2:addr_test1vr93qqyu30r5c7snd4wp8wu243st2xz8605yea78hgyg6
uckjakk5:118394023:6af457b70b23435d0c51bf7df59817f0ca11651e40d6bee6083722e216
5a978e''',

'''egc:election:3:d8799f5820caba5a8419e9c7a479a6082916a294a7ded31d56519220138
b7cf899f9fa660b00ff:2:addr_test1vr93qqyu30r5c7snd4wp8wu243st2xz8605yea78hgyg6
uckjakk5:118394261:df9dccc3c30cb34ec2a688760865cf113064792ba6b9ecaf9dca74b88c
02eeb8''',

'''egc:election:3:d8799f582069dd6d7fe16ce03b2be434208e44b3029ee397b9d31c38231
e472bf918ac311c00ff:2:addr_test1vr93qqyu30r5c7snd4wp8wu243st2xz8605yea78hgyg6
uckjakk5:118394372:2c44dca6e985b0e12d5828cfa57f4b440a364e27219d1acee85f9a3301
780299''',

'''egc:election:3:d8799f58206680e8ca553666f26e04df91de4a4c57d0c3c478dd4e25fb8
410d0556328ff1f00ff:2:addr_test1vr93qqyu30r5c7snd4wp8wu243st2xz8605yea78hgyg6
uckjakk5:118394547:ee7e9209d7a741e2558b800c88b8cb7b4f7480c9bb3dd7171918eaf044
ea34e5''',

'''egc:election:3:d8799f58203dda221dc5708ba75728e862d60822aeda9438f402ec01f83
c0abdfc94c1dea502ff:2:addr_test1vr93qqyu30r5c7snd4wp8wu243st2xz8605yea78hgyg6
uckjakk5:118393849:77c2cf1bca3035248597f169980c660f389f21eddd970bcee0464dc49b
dd469c''',

'''egc:election:3:d8799f5820fdd93a2598d48c49218f82f416b73839f89ff697dd6575d27
b135382670c736900ff:2:addr_test1vr93qqyu30r5c7snd4wp8wu243st2xz8605yea78hgyg6
uckjakk5:118394023:6af457b70b23435d0c51bf7df59817f0ca11651e40d6bee6083722e216
5a978e''',

'''egc:election:3:d8799f5820caba5a8419e9c7a479a6082916a294a7ded31d56519220138
b7cf899f9fa660b00ff:2:addr_test1vr93qqyu30r5c7snd4wp8wu243st2xz8605yea78hgyg6
uckjakk5:118394261:df9dccc3c30cb34ec2a688760865cf113064792ba6b9ecaf9dca74b88c
02eeb8''',

'''egc:election:3:d8799f582069dd6d7fe16ce03b2be434208e44b3029ee397b9d31c38231
e472bf918ac311c00ff:2:addr_test1vr93qqyu30r5c7snd4wp8wu243st2xz8605yea78hgyg6
uckjakk5:118394372:2c44dca6e985b0e12d5828cfa57f4b440a364e27219d1acee85f9a3301
780299''',

'''egc:election:3:d8799f58206680e8ca553666f26e04df91de4a4c57d0c3c478dd4e25fb8
410d0556328ff1f00ff:2:addr_test1vr93qqyu30r5c7snd4wp8wu243st2xz8605yea78hgyg6
uckjakk5:118394547:ee7e9209d7a741e2558b800c88b8cb7b4f7480c9bb3dd7171918eaf044
ea34e5''',

]

def write_qr_txt(cfg: ResolvedTestConfig, drawn: int):
    """Write a random election qr str in the qrcodes dir.
    `drawn` as a generic int prevents having to export `OLD_QR_STRS`."""
    qr_idx = drawn % len(OLD_QR_STRS)
    qr_str = OLD_QR_STRS[qr_idx]
    qr_path = cfg.qrcodes_path() / 'election.txt'
    qr_path.write_text(qr_str)

def write_qr_png(cfg: ResolvedTestConfig, drawn: int):
    """Write a random election qrcode png in the qrcodes dir.
    `drawn` as a generic int prevents having to export `OLD_QR_STRS`."""
    qr_idx = drawn % len(OLD_QR_STRS)
    qr_str = OLD_QR_STRS[qr_idx]
    qr_path = cfg.qrcodes_path() / 'election.png' # TODO svg?
    save_qrcode(obj=qr_str, path=qr_path)
