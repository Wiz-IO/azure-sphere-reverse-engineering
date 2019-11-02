# Reverse engineering of Azure Sphere

It sounds weird, doesn't it?

This project is an attempt to **UNIX-LIKE** ( Linux, Mac and Windows ) support platforms for Azure Sphere boards...

Version: 0.0.2

## What needs
* Any IDE as VS Code or Atom ( I use [PlatformIO](https://github.com/Wiz-IO/platform-azure) )
* GCC linux-hard-float ... [example](https://releases.linaro.org/components/toolchain/binaries/7.2-2017.11/)
* [Application Image Packer](https://github.com/Wiz-IO/azure-sphere-reverse-engineering/tree/master/packer)
* [Uploader](https://github.com/Wiz-IO/azure-sphere-reverse-engineering/tree/master/uploader)

## Base codes and Dependency
* pySerial
* ecdsa
* [pytuntap](https://github.com/gonewind73/pytuntap/blob/master/tuntap.py)

## THE SOURCE CODES
* Here is experimental source codes, I use Python to integrate this to [Azure Sphere - PlatformIO](https://github.com/Wiz-IO/platform-azure)
* The **problems** is marked in the source code with **???????**
* Executables:
* * packer/az_packer.py
* * uploader/win_test.py ( next will make unix-like interface )

## THE IMAGE PACKER

The image is **asxipfs** file system ( customization of the [**cramfs**](https://github.com/npitre/cramfs-tools/blob/master/mkcramfs.c) ) plus Microsoft meta-data footer

## THE IMAGE UPLOADER

The protocol is a simple REST-API client over HTTPS ... https://192.168.35.1/2

As first test - [work...](https://raw.githubusercontent.com/Wiz-IO/LIB/master/images/pyAzsphere.jpg) 

UART Slip to Tun/Tap interface
* BaudRate = 921600
* Parity = None
* DataBits = 8
* StopBits = One
* Handshake = RequestToSend

**TAP-Windows Adapter V9**
* [Windows 8 / 10 from OpenVPN](https://openvpn.net/community-downloads/) 
* [Windows 7](https://github.com/OpenVPN/tap-windows6/files/2037295/Tap-Driver.9.00.00.21.zip)
* [GitHub](https://github.com/OpenVPN/tap-windows6)

**Unix-like ... soon** ( windows similar ) [hint](http://thgeorgiou.com/posts/2017-03-20-usb-serial-network/)

**REST-API Commands**

GET, POST, PUT, DELETE ...

azsphere device show-attached
* GET http://192.168.35.2/device/security_state
* Response {"securityState":"SECURE","generalPublicKey":"22...67","deviceIdentityPublicKey":"E1...3E"}

Get Status
* GET https://192.168.35.2/status
* Response {"uptime":288}
