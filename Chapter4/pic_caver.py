import os
import re
import zlib
import cv2wrap as cv2


from scapy.all import *

pictures_directory = 'pictures'
faces_directory = 'faces'
pcap_file = 'bhp.pcap'

def http_assembler(pcap_file):
    carved_images = 0
    faces_detected = 0

    a = rdpcap(pcap_file)

    # sessionsはこんな感じの辞書
    # { session: packetlist }
    # ..., 'UDP 192.168.0.15:58890 > 95.172.70.138:17771': <PacketList: TCP:0 UDP:1 ICMP:0 Other:0>, ...
    sessions = a.sessions()

    for session in sessions:
        http_payload = ''

        for packet in sessions[session]:
            try:
                if packet[TCP].dport == 80 or packet[TCP].sport == 80:
                    # ストリームの再構築
                    http_payload += str(packet['TCP'].payload)
            except:
                pass

        headers = get_http_headers(http_payload)

        if headers is None:
            continue


        image, image_type = extract_image(headers, http_payload)

        if image is not None and image_type is not None:
            # 画像の保存
            file_name = "{}-pic_caver_{}.{}".format(pcap_file, carved_images, image_type)

            fd = open(os.path.join(pictures_directory, file_name), 'wb')

            fd.write(image)
            fd.close()

            carved_images += 1

            # 顔検出
            try:
                result = face_detect(os.path.join(pictures_directory, file_name), file_name)

                if result is True:
                    faces_detected += 1
            except:
                pass
    return carved_images, faces_detected

carved_images, face_detected = http_assembler(pcap_file)

print("Extracted: {} images".format(carved_images))
print("Detected: {} faces".format(face_detected))
