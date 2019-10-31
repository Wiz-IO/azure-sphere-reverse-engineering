# AZSPHERE IMAGE PACKER 2020 Georgi Angelov

import os, sys, struct, binascii, time, uuid, hashlib
from os.path import join
from uuid import UUID
from binascii import hexlify
from az_const import *

import ecdsa

def HEX(s): return hexlify(s).decode("ascii").upper()

def get_certificate():
    """
    dir = os.path.dirname( sys.argv[0] )
    f = open(join(dir, '..\\certs\\keystore.bin'), 'rb') # all public keys and thumbprints
    f.seek(6 * 100 + 80) # index 6, header, public_key[64], thumbprint[20]
    data = f.read(20)
    print('SIGNATURE CERTIFICATE', HEX(data))
    f.close()
    """
    #https://docs.microsoft.com/en-us/azure-sphere/reference/azsphere-image
    # Section: Signature - Cert: THUMBPRINT
    return b'\xA8\xD5\xCC\x69\x58\xF4\x87\x10\x14\x0D\x7A\x26\x16\x0F\xC1\xCF\xC3\x1F\x5D\xF0'

##################################################################################
# META DATA [ ID SG DB TP ND ]
##################################################################################

def meta_header(image, section_count = 4):
    image += struct.pack("I", 0x4D345834) 
    image += struct.pack("I", section_count)

##################################################################################
# META SECTION_Debug DB[x28]
# unix_date_64         [  8]
# application_name     [ 32]
##################################################################################
def meta_debug(image, application_name):
    DB  = bytearray()
    DB += struct.pack("HH", SECTION_Debug, 40)
    DB += struct.pack("LL", int(time.time()), 0) # 0x5DA46DCD, Mon, 14 Oct 2019 12:45:01 GMT
    DB += application_name[:32].encode('utf-8')
    size = len(DB)
    if size < 44: DB += (44 - size) * b'\0' 
    print('','DB', HEX(DB))
    image += DB

##################################################################################
# META SECTION_Identity   ID[x24] 
# image_type                [  2] = IMAGE_TYPE_Applications
# reserved                  [  2] = 0
# component_uid             [ 16] = json guid
# image_uid                 [ 16] = new?
##################################################################################
def meta_identity(  image, 
                    image_type = IMAGE_TYPE_Applications, 
                    c_uid = '0E3D632E-03B1-48E7-A9C2-3F5063AD0870', # from json
                    i_uid = ''): # new?     
    ID  = bytearray()
    ID += struct.pack("HH", SECTION_Identity, 0x24)  
    ID += struct.pack("HH", image_type, 0)  
    # component_uid
    u = UUID(c_uid).bytes
    ID += struct.pack("BBBB", u[3], u[2], u[1], u[0])
    ID += struct.pack("BBBB", u[5], u[4], u[7], u[6])
    ID += u[8:16]
    # image_uid
    if i_uid == '': 
        u = uuid.uuid4().bytes
    else: 
        u = UUID(i_uid).bytes
    ID += struct.pack("BBBB", u[3], u[2], u[1], u[0])
    ID += struct.pack("BBBB", u[5], u[4], u[7], u[6])
    ID += u[8:16]
    print('','ID', HEX(ID))
    image += ID

##################################################################################
# META SECTION_TemporaryImage TP[x04]
# flag                          [  4] = SECTION_TemporaryImage
##################################################################################
def meta_temp_image(image, flag = TEMP_IMAGE_UnderDevelopment):
    TP  = bytearray()
    TP += struct.pack("HHL", SECTION_TemporaryImage, 4, flag)  
    print('','TP', HEX(TP))
    image += TP    

##################################################################################
# META SECTION_Signature SG[x18]
# certificate              [ 20]
# type                     [  4] ECDsa256 = 1
##################################################################################
def meta_signature(image, certificate = b''):
    SG  = bytearray()
    SG += struct.pack("HH", SECTION_Signature, 0x18)  
    if certificate == b'':
        SG += get_certificate() # certificate from keystore
    else: 
        SG += certificate
    SG += struct.pack("L", 1) # ECDsa256
    print('','SG', HEX(SG))
    image += SG   

##################################################################################
# META SECTION_ABIDepends  ND[n * uint32_ABI]
##################################################################################
def meta_abi_depends(image, data):
    ND  = bytearray()
    ND += struct.pack("HH", SECTION_ABIDepends, len(data) * 4) 
    for d in data: 
        ND += struct.pack("L", d) 
    print('','ND', HEX(ND))
    image += ND  

##################################################################################
# HASH SIGNATURE -------> not ready
# pip install ecdsa
##################################################################################
def meta_hash(image, type):
    HASH = bytearray()

    m = hashlib.sha256()
    m.update( image )
    print( m.digest() ,len(m.digest()))
    print('HASH', HEX( m.digest() ))

    #PFX.SIGN() ????????????????
    #image += HASH      



