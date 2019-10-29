############################################################################
# THE PROJECT IS IN PROGRESS...
#
#   Dependency:
#       requests
#
# https://requests.kennethreitz.org/en/master/user/advanced/
# https://urllib3.readthedocs.io/en/latest/advanced-usage.html#ssl-warnings
############################################################################

from __future__ import print_function
import os, time, requests, urllib3
urllib3.disable_warnings()
from os.path import join

DEBUG           = True
TEST_IMAGE      = '1640b7fb-4924-46df-ae72-38998065455b'

def ERROR(message):
    print("[ERROR] {}".format(message))
    time.sleep(0.05)
    exit(1)

def ASSERT(flag, message):
    if flag == False:
        ERROR(message)

class Azure:
    def __init__(self):
        self.dir    = os.path.dirname( os.path.realpath(__file__) )
        self.cert   = (join(self.dir, 'gatewayd-server-cert.pem'), join(self.dir, 'gatewayd-server-key.pem'))
        self.url    = 'https://192.168.35.2'
        self.ses    = requests.Session()

    def GET(self, URL, debug = DEBUG):
        if debug:
            print( '[GET] ' + URL )         
        r = self.ses.get(URL, cert=self.cert, verify=False)
        ASSERT( 200 == r.status_code, "[GET] Response Code: {}".format( r.status_code ) )    
        if debug:
            print( '[RESPONSE] ', end='' )
            print( r.text.encode(encoding='UTF-8', errors='replace'), end='' )
            print(  )
            #time.sleep(0.01)
        return r.text         

    def get_dev_id(self):
        self.GET( str("/".join([self.url, 'device', 'security_state'])) )
        # {"securityState":"SECURE","generalPublicKey":"228A...23167","deviceIdentityPublicKey":"E194...3C3E"}

    def get_dev_status(self):
        self.GET( str("/".join([self.url, 'status'])) )
        # {"uptime":288} 
        
    def get_app_status(self, guid = TEST_IMAGE):
        self.GET( str("/".join([self.url, 'app', 'status', guid])) )
        # {"state":"running"}
        # {"state":"notPresent"}

    def get_telemetry(self): # binary
        self.GET( str("/".join([self.url, 'telemetry'])) ) 
    def get_log(self): # binary
        self.GET( str("/".join([self.url, 'log'])) )        

    def delete_image(self, guid = TEST_IMAGE):
        URL = "/".join([self.url, 'app', 'image', guid])
        r = self.s.delete(URL, cert=self.cert, verify=False)
        ASSERT( 200 == r.status_code, "delete_image Code: {}".format( r.status_code ) )       
        print(r.text)
        return r.text         


#a = Azure()
#a.get_dev_status()
#a.get_dev_id()
#a.get_app_status() 
