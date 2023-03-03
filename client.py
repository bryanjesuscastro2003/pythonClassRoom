from vidstream import CameraClient, StreamingServer, AudioSender, AudioReceiver
import socket 
import threading
import os
import sys
import random

dress = socket.gethostbyname(socket.gethostname())   
port = 9999

class UserClient:
    def __init__(self, nickname, myRoom, ip, port):
        self.nickname = nickname
        self.myRoom = myRoom
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.actions = ["_EXIT", "_USERS", "_CAMERA_ON", "_CAMERA_OFF", "_MICROPHONE_ON", "_MICROPHONE_OFF", "_MENU", "_CLEAR"]
        self.tl1 = None
        self.tl2 = None
        self.tlVid = None
        self.userVidPort = random.randint(1000,9999)
        self.userAudPort = random.randint(1000,9999)
        self.stream = None
        self.vidStream = None
        self.audio = None
        self.audStream = None
        self.ipServer = ip
        self.connected = self.connect(ip, port)
        self.setClient()
        self.setStream(ip)

    def connect(self, ip, port):
        try:
            self.client.connect((ip, port))
            return True
        except Exception as e:
            return False
    
    def setStream(self, ip):
        try:
            if self.connected:
                self.stream = StreamingServer(ip, self.userVidPort )
                self.vidStream = threading.Thread(target=self.stream.start_server)  
                self.audio = AudioReceiver(ip, self.userAudPort)
                self.audStream = threading.Thread(target=self.audio.start_server)  
        except Exception as e:
            pass
    
    def initVideoStream(self):
        try:
            self.vidStream.start()
            return True
        except Exception as e:
            return False
    
    def initAudioStream(self):
        try:
            self.audStream.start()
            return True
        except  Exception as e:
            return False

    def stopVideoStream(self):
        try:
            self.stream.stop_server()
            self.stream = None
            self.vidStream = None
            self.stream = StreamingServer(self.ipServer, self.userVidPort )
            self.vidStream = threading.Thread(target=self.stream.start_server)  
            return True
        except Exception as e:
            return False
    
    def stopAudioStream(self):
        try:
            self.audio.stop_server()
            self.audio = None
            self.audStream = None
            self.audio = AudioReceiver(self.ipServer, self.userAudPort)
            self.audStream = threading.Thread(target=self.audio.start_server)  
            return True
        except Exception as e:
            return False

    def receive(self):
        while True:
            try:
                data = self.client.recv(1024).decode("ascii")
                message = str(data)
                if message == "_NICKNAME":
                    self.client.send(self.nickname.encode("ascii"))
                elif message == "_ROOMCODE":
                    self.client.send(self.myRoom.encode("ascii")) 
                elif message == "_CAMERA_OFF_OK":
                    self.stopVideoStream()
                elif message == "_MICROPHONE_OFF_OK":
                    self.stopAudioStream()
                else:
                    print(message)
            except Exception as e:
                print("An error ocurred  =>", e)
                self.client.close()
                break
    def send(self):
        for id, option in enumerate(self.actions):
            print(f"{id} _ {option}")
        while True:
            try:
                text = input("")
                data = ""
                ready = False
                if text.upper() in self.actions:
                    if text.upper() == "_MENU":
                        for id, option in enumerate(self.actions):
                            print(f"{id} _ {option}")
                        ready = False
                    elif text.upper() == "_CLEAR":
                        os.system('cls')
                        ready = False
                    elif text.upper() == "_EXIT":
                        sys.exit("Bye : )")
                    elif text.upper() == "_CAMERA_ON":
                        state = self.initVideoStream()
                        if state:
                            data = f"{text.upper()}${self.userVidPort}"
                            ready = True
                        else:
                            ready = False
                    elif text.upper() == "_MICROPHONE_ON":
                        state = self.initAudioStream()
                        if state:
                            data = f"{text.upper()}${self.userAudPort}"
                            ready = True
                        else:
                            ready = False
                    elif text.upper() in ["_CAMERA_OFF", "_MICROPHONE_OFF"] :
                        state = True#self.stopVideoStream()
                        if state:
                            data = text.upper()
                            ready = True
                        else :
                            ready = False
                    else:
                        ready = True
                        data = text.upper()
                else:
                    ready = True
                    data = f"{self.nickname} : {text}"
                if ready:
                    self.client.send(data.encode("ascii"))
            except Exception as e:
                print("An error ocurred  =>", e)
                self.client.close()
                break
    def setClient(self):
        self.tl1 = threading.Thread(target = self.receive)
        self.tl2 = threading.Thread(target = self.send)
    def startClient(self):
        try:
            if self.connected:
                self.tl1.start()
                self.tl2.start()
            else:
                raise ValueError("ERROR NO CONNECTED TO THE SERVER!")
        except Exception as e:
            print("An error ocurred  =>", e)

if __name__ == '__main__':
    nickname = input("choose a nickname : ")
    roomCode = input("roomcode: ")
    client = UserClient(nickname, roomCode, dress, port)
    client.startClient()