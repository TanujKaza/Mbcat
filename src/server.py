import datetime
import sys
import socket
import select
import json
import sqlite3
from ldap3 import Server, Connection, ALL

conn = sqlite3.connect('database.db')
c = conn.cursor()

c.execute("SELECT * FROM userlist")
results=c.fetchall()
for i in range(len(results)):
    c.execute('''UPDATE userlist SET online = ?, socketnumber =? WHERE rowid = ? ''',(0, 0, i))

conn.commit()

HOST = '127.0.0.1' 
SOCKET_LIST = [] 
RECV_BUFFER = 4096 
PORT = 9001

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

"""Whenever a new connection request arrives then the server accepts it and then calls the recv function.
The message that it gets has the attribute action which can be either register or authenticate for the first time.
If it is register add the user to the list of Users and if it is authenticate check the username and password from the list of Users
Also add the item to the socket_map with the entry username and the socket. This gives information which socket corresponds to which client
When the action is send message. Read the attribute receivers and if they are online then send them the message by sending the message
on their respective sockets which we can get from the database"""
def chat_server():
    server_socket.bind((HOST, PORT))
    server_socket.listen(10)
    # add server socket object to the list of readable connections
    SOCKET_LIST.append(server_socket)
    print("Chat server started on port " + str(PORT))
    while 1:
        # get the list sockets which are ready to be read through select
        ready_to_read,ready_to_write,in_error = select.select(SOCKET_LIST,[],[],0)
        for sock in ready_to_read:
            # a new connection request recieved
            if sock == server_socket: 
                sockfd, addr = server_socket.accept()
                SOCKET_LIST.append(sockfd)
                print("Client (%s, %s) connected" % addr)
                
            else:
                # process data recieved from client, 
                # try:
                # receiving data from the socket.
                data = sock.recv(RECV_BUFFER)
                c.execute("SELECT * FROM userlist ORDER BY strftime('%Y-%m-%d %H:%M:%S',lastseen) DESC")
                query=c.fetchall()
                # print(query)
                if data:
                    addr = sock.getpeername()
                    data = data.decode()
                    data = json.loads(data) #After this line data is a json object with
                    # the attribute username containing the list of receivers of the message(this is also an attribute)
                    # print(data,"dfs")
                    c.execute("SELECT username FROM userlist WHERE socketnumber = ?", (sock.fileno(),))
                    query=c.fetchall()
                    if len(query) is not 0:
                        user=query[0][0]

                    if data['action'] == "authentication":

                        s = Server("10.129.3.114", get_info=ALL)  # define an unsecure LDAP server, requesting info on DSE and schema
                        name1 = data['username']
                        dnName =  "cn=" + name1 + ",dc=cs252lab,dc=cse,dc=iitb,dc=ac,dc=in"
                        try:
                            con = Connection(s, dnName, data['password'], auto_bind=True)
                            con.bind()
                            msg='Authenticated'
                            sock.send(msg.encode())
                            #check if the user is there in the database
                            c.execute("SELECT rowid FROM userlist WHERE username = ?", (data['username'],))
                            query=c.fetchall()
                            # print(query)
                            if len(query) is 0:
                                # If user is not there in the database enter it
                                c.execute("INSERT INTO userlist VALUES (?,?,1,?)",(data['username'],datetime.datetime.now(),sock.fileno()))
                            else:
                                # else update the online status
                                c.execute('''UPDATE userlist SET online = ?, lastseen =?, socketnumber =? WHERE username = ? ''',(1, datetime.datetime.now(), sock.fileno(),data['username'] ))
                        
                        except:
                            # print ("Your username or password is incorrect.")
                            msg='error'
                            sock.send(msg.encode())
                            # print('failed')
                    if data['action'] == 'exit':
                        c.execute('''UPDATE userlist SET online = ?, lastseen =?, socketnumber =? WHERE username = ? ''',(0, datetime.datetime.now(),None,data['username'] ))
                        print("Exit")
                        msg = "Done"
                        sock.send(msg.encode())
                    if data['action']== 'main screen':
                        #Shows the messages received by the user when he was offline and info about how to get help
                        # print('main screen')
                        msg='Type <--help--> for help\n'
                        sock.send(msg.encode())
                        # Get the messages which were not seen by the user
                        c.execute("SELECT * FROM messagelist WHERE username = ? and seen=? ORDER BY strftime('%Y-%m-%d %H:%M:%S',sentTime) ASC", (user,0))
                        query=c.fetchall()
                        msg=''
                        # if there are some messages then concatenate them
                        if len(query)!=0:
                            msg=msg+'Your Previous messages are - \n'
                        #for each message convert it into proper format
                        for i in query:
                            time=i[4]
                            time_object=datetime.datetime.strptime(i[4],"%Y-%m-%d %H:%M:%S.%f")
                            if time_object.strftime("%m %d")==datetime.datetime.now().strftime("%m %d"):
                                time=time_object.strftime("%H:%M:%S")
                            else:
                                time=time_object.strftime("%m %d")

                            if i[3]=='':
                                msg=msg+'[M] - ['+i[2]+'] - '+time+'\n'
                            else:    
                                msg=msg+'[M] - ['+i[3]+'] - ['+i[2]+'] - '+time+'\n'
                            msg=msg+i[5]

                        sock.send(msg.encode())
                        #update the seen status of the messages
                        c.execute("UPDATE messagelist SET seen=? WHERE seen=?", (1,0))
                        conn.commit()

                    if data['action']== 'send to users':
                        # print('send to users')
                        sendusers(user,data['users'],data['message'])

                    if data['action']== 'send to groups':
                        print('send to groups')
                        sendgroups(user,data['groups'],data['message'])
                        
                    if data['action']== 'leave group':
                        print('leave group')
                        # Leave the group
                        msg=''
                        for g in data['groups']:
                            # This contains the name of all the groups which the user wants to leave
                            # Get the group Id of all the groups which the user wants to leave
                            c.execute("SELECT rowid FROM grouplist WHERE groupname = ?", (g,))
                            q=c.fetchall()
                            query=[]
                            for j in q:
                                query.append(j[0])

                            # print("query ",query)
                            # Check if the user is a part of those groups
                            user_group_list=[]
                            for i in query:
                                c.execute("SELECT rowid FROM group_user WHERE user_id=? and group_id = ?", (user,i))
                                rowid=c.fetchall()
                                if len(rowid)!=0:
                                    user_group_list.append(i)

                            if len(user_group_list)==0:
                                msg=msg+'The user does not belong to group '+ g+'\n'
                            elif len(user_group_list)==1:
                                c.execute("DELETE FROM group_user WHERE user_id = ? and group_id= ?", (user,user_group_list[0]))
                            else:
                                msg=msg+'There are more than one ocurrance of '+g+' Choose an appropriate \n'

                        sock.send(msg.encode())

                    if data['action']== 'add users to group':
                        c.execute("SELECT rowid FROM grouplist WHERE groupname = ?", (data['group'],))
                        #Get the group id of the group
                        q=c.fetchall() 
                        # Check if the group exists
                        if(len(q) == 0):
                            msg = "Invalid Group"
                            sock.send(msg.encode())
                            
                        else: 
                            query=[]
                            ## Add the group id to the list query
                            for j in q:
                                query.append(j[0])

                            #For checking if the user if a part of this group
                            user_group_list=[]

                            for i in query:
                                #If the user is a part of that group only then append it to user_group_list
                                c.execute("SELECT rowid FROM group_user WHERE user_id=? and group_id = ?", (user,i))
                                rowid=c.fetchall()
                                if len(rowid)!=0:
                                    user_group_list.append(i)

                            if len(user_group_list)==1:
                                # Send this message to the users added
                                msg='You were added to the group '+data['group']+' by '+user+'\n'
                                for i in data['users']:
                                    # Get the socket number of all the added users
                                    c.execute("SELECT socketnumber FROM userlist WHERE username = ?", (i,))
                                    sockno=c.fetchall()
                                    is_online=0
                                    s=''
                                    # check if they are online
                                    for socket in SOCKET_LIST:
                                        if sockno[0][0]==socket.fileno():
                                            s=socket
                                            is_online=1
                                            break
                                    if is_online==1:
                                        #If is online make the seen field one otherwise 0 and send the message to the added user
                                        c.execute("INSERT INTO messagelist VALUES (?,?,?,?,?,?)",(i,1,user,data['group'],datetime.datetime.now(),msg))
                                        s.send(msg.encode())
                                        c.execute("INSERT INTO group_user VALUES (?,?,?)",(i,user_group_list[0],0))
                                    else:
                                        #Add this to the message list
                                        c.execute("INSERT INTO messagelist VALUES (?,?,?,?,?,?)",(i,0,user,data['group'],datetime.datetime.now(),msg))
                                        c.execute("INSERT INTO group_user VALUES (?,?,?)",(i,user_group_list[0],1))

                            # send this message to the user who sent this command
                            msg='Added users to groups :\n'
                            for groups in user_group_list:
                                c.execute("SELECT groupname FROM grouplist WHERE rowid = ?", (groups,))
                                name=c.fetchall()
                                msg += name[0][0] + " "
                                msg += '\n'
                            sock.send(msg.encode())

                    if data['action']== 'create group':
                        # print('create group')
                        for i in data['groups']:
                            # Insert the group name into the database
                            c.execute("INSERT INTO grouplist VALUES (?)", (i,))
                            # q=c.lastrowid
                            # print("rowid of inserted",q)
                            #Insert the user into the members of the group
                            c.execute("INSERT INTO group_user VALUES (?,?,?)",(user,q,0))
                        # send message to the user who sent this command
                        msg='Group created successfully\n'
                        sock.send(msg.encode())

                    if data['action']== 'show messages group':
                        # sends the number of messages requested from the group
                        c.execute("SELECT * FROM messagelist WHERE username = ? and sentByGroup=? ORDER BY strftime('%Y-%m-%d %H:%M:%S',sentTime) DESC", (user,data['group']))
                        query=c.fetchall()
                        msg=''
                        # Check if there are any messages in the group
                        if len(query)!=0:
                            msg=msg+'Previous messages in group '+data['group']+' are - \n'
                        else:
                            msg=msg+'There are no messages to show\n'

                        for i in range(int(data['number'])):
                            # When number of messages demanded becomes greater than the number of messages available
                            if i>len(query)-1:
                                break
                            # Get the time stamp of the messages
                            time=query[i][4]
                            time_object=datetime.datetime.strptime(query[i][4],"%Y-%m-%d %H:%M:%S.%f")
                            #Convert into proper format the time stamp
                            if time_object.strftime("%m %d")==datetime.datetime.now().strftime("%m %d"):
                                time=time_object.strftime("%H:%M:%S")
                            else:
                                time=time_object.strftime("%m %d")

                            if query[i][3]=='':
                                # If the message does not belong to a group
                                msg=msg+'[M] - ['+query[i][2]+'] - '+time+'\n'
                            else:    
                                # Else the message belongs to a group
                                msg=msg+'[M] - ['+query[i][3]+'] - ['+query[i][2]+'] - '+time+'\n'
                            msg=msg+query[i][5]

                        sock.send(msg.encode())

                    if data['action']== 'show messages user':
                        # similar to show messages group
                        # Just shows the number of messages demanded which are sent by a specific user
                        c.execute("SELECT * FROM messagelist WHERE username = ? and sentByUser=? ORDER BY strftime('%Y-%m-%d %H:%M:%S',sentTime) DESC", (user,data['user']))
                        query=c.fetchall()
                        msg=''
                        if len(query)!=0:
                            msg=msg+'Previous messages by user '+data['user']+' are - \n'
                        else:
                            msg=msg+'There are no messages to show\n'
                        for i in range(int(data['number'])):
                            if i>len(query)-1:
                                break
                            time=query[i][4]
                            time_object=datetime.datetime.strptime(query[i][4],"%Y-%m-%d %H:%M:%S.%f")
                            if time_object.strftime("%m %d")==datetime.datetime.now().strftime("%m %d"):
                                time=time_object.strftime("%H:%M:%S")
                            else:
                                time=time_object.strftime("%m %d")

                            if query[i][3]=='':
                                msg=msg+'[M] - ['+query[i][2]+'] - '+time+'\n'
                            else:    
                                msg=msg+'[M] - ['+query[i][3]+'] - ['+query[i][2]+'] - '+time+'\n'
                            msg=msg+query[i][5]

                        sock.send(msg.encode())

                    if data['action'] == 'show-all-users':
                        # Sends the online status of all the users
                        c.execute("SELECT * from userlist")
                        query = c.fetchall()
                        msg = ""
                        # If there are no users in the database
                        if len(query) == 0:
                            msg = "There are no users to stalk\n"
                        else:
                            msg = "The following users are/were active on the chat client\n"

                            for i in range(len(query)):

                                if query[i][0] != data['username']:

                                    if query[i][2] == 1:
                                        msg = msg + query[i][0] + " is now online\n"
                                    else:
                                        time_object=datetime.datetime.strptime(query[i][1],"%Y-%m-%d %H:%M:%S.%f")
                                        if time_object.strftime("%m %d")==datetime.datetime.now().strftime("%m %d"):
                                            time=time_object.strftime("%H:%M:%S")
                                        else:
                                            time=time_object.strftime("%m %d")
                                        msg = msg + query[i][0] + " was online at " + time + "\n"

                        sock.send(msg.encode())

                    if data['action'] == 'show-all-groups':
                        # sends info about all the groups that user is a part of 
                        c.execute("SELECT group_id from group_user WHERE user_id = ?",(data['username'],))
                        query = c.fetchall()
                        msg = ""
                        # check if the user is a part of any group
                        if len(query) == 0:
                            msg = "You are not a part of any group\n"
                        else:
                            for i in range(len(query)):
                                c.execute("SELECT user_id from group_user WHERE group_id = ?",(query[i][0],))
                                # Get all the users of the group
                                query1 = c.fetchall() 
                                c.execute("SELECT groupname from grouplist WHERE rowid = ?",(query[i][0],))
                                # Get all the group names
                                query2 = c.fetchall()

                                if len(query1) == 1:
                                    msg = msg + "Only you are part of the group "+ query2[0][0] + "\n"
                                else:
                                    msg = msg + "The following members are part of the group " + query2[0][0] + "\n"

                                    for j in range(len(query1)):
                                        if query1[j][0] != data['username']:
                                            msg = msg + query1[j][0] + "\n"

                        sock.send(msg.encode())

                    if data['action'] == 'show-specific-groups':
                        # Get the group name requested
                        c.execute("SELECT rowid from grouplist WHERE groupname = ?",(data['group_name'][0],))
                        query = c.fetchall()
                        msg = ""
                        # check if the user is a part of  the group
                        if len(query) == 0:
                            msg = "You are not a part of this group\n"
                        elif len(query) >= 2:
                            # If there are requests for mutiple groups
                            # Concatenate the group ids  of the group in the message
                            msg = "You are part of the following groups:\n"
                            msg = msg + "Select the group id you wish to see with the command <--show-specific-group_id--> group_id\n"
                            for i in range(len(query)):
                                c.execute("SELECT user_id from group_user WHERE group_id = ?",(query[i][0],))
                                query1 = c.fetchall()
                                msg = msg + "Group id: " + str(query[i][0]) + " and Number of users: " + str(len(query1)) + "\n"
                        else:
                            # For single group send the online status
                            c.execute("SELECT user_id from group_user WHERE group_id = ?",(query[0][0],))
                            query1 = c.fetchall()
                            count = 0
                            for i in range(len(query1)):
                                c.execute("SELECT online from userlist WHERE username = ?",(query1[i][0],))
                                query2 = c.fetchall()
                                if query2[0][0] == 1:
                                    count += 1
                            msg = "There are " + str(count) + " users online now\n"

                        sock.send(msg.encode())

                    if data['action'] == 'show-specific-group_id':
                        # Sends the number of users online in the group now 
                        c.execute("SELECT user_id from group_user WHERE group_id = ?",(data['group_id'][0],))
                        # get all the users in the group
                        query1 = c.fetchall()
                        count = 0
                        for i in range(len(query1)):
                            if query1[i][0] != data['username']:
                                c.execute("SELECT online from userlist WHERE username = ?",(query1[i][0],))
                                query2 = c.fetchall()
                                # for each user check if he is online
                                if query2[0][0] == 1:
                                    count += 1
                        if count > 0:
                            msg = "There are " + str(count) + " users online now\n"
                        else: 
                            msg = "Only you are online now\n"

                        sock.send(msg.encode())


                    if data['action'] == 'block-users':
                        # Prevents the users from sending the message to the user who request this
                        for i in data['users']:
                            # add entry to the database
                            c.execute("SELECT * FROM blocklist WHERE blockingusername = ? and blockedusername=?",(user,i))
                            query=c.fetchall();
                            # check if already blocked
                            if len(query)!=0:
                                continue
                            else:
                                c.execute("INSERT INTO blocklist VALUES (?,?)",(user,i))
                                conn.commit()

                    if data['action'] == 'unblock-users':
                        for i in data['users']:
                            c.execute("SELECT * FROM blocklist WHERE blockingusername = ? and blockedusername=?",(user,i))
                            query=c.fetchall();
                            if len(query)==0:
                                continue
                            else:
                                c.execute("DELETE FROM blocklist WHERE blockingusername = ? and blockedusername= ?", (user,i))
                                conn.commit()                        


                    conn.commit()
                   
                else:
                    # remove the socket that's broken
                    c.execute('''UPDATE userlist SET online = ?,lastseen=?, socketnumber =? WHERE socketnumber = ? ''',(0,datetime.datetime.now(), 0, sock.fileno()))
                    if sock in SOCKET_LIST:
                        SOCKET_LIST.remove(sock)
                    conn.commit()
                        
    server_socket.close()
    

