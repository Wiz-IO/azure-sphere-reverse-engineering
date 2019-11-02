import os, sys, json, shutil, uuid
from uuid import UUID
from os.path import join, normpath, basename

def error(msg):
   print('[ERROR]', msg); 
   exit(1) 

def create_json(manifest, hardware, approot):
    f = open(manifest, 'r')
    u = json.load( f )
    f.close()
    print(u)

    f = open(hardware, 'r+')
    hj = json.load( f )
    f.close()

    if 'Name' in u:
        if '' == u['Name']: error('Manifest.Name is empty'); 
    else:
        error('Manifest.Name missing'); 

    if 'ComponentId' in u: uid = UUID( u['ComponentId'], version = 4 )




    #f_dst = open(manifest, 'w+')
    #f.seek(0)
    #json.dump(data, f, indent=4) 
    #f.truncate()  


DIR = os.path.dirname( sys.argv[0] )
HARDWARE = join(DIR, '..', 'json', 'mt3620.json')#.replace('/','\\')
APPROOT = join(DIR, 'approot')#.replace('/','\\')
MANIFEST = join(DIR, 'app_manifest.json')#.replace('/','\\')
create_json(MANIFEST, HARDWARE, APPROOT)