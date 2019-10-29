############################################################################
#   Dependency:
#       Windows: TAP Driver tap0901 - TAP-Windows Adapter V9
#       pySerial
############################################################################

import os, sys, struct, time, socket, threading, subprocess, logging, random
from ctypes import *
from ctypes.wintypes import *
from ctypes import wintypes
from serial import Serial
from binascii import hexlify
import slip 
from rest_api import Azure
############################################################################
PYTHON2 = sys.version_info[0] < 3  # True if on pre-Python 3

def PrintHex(s):
    if False == PYTHON2: 
        if str == type(s):
            s = bytearray(s, 'utf-8')
    return hexlify(s).decode("ascii").upper()
############################################################################

AZ_IP  = b'\xC0\xA8\x23\x01' # 192.168.35.1
MY_IP  = b'\xC0\xA8\x23\x02' # 192.168.35.2
MY_MAC = b'\x00\xFF\x11\x22\x33\x44' # const
AZ_MAC = b'' # unknow


GENERIC_READ            = 0x80000000
GENERIC_WRITE           = 0x40000000
FILE_SHARE_READ         = 1 
FILE_SHARE_WRITE        = 2 
OPEN_EXISTING           = 3
FILE_ATTRIBUTE_SYSTEM   = 4
FILE_FLAG_OVERLAPPED    = 0x40000000

class _OVERLAPPED(Structure):
    _fields_ = [
        ("Internal",        ULONG),
        ("InternalHigh",    ULONG),
        ("Offset",          DWORD),
        ("OffsetHigh",      DWORD),
        ("hEvent",          HANDLE)
    ]
    def __init__(self):
        self.Offset         =  0
        self.OffsetHigh     =  0

OVERLAPPED   = _OVERLAPPED
LPOVERLAPPED = POINTER(_OVERLAPPED)

LPDWORD = POINTER(DWORD)

_stdcall_libraries = {}
_stdcall_libraries['kernel32'] = WinDLL('kernel32')

DeviceIoControl = _stdcall_libraries['kernel32'].DeviceIoControl
DeviceIoControl.restype = BOOL
DeviceIoControl.argtypes = [HANDLE, DWORD, LPVOID, DWORD, LPVOID, DWORD, LPDWORD, LPVOID]

ResetEvent = _stdcall_libraries['kernel32'].ResetEvent
ResetEvent.restype = BOOL
ResetEvent.argtypes = [HANDLE]

ReadFile = _stdcall_libraries['kernel32'].ReadFile
ReadFile.restype = BOOL
ReadFile.argtypes = [HANDLE, LPVOID, DWORD, LPDWORD, LPOVERLAPPED]

WriteFile = _stdcall_libraries['kernel32'].WriteFile
WriteFile.restype = BOOL
WriteFile.argtypes = [HANDLE, LPCVOID, DWORD, LPDWORD, LPOVERLAPPED]

GetOverlappedResult = _stdcall_libraries['kernel32'].GetOverlappedResult
GetOverlappedResult.restype = BOOL
GetOverlappedResult.argtypes = [HANDLE, LPOVERLAPPED, LPDWORD, BOOL]


def TunTap(nic_type, nic_name = None):
    if not sys.platform.startswith("win"):
        tap = Tap(nic_type,nic_name) # Unix-Like
    else:
        tap = WindowsTap(nic_type)   # Windows
    tap.create()
    return tap

class Tap(object):
    def __init__(self, nic_type, nic_name = None):
        self.nic_type = nic_type
        self.name = nic_name
        self.mac = b"\x00"*6
        self.handle = None
        self.ip = None
        self.mask = None
        self.gateway = None
        self.read_lock = threading.Lock()
        self.write_lock = threading.Lock()
        self.quitting = False


