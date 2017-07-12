import sys
import socket
import select
import json
import getpass



def chat_client():

# -----------  check for  proper arguments and assign host address as first argument and port number as second-------------------
    if(len(sys.argv) < 3) :
        print('Usage : python client.py hostname port')
        sys.exit()

    host = sys.argv[1]
    port = int(sys.argv[2])
     
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print(type(s))
    s.settimeout(2)
     
    # ------------------- connect to remote host and on fail send a message and exit--------------
    try :
        s.connect((host, port))
    except :
        print ('Unable to connect')
        sys.exit()


#  ---------------------------------  Authentication after connection to host--------------------------------------

    print('Connected to Remote Host. Authenticate your Credentials')
    username=input('Enter LDAP Username -> ')
    password = getpass.getpass('Enter LDAP Password -> ')
    # password=input('Enter Password -> ')

    msg = {"username" : username, "password" : password, "action" : "authentication"}
    msg = json.dumps(msg) 
    s.send(msg.encode())

    # the data is converted to json format so that it can be sent over the TCP socket otherwise it will give error.





    data = s.recv(4096)  # the maximum data size that it can recieve --------
                         # if data is not there print error and exit   

    if not data :
        print('\nDisconnected from chat server')
        sys.exit()
    data=data.decode()


# -------- Till the time you are not authenticated try again --------------------------------

    while(data!='Authenticated'):
        print("Incorrect credentials. Try again")
        username=input('Enter LDAP id -> ')
        password = getpass.getpass('Enter LDAP Password -> ')
        # password=input('Enter password -> ')

        msg = {"username" : username, "password" : password, "action" : "authentication"}
        msg = json.dumps(msg) #convverting the data into json format so that it can be sent over the TCP socket otherwise it will give error.
        s.send(msg.encode())

        data = s.recv(4096)
        if not data :
            print('\nDisconnected from chat server')
            sys.exit()
        data=data.decode()

    print("You are authenticated. You can begin to chat!")

# ---------- once authenticated make action to main screen and send it to server -------------------------


    msg={"action":"main screen"}
    msg = json.dumps(msg)
    s.send(msg.encode())


# ----------- server responds by giving the message instructions ----------

    data = s.recv(4096)
    if not data :
        print('\nDisconnected from chat server')
        sys.exit()
    data=data.decode()
    print(data)

    sys.stdout.write('--> '); sys.stdout.flush()



    user_list=[]
    group_list=[]
    flag_user_group=-1

    # -----list of users and groups to which we are sending and flag is for checking whether the message that we are sennding is for a particular group-------------------------------------------------


    while 1:
        socket_list = [sys.stdin, s]

        # --- this is a list of 2 elements containing socket of text over terminal and scoket which is opened over the server for this particular client ---------

        # Get the list sockets which are readable

        # so we are using select because
        # -  it helps in giving a list of socket which are sending data to us ---
        # from this list of data we select the socket which is ran over the server 
        # to send and recieve message

        ready_to_read,ready_to_write,in_error = select.select(socket_list , [], [])
         
        for sock in ready_to_read:             
            if sock == s:
                # incoming message from remote server, s
                data = sock.recv(4096)
                if not data :
                    print('\nDisconnected from chat server')
                    sys.exit()
                else :

    #  --- recieved data from the socket and writing it ------------
                    sys.stdout.write(data.decode())
                    sys.stdout.write('--> '); sys.stdout.flush()     
            
            else :

                # user entered a message
                msg = sys.stdin.readline()
                """Message should be read from the terminal using readline function as given above.
                   It is stored in message and then checked for matching strings. 
                   [:x] represents how many letters we are checking
                """
               
                if msg[:10]=="<--exit-->":
                    flag_user_group=-1
                    msg = {"action":"exit","username":username}
                    msg = json.dumps(msg)
                    s.send(msg.encode())
                    data = s.recv(4096)
                    data = data.decode()
                    if not data :
                        print('\nDisconnected from chat server')
                        sys.exit()
                    if(data != "Done"):
                        print("[error] Please try again")
                    else:
                        print("Ok")
                       
                        sys.exit()
                elif msg[:10] == "<--help-->":
                    print("               <--help--> ")
                    print(" ")
                    print("Send message to user or multiple users at once- ")
                    print("    <--send-to-users--> (usernames seperated by space) ")
                    print("Send message to group or multiple groups at once -")
                    print("    <--send-to-groups--> (groupnames seperated by space) ")
                    print("Create groups or multiple groups at once ")
                    print("    <--create-group--> (groupnames seperated by space)")
                    print("Add multiple users to a group")
                    print("    <--add-users-to-group--> (groupname) (usernames seperated by space)")
                    print("To leave multiple groups ")
                    print("    <--leave-group--> (groupnames seperated by space)")
                    print("To see a specific number of the most recent messages from a particular user")
                    print("    <--show-messages-user--> (number of messages) (username)")
                    print("To see a specific number of the most recent messages from a particular group")
                    print("    <--show-messages-group--> (number of messages) (groupname)")
                    print("Shows the list of users present in the list of groups the said user is present in")
                    print("    <--show-all-groups-->")
                    print("Shows the number of users who are online and present in the group in question")
                    print("    <--show-specific-group--> (groupnames seperated by space)")
                    print("To show whether other users of the application is online or not ")
                    print("    <--show-all-users--> ")
                    print("In ‘<--show-specific-group--> ‘ if the user is present in two groups of the same name, the user enters a specific number")
                    print("    <--show-specific-group_id--> (group_id number)")
                    print("Block users (These users cannot talk to you but you can send to them if they have not blocked you")
                    print("    <--block-users--> (usernames seperated by space) ")
                    print("Unblock users")
                    print("    <--block-users--> (usernames seperated by space) ")
                elif msg[:17]=="<--main-screen-->":

                    flag_user_group=-1
                    msg={"action":"main screen"}
                    msg = json.dumps(msg) #converting the data into json format so that it can be sent over the TCP socket otherwise it will give error.
                    s.send(msg.encode())

