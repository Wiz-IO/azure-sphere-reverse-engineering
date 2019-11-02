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

def create_json(manifest, board, approot):
    dict = create_perifery(board)
    manifest = load_json( manifest )
    json_replace(manifest['Capabilities']['Gpio'], dict)
    json_replace(manifest['Capabilities']['Uart'], dict)
    json_replace(manifest['Capabilities']['SpiMaster'], dict)
    json_replace(manifest['Capabilities']['I2cMaster'], dict)

    print(manifest)

    if 'Name' in manifest:
        if '' == manifest['Name']: error('Manifest.Name is empty'); 
    else:
        error('Manifest.Name missing'); 

    if 'ComponentId' in manifest: uid = UUID( u['ComponentId'], version = 4 )


if __name__ == "__main__":
    DIR = os.path.dirname( sys.argv[0] )
    APPROOT = join(DIR, 'approot')
    MANIFEST = join(DIR, 'app_manifest.json')
    create_json(MANIFEST, 'avnet_aesms_mt3620', APPROOT)