class WindowsTap(Tap):
    def __init__(self,nic_type):
        super().__init__(nic_type)
        self.component_id = "tap0901"
        self.adapter_key = r'SYSTEM\CurrentControlSet\Control\Class\{4D36E972-E325-11CE-BFC1-08002BE10318}'
        self.TAP_IOCTL_GET_MAC                  = self._TAP_CONTROL_CODE( 1, 0)
        self.TAP_IOCTL_GET_VERSION              = self._TAP_CONTROL_CODE( 2, 0)
        self.TAP_IOCTL_GET_MTU                  = self._TAP_CONTROL_CODE( 3, 0)
        self.TAP_IOCTL_GET_INFO                 = self._TAP_CONTROL_CODE( 4, 0)
        self.TAP_IOCTL_CONFIG_POINT_TO_POINT    = self._TAP_CONTROL_CODE( 5, 0)
        self.TAP_IOCTL_SET_MEDIA_STATUS         = self._TAP_CONTROL_CODE( 6, 0)#
        self.TAP_IOCTL_CONFIG_DHCP_MASQ         = self._TAP_CONTROL_CODE( 7, 0)
        self.TAP_IOCTL_GET_LOG_LINE             = self._TAP_CONTROL_CODE( 8, 0)
        self.TAP_IOCTL_CONFIG_DHCP_SET_OPT      = self._TAP_CONTROL_CODE( 9, 0)
        self.TAP_IOCTL_CONFIG_TUN               = self._TAP_CONTROL_CODE(10, 0)#
        self.read_overlapped                    = OVERLAPPED()
        self.read_overlapped.hEvent             = ctypes.windll.kernel32.CreateEventW(None, True, False, None)
        self.write_overlapped                   = OVERLAPPED()
        self.write_overlapped.hEvent            = ctypes.windll.kernel32.CreateEventW(None, True, False, None)

    def _CTL_CODE(self,device_type, function, method, access):
        return (device_type << 16) | (access << 14) | (function << 2) | method;

    def _TAP_CONTROL_CODE(self,request, method):
        return self._CTL_CODE(34, request, method, 0)

    def OpenKey(self, root, key):
        KEY_QUERY_VALUE = 0x0001 
        KEY_READ = 0x00020019
        INVALID_HANDLE_VALUE = 4294967295
        val = HKEY(INVALID_HANDLE_VALUE)
        err = ctypes.windll.advapi32.RegOpenKeyExW( root, key, 0, KEY_READ, byref( val ) )
        if 0 == err: 
            return HKEY(val.value)
        print('[ERROR] OpenKey', key)
        return None       

    def QueryValueString(self, hkey, name):
        size = 256
        lpcbData = DWORD(size)
        buf = create_string_buffer(size)
        err = ctypes.windll.advapi32.RegQueryValueExW( hkey, name, 0, b'REG_SZ', cast(buf, LPBYTE), byref( lpcbData ) )
        if 0 == err:
            return buf[::2].decode().rstrip('\x00')
        print('[ERROR] QueryValueString', name)
        return None

    def _get_device_guid(self):
        HKEY_LOCAL_MACHINE = 2147483650 
        adapters = self.OpenKey(HKEY_LOCAL_MACHINE, self.adapter_key)
        if adapters == None: 
            return None
        for i in range(30):
            enum_name = create_unicode_buffer(32) # 00XX
            err = ctypes.windll.advapi32.RegEnumKeyW(adapters, i, enum_name, 32)
            if 0 == err:
                adapter = self.OpenKey(adapters, enum_name)
                if c_void_p(0) == adapter: continue
                #print('ADAPTER', i, adapter)
                if self.component_id == self.QueryValueString(adapter, 'ComponentId'):
                    guid = self.QueryValueString(adapter, 'NetCfgInstanceId')
                    print('FOUND', self.component_id, guid)
                    return guid
            else: break
        return None

    def _mac2string(self, mac):
        print('mac', mac)
        mac_string = ""
        for i in range( len(mac) ):
            mac_string += "%02X"%mac[i]
            if i< len(mac)-1:
                mac_string +="-"
        return mac_string

    def _getNameByMac(self, mac):
        result = str(subprocess.check_output("ipconfig/all", shell = True))#.decode().encode().decode()
        res = result.split("adapter")
        for i in range(1, len(res)):
            if res[i].find( self._mac2string(mac) ) > 0:
                res = res[i].split(":")[0].strip()
                print('FIND ADAPTER', res)
                return res
        print('NO ADAPTER')

    def create(self):
        guid =  self._get_device_guid()
        if None == guid:
            print('[ERROR] TAP not found')
            return None
        name = "\\\\.\\Global\\%s.tap"%guid
        self.handle = ctypes.windll.kernel32.CreateFileA(
            name.encode(),
            GENERIC_READ | GENERIC_WRITE, 
            0,#FILE_SHARE_READ | FILE_SHARE_WRITE, 
            None, 
            OPEN_EXISTING, 
            FILE_ATTRIBUTE_SYSTEM | FILE_FLAG_OVERLAPPED,
            None
        )        
        if self.handle == -1: # INVALID_HANDLE_VALUE
            print('TAP-Windows Adapter V9 NOT FOUND')
            return None # [WinError 31] A device attached to the system is not functioning.
            raise ctypes.WinError()
            return None
        if self.handle:
            #print('TAP-TUN FILE HANDLE =', self.handle)
            return self
        return None

    def config(self, ip, mask, gateway = "0.0.0.0"):
        self.ip = ip
        self.mask = mask
        self.gateway = gateway
        try:
            input  = b'\x01\x00\x00\x00' # true
            output = create_string_buffer(4)
            res = DWORD(0)
            ctypes.windll.kernel32.DeviceIoControl(self.handle, self.TAP_IOCTL_SET_MEDIA_STATUS, input, 4, output, 4, byref(res), None)
            print('output', output)
            ipnet  = struct.pack("I",struct.unpack("I", socket.inet_aton(self.ip))[0]&struct.unpack("I", socket.inet_aton(self.mask))[0])
            ipcode = socket.inet_aton(self.ip) + ipnet + socket.inet_aton(self.mask)
            if self.nic_type=="Tap":
                flag = self.TAP_IOCTL_CONFIG_POINT_TO_POINT
            if self.nic_type=="Tun":
                flag =  self.TAP_IOCTL_CONFIG_TUN
            ctypes.windll.kernel32.DeviceIoControl(self.handle, flag, ipcode, 16, None, 0, byref(res), None)
            self.mac= create_string_buffer(6)
            ctypes.windll.kernel32.DeviceIoControl(self.handle, self.TAP_IOCTL_GET_MAC, self.mac, 6, self.mac, 6, byref(res), None) # ???
            print('self.mac', self.mac)
            self.name = self._getNameByMac(self.mac)          
        except Exception as exp:
            print('[ERROR]', exp)
            logging.debug(exp)
            ctypes.windll.kernel32.CloseHandle(self.handle)
            exit(1)
        print('self.name', self.name)
        sargs = r"netsh interface ip set address name=NAME source=static addr=ADDRESS mask=MASK gateway=GATEWAY"
        sargs = sargs.replace("NAME", "\"%s\""%self.name)
        sargs = sargs.replace("ADDRESS", self.ip)
        sargs = sargs.replace("MASK", self.mask)
        if self.gateway == "0.0.0.0":
            sargs = sargs.replace("gateway=GATEWAY","")
        else:
            sargs = sargs.replace("GATEWAY", self.gateway)
        subprocess.check_call(sargs, shell = True)

    def close(self):
        ctypes.windll.kernel32.CloseHandle(self.read_overlapped)
        ctypes.windll.kernel32.CloseHandle(self.write_overlapped)
        err = ctypes.windll.kernel32.CloseHandle(self.handle)
        if 0 == err: raise ctypes.WinError()
        print('close', self.handle, err)

    def read(self): # return bufer
        self.read_lock.acquire()
        RESULT = b''
        RD = DWORD()
        try:
            err = ResetEvent(self.read_overlapped.hEvent) # ok (TRUE)
            if 0 == err: raise ctypes.WinError()
            BUFFER = create_string_buffer(2000)  
            err = ReadFile(self.handle, cast(BUFFER, LPBYTE), 2000, byref(RD), self.read_overlapped) # OK (TRUE)
            lastError = GetLastError()
            if lastError == 997: # ERROR_IO_PENDING
                err = GetOverlappedResult(self.handle, self.read_overlapped, byref(RD), True)
                if 0 == err: raise ctypes.WinError()
                RESULT = BUFFER[:RD.value]
            elif lastError == 0:
                RESULT = BUFFER
            elif lastError == 995:
                print('[ERROR] MEDIA IS NOT CONNECTED')
                exit(1)
            else: 
                print('ReadFile()', 'H = {}, E = {}'.format(self.handle, lastError) )
                raise ctypes.WinError()
        finally:
            self.read_lock.release() 
        return bytearray(RESULT)

    def write(self, data): # return writed data size
        self.write_lock.acquire()
        RESULT = 0
        LEN = len(data)
        BUFFER = create_string_buffer(LEN)
        for i in range(LEN): BUFFER[i] = data[i]
        WR = DWORD()
        try:
            if 0 == ResetEvent(self.write_overlapped.hEvent): raise ctypes.WinError()
            if WriteFile(self.handle, cast(BUFFER, LPBYTE), LEN, byref(WR), self.write_overlapped): # OK (TRUE)
                RESULT = WR
            else:
                lastError = GetLastError()               
                if 997 == lastError: # ERROR_IO_PENDING
                    err = GetOverlappedResult(self.handle, self.write_overlapped, byref(WR), True)
                    if 0 == err: raise ctypes.WinError()
                    RESULT = WR
                elif 0 == lastError:
                    RESULT = LEN
                elif 995 == lastError:
                    print('[ERROR] MEDIA IS NOT CONNECTED')
                    exit(1)                    
                else:
                    print('WriteFile()', 'H = {}, E = {}'.format(self.handle, lastError) )
                    raise ctypes.WinError()
        finally:
            self.write_lock.release()
        return RESULT

    def try_route(self, packet):
        global MY_MAC, AZ_MAC
        if packet[12:14] == b'\x08\x06': # ARP
            if packet[28:32] != AZ_IP: # is not 192.168.35.1 ... allway is this
                print('[REJECT] IS NOT 192.168.35.1', PrintHex(packet[28:32]) )
                return
            if packet[38:42] != MY_IP: # is not for me
                print('[REJECT] IS NOT FOR ME', PrintHex(packet[38:42]) )
                return
            if packet[20:22] != b'\x00\x01': # is not request
                print('[REJECT] IS NOT ARP REQUEST')
                return                
            if AZ_MAC == b'':
                AZ_MAC =packet[6:12]
                #print('DRIVER MAC ADDRESS', PrintHex(AZ_MAC))
            #print ( "ARP-REQUEST", PrintHex(MY_MAC))
            ###print ( "-->", PrintHex(packet))
            packet[  : 6], packet[6:12] = packet[6:12], MY_MAC # swap eth mac
            packet[20:22] = b'\x00\x02' # set response
            packet[22:32], packet[32:42] = packet[32:42], packet[22:32] # swap arp
            packet[22:28] = MY_MAC
            ###print ( "<--", PrintHex(packet))
            self.write(packet) # send ARP answer 
            return
        if packet[12:14] == b'\x08\x00' and packet[23] == 6: # IP/TCP
            if packet[30:34] == MY_IP and packet[36:38] == b'\x01\xBB': # https://192.168.35.2:443    
                #[00FF11223344][00FF9832CF41][0800]-->450000340298400080[06]30D8[C0A82301][C0A82302]D9CA[01BB]3714....  
                return packet[14:] # skip ethernet

    class SpipRead(threading.Thread):
        def __init__(self, this):
            threading.Thread.__init__(self)
            self.this = this
        def run(self):
            #print('[SpipRead] BEGIN')
            slipDriver = slip.Driver()
            while self.this.isSRunnig:
                packet = bytearray( self.this.read() ) 
                if 0 == len(packet): # ERR 995
                    time.sleep(1)
                    continue
                #print ( "[SpipRead]", PrintHex(packet))
                p = self.this.try_route(packet)
                if None == p: continue  
                s = slipDriver.send(p)     
                self.this.serial.write(s)   
                ###print ( "[SERIAL-PC] >>>", PrintHex(s))                    
            print('[SpipRead] END')
            self.this.isSRunnig == False

    class SlipWrite(threading.Thread):
        def __init__(self, this):
            threading.Thread.__init__(self)
            self.this = this
        def run(self):
            #print('[SpipWrite] BEGIN')
            slipDriver = slip.Driver()
            while self.this.isSRunnig: 
                rx = bytearray(self.this.serial.read(2000) )
                if b'' != rx: 
                    data = slipDriver.receive(rx) # A (possibly empty) list of decoded messages.    
                    for tx in data:
                        ###print('[SERIAL-AZ] <<<', PrintHex(tx))
                        tx = AZ_MAC + MY_MAC + b'\x08\x00' + tx
                        self.this.write(tx)                                
            print('[SpipWrite] END') 
            self.this.isSRunnig == False          

    def start(self, com_port):
        global MY_MAC
        self.serial = Serial(com_port, 921600) #  115200 3000000   
        self.serial.timeout = 0
        self.serial.rtscts = True # RequestToSend
        #print('DEVICE MAC ADDRESS', PrintHex(MY_MAC))
        self.isSRunnig = True
        self.SW = self.SlipWrite(self)        
        self.SR = self.SpipRead(self)
        self.SR.start()
        self.SW.start()
        time.sleep(0.1)
        if False == self.isSRunnig:
            print('[ERROR] START')
            exit(1)
        print('--------------AZSPHERE--------------')
        a = Azure()
        a.get_dev_status()
        a.get_dev_id()        
        print('----------------DONE----------------')
        exit(0)

t = WindowsTap('Tap')
if None != t.create():
    t.start('COM27')
#t.close()