#  check all these numbers for overflow eg. if user does not enter anything after the command and we are taking a list input

                elif msg[:19]=="<--send-to-users-->":
                    #All the messages after this command will be sent to the users entered here.
                    flag_user_group=0# This is the state in which message will be sent to the server which will forward it to the users
                    user_list=msg[20:].split()
                    # print(user_list)
                    if not user_list:
                        print("Please specify the user names to which you want to send the message\n")


                elif msg[:20]=="<--send-to-groups-->":
                    #All the messages after this command will be sent to the groups entered here.
                    flag_user_group=1 #
                    group_list=msg[21:].split()

                    if not group_list:
                        print("Please specify the group names to which you want to send the message\n")

                elif msg[:24]=="<--add-users-to-group-->":
                    # Message is sent in this part to the server so flag_user_group is -1
                    flag_user_group=-1
                    l=msg[25:].split()

                    if not l:
                        print("Please specify the group name in which you want to add\n")

                    elif not l[0]:
                       print("Please specify the group name in which you want to add\n")
                    elif not l[1:]:
                        print("Please specify the user names you want to add in the group ",l[0],"\n")

                    else: 
                        # print(l)
                        msg = {"action" : "add users to group" , "group": l[0], "users" :l[1:] }
                        msg = json.dumps(msg) #Converts the msg into suitable form for sending Line 47 of server shows how to get it back in the dictionary form
                        s.send(msg.encode())
                        print("user ","add-users-to-group")
# ####################################-----------------------------------------------------------------                  
# ####################################-----------------------------------------------------------------

# till here

