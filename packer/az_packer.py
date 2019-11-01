# AZSPHERE IMAGE PACKER 2020 Georgi Angelov

import os, sys, struct, binascii
from os.path import join
from binascii import hexlify
from az_const import *
from az_meta import *

PAGE_SIZE = 4096
NODE_ROOT = 1
NODE_DIR  = 2
NODE_FILE = 3

img = bytearray()
nodes = []
fs_info = bytearray()
data_offset = PAGE_SIZE

def roundUp4(num): return num + 3 & -4

def default_header(bin):
    bin += struct.pack("I", 0x28CD3D45)                         # offset[0]
    bin += struct.pack("I", 0)                                  # size of image
    bin += struct.pack("I", 3)                                  # 3
    bin += struct.pack("I", 0)                                  # 0
    bin += bytearray("Compressed ROMFS".encode('utf-8'))        # offset[16:32]
    bin += struct.pack("I", 0)                                  # crc32
    bin += struct.pack("I", 0)                                  # 0
    bin += struct.pack("I", 0)                                  # 0
    bin += struct.pack("I", 0)                                  # root entry count
    bin += bytearray("Compressed\0\0\0\0\0\0".encode('utf-8'))  # offset[48:64]

def add_fs_info(info, node):
    info += struct.pack("H", node.mode)                         # [0, 1]
    info += struct.pack("H", node.uid)                          # [2, 3]
    info += struct.pack("L", node.file_size)[:3]                # [4, 5, 6]    
    info += struct.pack("B", node.gid)                          # [7]
    name_size = ( node.name_round_up >> 2 ) & 0x0000003F
    if node.type == NODE_FILE:
        offset = node.data_offset
    else:
        offset = len(info) + 4 + node.name_round_up
    offset = offset >> 2
    offset = ( offset << 6 ) & 0xFFFFFFC0
    info += struct.pack("L", offset | name_size)
    if node.type != NODE_ROOT:
        info += node.fs_name   

def find_parent(path):
    parent = os.path.normpath( os.path.join(path, os.pardir) )
    for node in nodes:
        if parent == node.path:
            return node
    return None

######################################################################################

class INODE():
    def __init__(self, path):
        global nodes, fs_info, data_offset
        self.index = len(nodes)        
        self.path = path
        self.name = os.path.basename(path)
        print('NODE[{}]'.format(self.index), self.name)
        self.name_round_up = roundUp4( len(self.name) )
        self.fs_name  = bytearray( self.name.encode('utf-8') ) 
        self.fs_name += ( self.name_round_up  - len(self.name) ) * b'\0'

        self.type = 0
        self.mode = DEFAULT_DIR_PERM | S_ISDIR
        self.uid = 0 # ? allways 0
        self.gid = 0 # ? allways 0
        self.file_size = 0
        self.data_size = 0
        self.data_offset = 0

        if 0 == self.index: 
            #print('NODE-ROOT', self.name)
            self.type = NODE_ROOT
            self.data_size = PAGE_SIZE
            self.name_round_up = 0
            default_header(fs_info)

        elif os.path.isdir(self.path):
            #print('NODE-DIR', self.name)
            self.type = NODE_DIR 

        elif os.path.isfile(self.path):
            #print('NODE-FILE', self.name)
            self.type = NODE_FILE
            self.file_size = os.path.getsize(path)
            self.data_size = ( int( self.file_size / PAGE_SIZE ) + 1 ) * PAGE_SIZE            
            #print('DATA-OFFSET', hex(data_offset))
            #print('DATA-SIZE  ', hex(self.data_size))
            self.data_offset = data_offset 
            data_offset += self.data_size
            #print('FILE-SIZE  ', hex(self.file_size))
            f = open(self.path,'rb') 
            self.data = bytearray( f.read() ) 
            #print('READ-SIZE  ', hex( len( self.data ) ))
            f.close()
            if self.data[:4] == b'\x7FELF':
                self.mode = EXE_MODE # 0x83ED
                #print('FILE-EXECUTABLE')
            else: 
                self.mode = DEFAULT_FILE_PERM | S_ISREG | S_ISVTX
            self.data += (self.data_size - self.file_size) * b'\0'
            #print('TOTL-SIZE  ', hex( len( self.data ) ))

        nodes.append( self )

######################################################################################

def create_approot(path, image):
    if False == os.path.isdir(path):
        print('[ERROR] approot path not found')
        exit(1)
    print()
    print('--- CRETE IMAGE ---')        
    # CREATE INODES
    for PATH, DIRS, FILES in os.walk(path): 
        PATH = PATH.replace('/','\\')
        node = INODE( PATH ) # make folder
        for f in FILES:    
            node = INODE( join(PATH, f) ) # make file
    # UPDATE FOLDER SIZE
    for node in nodes: 
        parent = find_parent(node.path)
        if parent:             
            parent.file_size += 12 + node.name_round_up
            #print('folder', parent.name, 'add size =', parent.file_size)
    # ADD INODES
    for node in nodes: 
        add_fs_info(fs_info, node)
    image += fs_info + (PAGE_SIZE - len(fs_info)) * b'\0'    
    # ADD DATA
    for node in nodes: 
        if hasattr(node, 'data'): 
            image += node.data       
    # UPDATE HEADER
    image[ 4: 8] = struct.pack("I", len(image))  
    image[44:48] = struct.pack("I", len(nodes)) 
    crc = binascii.crc32(image)
    image[32:36] = struct.pack("I", crc)    

def write_image(name, image):
    f = open(name,'wb') 
    f.write(image) 
    f.close()  

######################################################################################

DIR = os.path.dirname( sys.argv[0] )
create_approot(join(DIR, 'approot'), img) 
img += create_manifest()
write_image(join(DIR, 'test_image.image'), img)
