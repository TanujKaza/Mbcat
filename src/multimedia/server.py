import socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind(("", 5006))
server_socket.listen(5)
import json
from PIL import Image

SIZE = 40000000

client_socket, address = server_socket.accept()
while (1):
    file_name = client_socket.recv(1024).decode()
    data = client_socket.recv(SIZE)

    newFileByteArray = bytearray(data)
   
    transfer_file = "transfer"
    for i in range(1,len(file_name.split("."))):
        transfer_file = transfer_file + "." + file_name.split(".")[i]

    if transfer_file != "transfer":
        newFile = open(transfer_file, "wb")
        newFile.write(newFileByteArray)



       