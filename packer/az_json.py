##################################################################################
#   AZSPHERE IMAGE PACKER 2020 Georgi Angelov
#
#   Create approot json manifest
#       
##################################################################################

import os, sys, json, shutil, uuid
from uuid import UUID
from os.path import join, normpath, basename

def error(msg):
   print('[ERROR]', msg); 
   exit(1) 

def load_json(file_name, mode = 'r'):
    f = open(file_name, mode)
    j = json.load( f )
    f.close()  
    return j

def load_hardware():
    return load_json( join(os.path.dirname(sys.argv[0] ), '..', 'json', 'mt3620.json') )

def load_board(name):
    return load_json( join(os.path.dirname(sys.argv[0] ), '..', 'json', name + '.json') )

def get_AppManifestValue(name, h):
    for item in h['Peripherals']:
        if item['Name'] == name: 
            return item['AppManifestValue']
    error('value not exist')

def create_perifery(board):
    d = {}
    hardware = load_hardware()
    board = load_board(board)
    for item in board['Peripherals']:
        map = get_AppManifestValue(item['Mapping'], hardware)
        d[ '$' + item['Name'] ] = map
    return d

def json_replace(key, dict):
    i = 0
    for item in key: 
        key[i] = dict[item]
        i+=1    

def set_default_value(jsn, key, value):
    if key in jsn: # else new
        if '' == jsn[key]:
            jsn[key] = value 
    else:
        jsn[key] = value

def create_json(manifest, board, approot):
    print()
    print('--- CREATE APPROOT MANIFEST ---')
    dict = create_perifery(board)
    manifest = load_json( manifest )

    # REPLACE PERIFERY
    json_replace(manifest['Capabilities']['Gpio'], dict)
    json_replace(manifest['Capabilities']['Uart'], dict)
    json_replace(manifest['Capabilities']['SpiMaster'], dict)
    json_replace(manifest['Capabilities']['I2cMaster'], dict)

    # CHECK VALUES
    set_default_value(manifest, 'Name', 'PROGRAM')
    set_default_value(manifest, 'ComponentId', str(uuid.uuid4()).upper())
    set_default_value(manifest, 'EntryPoint', '/bin/app')
    set_default_value(manifest, 'TargetApplicationRuntimeVersion', 3)
    #"TargetBetaApis":"Beta1905"
    
    #print(manifest)

    print('APPLICATION:', manifest['Name'], manifest['ComponentId'])
    return manifest

def clean(path):
    for c in os.listdir(path):
        full_path = os.path.join(path, c)
        if os.path.isfile(full_path):
            os.remove(full_path)
        else:
            shutil.rmtree(full_path)
    try: os.remove(path)     
    except: pass  

def create_approot_folder(path):
    if True == os.path.isdir(path):
        clean(path)
    else:
        os.makedirs(path)      

def copy_files(approot, files):
    for item in files:
        copyfile(item, join(approot, os.path.basename(item)) ) 

if __name__ == "__main__":
    DIR = os.path.dirname( sys.argv[0] )

    APPROOT     = join(DIR, 'test_approot')
    MANIFEST    = join(DIR, 'app_manifest.json')
    BOARD       = 'avnet_aesms_mt3620'
    
    SDK         = 3
    BETA        = None
    BIN         = 'app' # the elf name
    FILES       = list() # path to files

    create_approot_folder(APPROOT)
    manifest = create_json(MANIFEST, BOARD, APPROOT)
    os.makedirs( join(APPROOT, 'bin') ) 
    
    # COPY app to bin
    #copy_files(join(APPROOT, 'bin'), app)
    
    # COPY other files
    copy_files(APPROOT, FILES)

    # SAVE MANIFEST
    with open(join(APPROOT, 'app_manifest.json'), 'w+') as f: json.dump(manifest, f, indent=4)