def sendusers (user,userlist, message,groupname=''):
    # send the message to all the users in the user list
    # print('userlist ',userlist)
    # Get the socket number of the user
    c.execute("SELECT socketnumber FROM userlist WHERE username = ?", (user,))
    query=c.fetchall()
    usersocketno=query[0][0]

    l=[] # contains the list of the socketno of users which have not blocked the sender
    for i in userlist:
        #check if the user is blocked by any user
        c.execute("SELECT * FROM blocklist WHERE blockingusername = ? and blockedusername=?",(i,user))
        query=c.fetchall();
        if len(query)!=0:
            continue
        else:
            # Insert the message into the database
            c.execute("INSERT INTO messagelist VALUES (?,?,?,?,?,?)",(i,0,user,groupname,datetime.datetime.now(),message))
            # Get the socketnumbers of the receivers of this message
            c.execute("SELECT socketnumber FROM userlist WHERE username = ?", (i,))
            sockno=c.fetchall()
            if len(sockno)!=0 and sockno[0][0]!=0:
                l.append(sockno[0][0])
            conn.commit()
    # print(l)
    for socket in SOCKET_LIST:
        # For all the sockets check if it is in the senders list
        # send the message only to peer
        if socket != server_socket and socket.fileno() != usersocketno and socket.fileno() in l :
            try :
                msg=''
                # If the message belongs to a group or not
                if groupname!='':
                    msg='['+groupname+'] '+'['+user+' ] '+message
                else:
                    msg=' ['+user+'] '+message
                socket.send(msg.encode())
                c.execute("SELECT username FROM userlist WHERE socketnumber = ?", (socket.fileno(),))
                query=c.fetchall()
                destsocketno=query[0][0]

                c.execute('''UPDATE messagelist SET seen=? WHERE username = ? and sentByUser=? and sentByGroup=? ''',(1,destsocketno,user,groupname))
                conn.commit()
            except :
                # broken socket connection
                # print(socket)
                socket.close()
                # broken socket, remove it
                if socket in SOCKET_LIST:
                    SOCKET_LIST.remove(socket)

def sendgroups(user,grouplist,message):
    #Send the message to the groups in grouplist
    for group in grouplist:
        
        #Will contain the list of all the users
        user_list=[]

        #Get the id of all the groups
        c.execute("SELECT rowid FROM grouplist WHERE groupname = ?", (group,))
        q=c.fetchall()
        query=[]
        #convert to proper format the group id
        for j in q:
            query.append(j[0])

        # print("query ",query)
        user_group_list=[] # The list of groups of which the user is a part
        for i in query:
            c.execute("SELECT rowid FROM group_user WHERE user_id=? and group_id = ?", (user,i))
            rowid=c.fetchall()
            if len(rowid)!=0:
                user_group_list.append(i)

        if len(user_group_list)==1:
            # append users belonging to the group
            c.execute("SELECT user_id FROM group_user WHERE group_id = ?", (user_group_list[0],))
            q=c.fetchall()
            for j in q:
                if j[0] !=user:
                    user_list.append(j[0])
            #send message to the user_list
            sendusers(user,user_list,message,group)
        else:
            msg='[error] There are more than one occurances of '+group+' Choose one \n'
            # print(msg)
           
 
if __name__ == "__main__":

    sys.exit(chat_server())         
