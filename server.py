from vidstream import CameraClient, StreamingServer, AudioSender, AudioReceiver
import threading
import socket
import random

local_ip_address = socket.gethostbyname(socket.gethostname())
port = 9999

class User:
    def __init__(self):
        self.nickname = None
        self.client = None
        self.room = None
        self.address = None
        self.camera = False
        self.microphone = False
        self.shareScreen = False
        self.vidStream = None
        self.audStream = None
        self.userVidPort = random.randint(1000,9999)
        self.userAudPort = random.randint(1000,9999)
        self.tlVid = None
        self.tlAud = None

    def verifyNickname(self, nickname, users):
        for user in users:
            if user.nickname == nickname:
                return False
        return True

    def createUser(self, nickname, client, room, address):
        self.nickname = nickname
        self.client = client
        self.room = room
        self.address = address

    def connect(self):
        pass

    def disconnect(self):
        self.client.close()
    
    def setCamera(self):
        self.camera = not self.camera

    def setMicrophone(self):
        self.microphone = not self.microphone

    def initVidStream(self, port):
        try:
            self.tlVid = None
            self.userVidPort = port
            self.vidStream = CameraClient(local_ip_address, self.userVidPort)
            self.tlVid = threading.Thread(target = self.vidStream.start_stream)
            self.tlVid.start()
        except Exception as e:
            pass
    def stopVidSream(self):
        try:
            self.vidStream.stop_stream()
        except Exception as e:
            pass
    def initAudStream(self,port):
        try:
            self.tlAud = None
            self.userAudPort = port
            self.audStream = AudioSender(local_ip_address, self.userAudPort)
            self.tlAud = threading.Thread(target = self.audStream.start_stream)
            self.tlAud.start()
        except Exception as e:
            pass
    def stopAudStream(self):
        try:
            self.audStream.stop_stream()
        except Exception as e:
            pass    


class Room:
    def __init__(self):
        self.admin = None
        self.roomCode = None
        self.users = []
        self.vidStreams = {}
        self.audStreams = {}
        
    def verifyRoomCode(self, roomCode, rooms):
        for room in rooms:
            if room.roomCode == roomCode:
                return False
        return True

    def createMetting(self, roomCode, user):
        self.roomCode = roomCode
        self.admin = user
        self.users.append(user)
        stream = StreamingServer(local_ip_address, user.userVidPort )
        self.vidStreams[f"{user.nickname}"] = [threading.Thread(target=stream.start_server), stream]
        audio = AudioReceiver(local_ip_address, user.userAudPort)
        self.audStreams[f"{user.nickname}"] = [threading.Thread(target=audio.start_server), audio]

    def joinMetting(self, user):
        self.users.append(user)
        stream = StreamingServer(local_ip_address, user.userVidPort )
        self.vidStreams[f"{user.nickname}"] = [threading.Thread(target=stream.start_server), stream]
        audio = AudioReceiver(local_ip_address, user.userAudPort)
        self.audStreams[f"{user.nickname}"] = [threading.Thread(target=audio.start_server), audio]

    def leftMetting(self, user):
        self.users.remove(user)

    def initVidStream(self, nickname):
        try:
            self.vidStreams[nickname][0].start()
        except Exception as e:
            pass
    def initAudStream(self, nickname):
        try:
            self.audStreams[nickname][0].start()
        except Exception as e:
            pass        
    def stopVidStream(self, user):
        try:
            self.vidStreams[user.nickname][1].stop_server()
            stream = StreamingServer(local_ip_address, user.userVidPort )
            self.vidStreams[f"{user.nickname}"] = [threading.Thread(target=stream.start_server), stream]
        except Exception as e:
            pass
    def stopAudStream(self, user):
        try:
            self.audStreams[user.nickname][1].stop_server()
            audio = AudioReceiver(local_ip_address, user.userAudPort)
            self.audStreams[f"{user.nickname}"] = [threading.Thread(target=audio.start_server), audio]
        except Exception as e:
            pass


