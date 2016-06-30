import socket
import os
# リッスンするホストのIPアドレス
host = "192.168.0.25"

# rawソケットを作成しパブリックなインターフェースにバインド
if os.name == "nt":
    socket_protocol = socket.IPPROTO_IP
else:
    socket_protocol = socket.IPPROTO_ICMP

sniffer = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket_protocol)

sniffer.bind((host, 0))

# キャプチャー結果にIPヘッダを含めるように指定
sniffer.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)

# Windowsの場合はioctlを使用してプロミスキャス・モードを有効化
if os.name == "nt":
    sniffer.ioctl(socket.SIO_RCVALL, socket.RCVALL_ON)

# 単一バケットの読み込み
print(sniffer.recvfrom(65565))

# Windowsの場合はプロミスキャス・モードを無効化
if os.name == "nt":
    sniffer.ioctl(socket.SIO_RCVALL, socket.RCVALL_OFF)