##################################################################################
# POSIX
##################################################################################

S_ISOCK     = 49152 # 0xC000
S_ISLNK     = 40960 # 0xA000
S_ISREG     = 32768 # 0x8000
S_ISBLK     = 24576 # 0x6000
S_ISDIR     = 16384 # 0x4000
S_ISCHR     =  8192 # 0x2000
S_IFIFO     =  4096 # 0x1000
S_IFMT      = S_IFIFO | S_ISCHR | S_ISDIR | S_ISREG # 0xF000
S_IRUSR     = 256 # 0x0100
S_IWUSR     = 128 # 0x0080
S_IXUSR     =  64 # 0x0040
S_IRWXU     = S_IXUSR | S_IWUSR | S_IRUSR # 0x01C0
S_IRGRP     = 32 # 0x0020
S_IWGRP     = 16 # 0x0010
S_IXGRP     = 8
S_IRWXG     = S_IXGRP | S_IWGRP | S_IRGRP # 0x0038
S_IROTH     = 4
S_IWOTH     = 2
S_IXOTH     = 1
S_IRWXO     = S_IXOTH | S_IWOTH | S_IROTH # 0x0007
S_ISUID     = 2048 # 0x0800
S_ISGID     = 1024 # 0x0400
S_ISVTX     =  512 # 0x0200
ONLY_PERM   = S_IRWXO | S_IRWXG | S_IRWXU # 0x01FF
CLEAR_PERM  = S_ISVTX | S_ISGID | S_ISUID | S_IFMT # 0xFE00

DEFAULT_DIR_PERM  = 493 # 0x01ED
DEFAULT_FILE_PERM = 420 # 0x01A4
EXE_MODE = DEFAULT_FILE_PERM | S_ISREG | S_IXUSR | S_IXGRP | S_IXOTH | S_ISVTX # 0x83ED

##################################################################################
# META DATA 
##################################################################################

SECTION_Debug                           = 16964 # 0x4244 DB * 
SECTION_LegacyABIDepends                = 17473 # 0x4441 AD
SECTION_Identity                        = 17481 # 0x4449 ID * 
SECTION_ABIDepends                      = 17486 # 0x444E ND * 
SECTION_Legacy                          = 18252 # 0x474C LG
SECTION_Signature                       = 18259 # 0x4753 SG * 
SECTION_Compression                     = 19779 # 0x4D43 CM
SECTION_RequiredFlashOffset             = 20306 # 0x4F52 RO
SECTION_LegacyABIProvides               = 20545 # 0x5041 AP
SECTION_ABIProvides                     = 20558 # 0x504E NP * 
SECTION_TemporaryImage                  = 20564 # 0x5054 TP * 
SECTION_Revocation                      = 22098 # 0x5652 RV

##################################################################################

IMAGE_TYPE_Invalid                      =  0 
IMAGE_TYPE_OneBL                        =  1 
IMAGE_TYPE_PlutonRuntime                =  2 
IMAGE_TYPE_WifiFirmware                 =  3 
IMAGE_TYPE_SecurityMonitor              =  4 
IMAGE_TYPE_NormalWorldLoader            =  5 
IMAGE_TYPE_NormalWorldDTB               =  6 
IMAGE_TYPE_NormalWorldKernel            =  7 
IMAGE_TYPE_RootFs                       =  8 
IMAGE_TYPE_Services                     =  9 
IMAGE_TYPE_Applications                 = 10 
IMAGE_TYPE_FirmwareConfig               = 13 
IMAGE_TYPE_BootManifest                 = 16 
IMAGE_TYPE_NormalWorldFileSystem        = 17 
IMAGE_TYPE_TrustedKeystore              = 19 
IMAGE_TYPE_Policy                       = 20 
IMAGE_TYPE_CustomerBoardConfig          = 21 
IMAGE_TYPE_UpdateCertStore              = 22 
IMAGE_TYPE_BaseSystemUpdateManifest     = 23 
IMAGE_TYPE_FirmwareUpdateManifest       = 24
IMAGE_TYPE_CustomerUpdateManifest       = 25 
IMAGE_TYPE_RecoveryManifest             = 26 
IMAGE_TYPE_ManifestSet                  = 27 
IMAGE_TYPE_Other                        = 28 

##################################################################################

TEMP_IMAGE_None                         = 0
TEMP_IMAGE_RemoveAtBoot                 = 1
TEMP_IMAGE_UnderDevelopment             = 2

##################################################################################


