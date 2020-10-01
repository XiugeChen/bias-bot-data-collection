import socket
import threading
import time

# Protocol
CLOSE_CODE = "CLOSE"

# Settings
HOST = "" # use empty string to bind to all interface
PORT = 10000
PARTICIPANT = "test"


class FileWriter:
    def __init__(self, filepath):
        self.fp = open(filepath, "a")
        print("[Info] open writing file at: {}".format(filepath))
        self.fp.write("#### Gaze data point format: server_pc_time,record_computer_time,data_type,screen_x,screen_y,left_x_per,left_y_per,right_x_per,right_y_per\n")
        self.fp.write("#### Face infrared data point format: server_pc_time,record_computer_time,data_type,participant_name,face_head_tep,nose_tmp\n")

    def write_file(self, record):
        self.fp.write("{},{}\n".format(str(round(time.time() * 1000)), record))

    def close(self):
        self.fp.close()


class ClientThread(threading.Thread):
    def __init__(self, client_address, client_socket):
        threading.Thread.__init__(self)
        self.csocket = client_socket
        self.caddr = client_address
        print("[Info] New connection added: {}".format(client_address))

    def run(self):
        while True:
            data = self.csocket.recv(2048)
            msg = data.decode()

            if not msg:
                continue

            if CLOSE_CODE in msg:
                break

            file_writer.write_file(msg)

        print("[Info] Client at {} disconnected".format(self.caddr))
        self.csocket.close()


file_writer = FileWriter("./{}_{}.txt".format(PARTICIPANT, str(round(time.time() * 1000))))
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    server_address = (HOST, PORT)
    server.bind(server_address)
    print("[Info] Starting up on %s port %s" % server_address)
    print("[Info] Waiting for client request")

    while True:
        server.listen(1)
        clientsock, clientAddress = server.accept()
        newthread = ClientThread(clientAddress, clientsock)
        newthread.start()

except KeyboardInterrupt:
    print("[Info] Key board interrupt, terminate program")
    server.close()
    file_writer.close()
    print("[Info] Waiting all clients to close...")
except Exception as e:
    print("[Error]", e.__class__, "occurred.")
    server.close()
    file_writer.close()
    print("[Info] Waiting all clients to close...")