# ####################################-----------------------------------------------------------------
# ####################################-----------------------------------------------------------------
# ####################################-----------------------------------------------------------------

                elif msg[:18]=="<--create-group-->":
                    # Creates a new group
                    flag_user_group=-1
                    l=msg[19:].split()
                    # l contains the name of the group
                    if not l:
                        print("Please specify the group name in which you want to add\n")
                    # print(l)
                    else:
                        msg = {"action" : "create group" , "groups" :l }
                        msg = json.dumps(msg) #Converts the msg into suitable form for sending Line 47 of server shows how to get it back in the dictionary form
                        s.send(msg.encode())    
                        # print("create-group")

                elif msg[:17]=="<--leave-group-->":
                    flag_user_group=-1
                    # Get the name of the group
                    l=msg[18:].split()
                    if not l:
                        print("Please specify the group name in which you want to leave\n")
                    else:
                        msg = {"action" : "leave group" , "groups" :l }
                        msg = json.dumps(msg) #Converts the msg into suitable form for sending Line 47 of server shows how to get it back in the dictionary form
                        s.send(msg.encode())
                    
                elif msg[:25]=="<--show-messages-group-->":
                    # first enter the number of messages to be displayed and then the name of the group
                    flag_user_group=-1
                    # get the name of the group
                    l=msg[26:].split()
                    # print(l)
                    if not l:
                        print("Please specify the group name from which you want to show messages\n")
                    elif type(l[0]) != type(0):
                        print("Please enter the number of messages first and then the group name")
                    else:
                        msg = {"action" : "show messages group" , "number" :l[0],"group": l[1]}
                        msg = json.dumps(msg) #Converts the msg into suitable form for sending Line 47 of server shows how to get it back in the dictionary form
                        s.send(msg.encode())
                        # print("show-messages-group")

                elif msg[:24]=="<--show-messages-user-->":
                    # first enter the number of messages to be displayed and then the name of the group
                    flag_user_group=-1
                    #get the number of messages to be displayed and the name of the user
                    l=msg[25:].split()
                    # print(l)
                    if not l:
                        print("Please specify the group name from which you want to show messages\n")
                    elif type(l[0]) != type(0):
                        print("Please enter the number of messages first and then the group name")
                    else:
                        msg = {"action" : "show messages user" , "number" :l[0],"user": l[1]}
                        msg = json.dumps(msg) #Converts the msg into suitable form for sending Line 47 of server shows how to get it back in the dictionary form
                        s.send(msg.encode())
                        # print("show-messages-user")

                elif msg[:21] == "<--show-all-groups-->":
                    # Gets information about all the groups and their members
                    flag_user_group = -1
                    msg = {"action":"show-all-groups","username":username}
                    msg = json.dumps(msg)
                    s.send(msg.encode())
                    print("show-all-groups")

                elif msg[:25] == "<--show-specific-group-->":
                     # Gets the information about how many members are online in this group
                    flag_user_group = -1
                    # Get the group name
                    l = msg[26:].split()
                    msg = {"action":"show-specific-groups","group_name":l}
                    msg = json.dumps(msg)
                    s.send(msg.encode())
                    print("show-specific-groups")

                elif msg[:20] == "<--show-all-users-->":
                    # Gets the information about which users are online now
                    flag_user_group = -1
                    msg = {"action":"show-all-users","username":username}
                    msg = json.dumps(msg)
                    s.send(msg.encode())    
                    print("show-all-users") 

                elif msg[:28] == "<--show-specific-group_id-->":
                    flag_user_group = -1
                    l = msg[29:].split()
                    msg = {"action":"show-specific-group_id","group_id":l,"username":username}
                    msg = json.dumps(msg) 
                    s.send(msg.encode())
                    print("show-specific-group_id") 

                elif msg[:30] == "<--send-multimedia-to-users-->":
                    #For sending files over the server
                    flag_user_group = 2
                    user_list = msg[31:].split()
                    print(user_list)
                    print("send-multimedia-to-users")

                elif msg[:17] == "<--block-users-->":
                    # Prevent the user from sending messages to us
                    flag_user_group = -1
                    l = msg[17:].split()
                    msg = {"action" : "block-users" , "users": l}
                    msg = json.dumps(msg) 
                    s.send(msg.encode())
                    print("block-user")

                elif msg[:19] == "<--unblock-users-->":
                    flag_user_group = -1
                    l = msg[19:].split()
                    msg = {"action" : "unblock-users" , "users": l}
                    msg = json.dumps(msg) 
                    s.send(msg.encode())
                    print("unblock-user")

                elif flag_user_group==0:
                    message = {"action" : "send to users" , "users" :user_list, "message":msg}
                    message = json.dumps(message)
                    s.send(message.encode())

                elif flag_user_group==1:
                    message = {"action" : "send to groups" , "groups" :group_list, "message":msg}
                    message = json.dumps(message) #Converts the msg into suitable form for sending Line 47 of server shows how to get it back in the dictionary form
                    s.send(message.encode())

                elif flag_user_group == 2:
                    print("sending multimedia")
                    file = open(msg.strip().split('\n')[0],"rb")
                    file_data = file.read()
                    file.close()
                    message = {"action" : "send-multimedia-to-users" , "users" :user_list, "message":msg, "file":file_data}
                    s.send(message)

                else:
                    print("wrong input try again")


                sys.stdout.write('--> '); sys.stdout.flush() 
                """Whenever you enter some data into the terminal enters this else case because at that 
                time sys.stdin changes
                """
if __name__ == "__main__":
    sys.exit(chat_client())

