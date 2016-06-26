import sys
import socket
import threading
import argparse


def server_loop(local_host, local_port, remote_host, remote_port, receive_first):

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        server.bind((local_host, local_port))
    except:
        print("[!!] Failed to listen on {}:{}".format(local_host, local_port))
        print("[!!] Check for other listening sockets or correct permissions.")
        sys.exit(1)

    print("[*] Listening on {}:{}".format(local_host, local_port))

    server.listen(5)

    while True:
        client_socket, addr = server.accept()

        # ローカル側からの接続情報を表示
        print("[==>] Received incoming connection from {}:{}".format(addr[0], addr[1]))

        # リモートホストと通信するためのスレッドを開始
        proxy_thread = threading.Thread(
            target=proxy_handler,
            args=(client_socket, remote_host, remote_port, receive_first)
        )

        proxy_thread.start()


def proxy_handler(client_socket, remote_host, remote_port, recieve_first):

    # リモートホストへ接続
    remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    remote_socket.connect((remote_host, remote_port))

    # 必要ならリモートホストからデータを受信
    if recieve_first:

        remote_buffer = receive_from(remote_socket)
        hexdump(remote_buffer)

        # 受信データ処理関数にデータ受け渡し
        remote_buffer = response_handler(remote_buffer)

        # もしローカル側に対して送るデータがあれば送信
        if len(remote_buffer):
            print("[<==] Sending {} bytes to localhost.".format(len(remote_buffer)))

            client_socket.send(remote_buffer)

    # ローカルからのデータ受信、リモートへの送信、ローカルへの送信の繰り返しを行うループ
    while True:

        # ローカルホストからデータ受信
        local_buffer = receive_from(client_socket)

        if len(local_buffer):

            print("[==>] Received {} bytes from localhost.".format(len(local_buffer)))
            hexdump(local_buffer)

            # 送信データ処理関数にデータ渡し
            local_buffer = request_handler(local_buffer)

            # リモートホストへのデータ送信
            remote_socket.send(local_buffer)
            print("[==>] Sent to remote.")

        # 応答の受信
        remote_buffer = receive_from(remote_socket)

        if len(remote_buffer):
            print("[<==] Received {} bytes from remote.".format(len(remote_buffer)))

            hexdump(remote_buffer)

            # 受信データ処理関数にデータ受け渡し
            remote_buffer = response_handler(remote_buffer)

            # ローカル側に応答データを送信
            client_socket.send(remote_buffer)

            print("[<==] Sent to localhost.")

        # ローカル側・リモート側双方からデータが来なければ接続を閉じる
        if not len(local_buffer) or len(remote_buffer):
            client_socket.close()
            remote_socket.close()
            print("[*] No more data. Closing connections.")

            break


# 16進数ダンプを整形して表示する関数
def hexdump(src, length=16):
    result = []
    # よくわからんので全部2で
    digits = 2
    # digits = 4 if isinstance(src, str) else 2

    for i in range(0, len(src), length):
        s = src[i:i+length] # -> byte
        hexa = ' '.join(["{:0{width}X}".format(x, width=digits) for x in s])
        text = ''.join([chr(x) if 0x20 <= x < 0x7F else '.' for x in s])
        result.append("{:04X}    {:{width}s}    {:s}".format(i, hexa, text, width=length*(digits + 1)))

    print('\n'.join(result))


def receive_from(connection):

    buffer = b""

    # タイムアウト値を２秒に設定
    connection.settimeout(timeout)

    try:
        # データを受け取らなくなるかタイムアウトになるまでデータを受信してbufferに格納
        while True:
            data = connection.recv(4096)

            if not data:
                break

            buffer += data
    except:
        pass

    return buffer


# リモート側のホストに送る全リクエストデータの改変
def request_handler(buffer):
    # パケットの改変を実施
    return buffer


def response_handler(buffer):
    # パケットの改変を実施
    return buffer


def main():

    # オプションパース
    parser = argparse.ArgumentParser(description="BHP TCP Proxy")
    parser.add_argument('localhost', type=str)
    parser.add_argument('localport', type=int)
    parser.add_argument('remotehost', type=str)
    parser.add_argument('remoteport', type=int)
    parser.add_argument('-rf', '--receive-first', action='store_true')
    parser.add_argument('-t', '--timeout', type=int, default=2)
    args = parser.parse_args()

    global timeout
    timeout = args.timeout

    if len(sys.argv[1:]) == 0:
        parser.print_usage()

    server_loop(args.localhost, args.localport, args.remotehost, args.remoteport, args.receive_first)


if __name__ == '__main__':
    main()
