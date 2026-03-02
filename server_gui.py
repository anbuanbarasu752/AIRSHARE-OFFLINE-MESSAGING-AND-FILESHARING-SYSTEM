import socket
import threading

HOST = "0.0.0.0"
PORT = 5000

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen()

clients = []

print("Server started...")

def handle_client(conn):
    while True:
        try:
            data = conn.recv(4096)
            if not data:
                break

            for client in clients:
                if client != conn:
                    client.send(data)

        except:
            break

    clients.remove(conn)
    conn.close()

while True:
    conn, addr = server.accept()
    clients.append(conn)
    print("Connected:", addr)
    threading.Thread(target=handle_client, args=(conn,)).start()