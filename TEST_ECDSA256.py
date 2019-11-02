# AZSPHERE IMAGE PACKER 2020 Georgi Angelov

"""
https://wiki.openssl.org/index.php/Command_Line_Elliptic_Curve_Operations
https://www.sslshopper.com/ssl-converter.html
meta_sign_pfx.pfx >>>> meta_sign_pfx.pem

openssl x509 -in meta_sign_pfx.pem -out certificate.pem
openssl x509 -pubkey -noout -in certificate.pem

ecpubkey.pem ... is ok
-----BEGIN PUBLIC KEY-----
MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAE7fIzwA0xFB2PP1YzQ0DM2MFp+2fi
7FZL+KXvWGscP3vBiMoghwHm18d1ahMmOP6YyaAgB0A95cQi5qfoJqS9JA==
-----END PUBLIC KEY-----

openssl ec -in meta_sign_pfx.pem -out ecprivkey.pem ???????????
-----BEGIN EC PRIVATE KEY-----
MHcCAQEEIEsZ9LgD8QisVLCEsT604r3sRhm8caaufgJ+SgzZWXWmoAoGCCqGSM49
AwEHoUQDQgAE7fIzwA0xFB2PP1YzQ0DM2MFp+2fi7FZL+KXvWGscP3vBiMoghwHm
18d1ahMmOP6YyaAgB0A95cQi5qfoJqS9JA==
-----END EC PRIVATE KEY-----

pip install ecdsa

"""

import os, sys, binascii, hashlib, ecdsa
from binascii import hexlify
from os.path import join

from ecdsa import SigningKey, VerifyingKey, BadSignatureError

def HEX(s): return hexlify(s).decode("ascii").upper()
dir = os.path.dirname( sys.argv[0] )

image   = join(dir, 'packer',   'app.image')        # tested image
private = join(dir, 'certs',    'ecprivkey.pem')    # is OK
public  = join(dir, 'certs',    'ecpubkey.pem')     # is OK, same as PFX 

f = open(image, 'rb' )            
MSG = f.read( 20628 )   
f.seek( 20628 ) # signature offset is last 64 bytes
old_signature = f.read( 64 )
print('OLD SIGNATURE', HEX(old_signature))

sk = SigningKey.from_pem( open( private ).read(), hashfunc = hashlib.sha256)
#print('SK ', HEX( sk.to_string() ) )
vk = VerifyingKey.from_pem( open( public ).read() )
#print('VK ', HEX( vk.to_string() ) )

new_signature = sk.sign(MSG, hashfunc = hashlib.sha256) 

try:
    vk.verify(old_signature, MSG, hashfunc = hashlib.sha256 )
    print ("verify old signature: OK") # YES !!!
except BadSignatureError:
    print ("APP BAD SIGNATURE")    

try:
    vk.verify(new_signature, MSG, hashfunc = hashlib.sha256 )
    print ("verify new signature: OK") # YES !!!
except BadSignatureError:
    print ("NEW BAD SIGNATURE")  