class Server:
    def __init__(self, host, port):
        self.host_ip = host
        self.port = port
        self.clients = []
        self.rooms = []
        self.server = self.startserver()
        self.thread = None

    def startserver(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((self.host_ip, self.port))
        server.listen()
        return server

    def broadcast(self, roomCode, message):
        for room in self.rooms:
            if room.roomCode == roomCode:
                for user in room.users:
                    user.client.send(message)

    def leftMetting(self, roomCode, user):
        for room in self.rooms:
            if room.roomCode == roomCode:
                room.leftMetting(user)
                self.clients.remove(user)
                break

    def getUsers(self, roomCode):
        users = f"RoomCode: {roomCode} => "
        for room in self.rooms:
            if room.roomCode == roomCode:
                for user in room.users:
                    users += f"{user.nickname}, "
                break
        return users

    def getRoom(self, roomCode):
        room = None
        for room in self.rooms:
            if room.roomCode == roomCode:
                room = room
                break
        return room

    def handle(self, user, roomCode):
        while True:
            try:
                userID = self.clients.index(user)
                user = self.clients[userID]
                room = self.getRoom(roomCode)
                if room == None:
                    raise ValueError("Unexpected error vid stream")
                message = user.client.recv(1024)
                message = message.decode("UTF-8")
                if (message) == "_EXIT":
                    message = f"{user.nickname} has left the room".encode(
                        "ascii")
                    self.leftMetting(roomCode, user)
                    self.broadcast(roomCode, message)
                elif message == "_USERS":
                    message = self.getUsers(roomCode).encode("ascii")
                    self.broadcast(roomCode, message)
                elif "_CAMERA_ON" in message:
                    #room.initVidStream(user.nickname)
                    port = ""
                    startLoad = False
                    for ch in message:
                        if startLoad:
                            port = port + ch
                        if ch == "$":
                            startLoad = True
                    port = int(port)
                    user.initVidStream(port)
                elif message == "_CAMERA_OFF":
                    user.stopVidSream()
                    user.client.send("_CAMERA_OFF_OK".encode("ascii"))
                elif  "_MICROPHONE_ON" in message:
                    #room.initAudStream(user.nickname)
                    port = ""
                    startLoad = False
                    for ch in message:
                        if startLoad:
                            port = port + ch
                        if ch == "$":
                            startLoad = True
                    port = int(port)
                    user.initAudStream(port)
                elif message == "_MICROPHONE_OFF" :
                    user.stopAudStream()
                    user.client.send("_MICROPHONE_OFF_OK".encode("ascii"))
                    #room.stopAudStream(user)
                else:
                    message = message.encode("ascii")
                    self.broadcast(roomCode, message)
            except Exception as e:
                try:
                    user.disconnect()
                    self.clients.remove(user)
                    self.leftMetting(roomCode, user)
                except:
                    pass
                finally:
                    break

    def receive(self):
        while True:
            client, address = self.server.accept()
            print(f"Connected with {str(address)}")
            client.send("_NICKNAME".encode("ascii"))
            nickname = client.recv(1024).decode("ascii")
            client.send("_ROOMCODE".encode("ascii"))
            roomcode = client.recv(1024).decode("ascii")
            user = User()
            status = user.verifyNickname(nickname, self.clients)
            if status:
                user.createUser(nickname, client, roomcode, address)
                self.clients.append(user)
                room = Room()
                status = room.verifyRoomCode(roomcode, self.rooms)
                if status:
                    room.createMetting(roomcode, user)
                    self.rooms.append(room)
                else:
                    for room in self.rooms:
                        if room.roomCode == roomcode:
                            room.joinMetting(user)
                            break
                client.send("Joined to the room".encode("ascii"))
                self.broadcast(
                    roomcode, f"{nickname} joined to the chat".encode("ascii"))
                self.thread = threading.Thread(
                    target=self.handle, args=(user, roomcode,))
                self.thread.start()
            else:
                client.send(
                    "ERROR! please choose another nickname".encode("ascii"))
                client.send("_exit")
                client.close()

    def start(self):
        self.receive()

if __name__ == '__main__':
    try:
        worker = Server(local_ip_address, port)
        print(f"Server running on {worker.host_ip} - {worker.port}")
        worker.start()
    except Exception as e:
        print("Unexpected error in the server => ", e)
