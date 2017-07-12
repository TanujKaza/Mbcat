import socket,os
import json
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(("", 5006))

while(1):
    file_name = input("Enter File Name:")
    client_socket.send(file_name.encode())

    file = open(file_name,"rb")
    file_data = file.read()
    file.close()
    client_socket.send(file_data)
    print(len(file_data))


