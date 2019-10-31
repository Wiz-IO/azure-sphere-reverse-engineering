"""
https://wiki.openssl.org/index.php/Command_Line_Elliptic_Curve_Operations
meta_sign_pfx.pfx >>>> meta_sign_pfx.pem

openssl x509 -in meta_sign_pfx.pem -out certificate.pem
openssl x509 -pubkey -noout -in certificate.pem

ecpubkey.pem
-----BEGIN PUBLIC KEY-----
MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAE7fIzwA0xFB2PP1YzQ0DM2MFp+2fi
7FZL+KXvWGscP3vBiMoghwHm18d1ahMmOP6YyaAgB0A95cQi5qfoJqS9JA==
-----END PUBLIC KEY-----

openssl ec -in meta_sign_pfx.pem -out ecprivkey.pem
-----BEGIN EC PRIVATE KEY-----
MHcCAQEEIEsZ9LgD8QisVLCEsT604r3sRhm8caaufgJ+SgzZWXWmoAoGCCqGSM49
AwEHoUQDQgAE7fIzwA0xFB2PP1YzQ0DM2MFp+2fi7FZL+KXvWGscP3vBiMoghwHm
18d1ahMmOP6YyaAgB0A95cQi5qfoJqS9JA==
-----END EC PRIVATE KEY-----

pip install ecdsa
#https://github.com/warner/python-ecdsa
"""



import os, sys, binascii, hashlib, ecdsa
from binascii import hexlify
from os.path import join

from ecdsa import SigningKey, VerifyingKey, BadSignatureError

def HEX(s): return hexlify(s).decode("ascii").upper()
dir = os.path.dirname( sys.argv[0] )

image   = join(dir, 'packer',   'app.image')        # test image
private = join(dir, 'certs',    'ecprivkey.pem')    # maybe is wrong
public  = join(dir, 'certs',    'ecpubkey.pem')     # maybe is ok

f = open(image, 'rb' )
f.seek( 20480 )         # meta offset
MSG = f.read( 144 )     # or 148 or image or all ??????????
f.seek( 20628 )         # signature?
SIG = f.read( 64 )      # read last 64 bytes
print('SIG', HEX(SIG))

sk = SigningKey.from_pem( open( private ).read(), hashfunc = hashlib.sha256 )
vk = VerifyingKey.from_pem( open( public ).read() )

sig = sk.sign(MSG, hashfunc = hashlib.sha256 ) # for new
#print('sig', HEX( sig ))


try:
    vk.verify(str(SIG), MSG)
    print ("app good signature")
except BadSignatureError:
    print ("APP BAD SIGNATURE") # <-------------    



