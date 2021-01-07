import asyncio
import websockets
import json

class ClientList:
    def __init__(self):
        self.clients = set()
        self.score = 0

    def addOneScore(self):
        self.score += 1
    
    def resetScore(self):
        self.score = 0

    def getScore(self):
        return self.score

    async def addClient(self, websocket):
        self.clients.add(self.Client(websocket))
        print(f'[Client] New client connected! Address: {websocket.remote_address}')
        await self.sendUpdateToSpectate()

    async def removeClient(self, websocket):
        for client in self.clients:
            if client.getWebsocket() == websocket:
                self.clients.remove(client)
                print(f'[Client] A client disconnected! Address: {websocket.remote_address}')
                await self.sendUpdateToSpectate()
                return True
        print('[ERROR] Client to be removed not found!')
        return False

    def getNumOfClients(self):
        return sum(1 for client in self.clients)

    def getClientWebsocketSet(self):
        result = set()
        for client in self.clients:
            result.add(client.getWebsocket())
        return result

    def isAllHit(self):
        #print (f'[Client] Number of clients: {self.getNumOfClients()}')
        for client in self.clients:
            if client.getIsHit() == False and client.getIsSpectate() == False:
                #print(f'[Client] One client is not hit! Address: {client.getWebsocket().remote_address}')
                return False
        print('[Client] All clients are knocked down!')
        return True

    async def setIsHitBySocket(self, websocket, flag):
        for client in self.clients:
            if client.getWebsocket() == websocket:
                client.setIsHit(flag)
                #print(f'[Client] A client is set to hit! Address: {client.getWebsocket().remote_address}')
                await self.sendUpdateToSpectate()
                return True
        print('[ERROR] Client set to hit not found!')
        return False

    async def setIsSpectateBySocket(self, websocket, flag):
        for client in self.clients:
            if client.getWebsocket() == websocket:
                client.setIsSpectate(flag)
                print(f'[Client] A client is set to spectate! Address: {client.getWebsocket().remote_address}')
                await self.sendUpdateToSpectate()
                return True
        print('[ERROR] Client set to spectate not found!')
        return False

    async def resetAllToFalse(self):
        for client in self.clients:
            client.setIsHit(False)
        await self.sendUpdateToSpectate()
        print("[Reset] All clients reset hit!")

    async def sendToClient(self, websocket, message):
        await websocket.send(message)
        #print(f'Sent "{message}" to client: {websocket.remote_address}')

    async def sendToAll(self, message):
        socketList = self.getClientWebsocketSet()
        #print (f'Number of clients: {self.getNumOfClients()}')
        for socket in socketList:
            #await socket.send(f'Message from {websocket.remote_address}: {message}')
            #await socket.send(json.dumps(websocket.remote_address))
            await socket.send(message)
            #print(f'Sent "{message}" to client: {socket.remote_address}')

    async def sendToAllExcept(self, websocket, message):
        socketList = self.getClientWebsocketSet()
        for socket in socketList:
            if socket != websocket:
                await socket.send(f'Message from {websocket.remote_address}: {message}')
                #await socket.send(json.dumps(websocket.remote_address))

    async def sendUpdateToSpectate(self):
        result = []
        for client in self.clients:
            temp = {
                'address': f'{client.getWebsocket().remote_address[0]}:{client.getWebsocket().remote_address[1]}',
                'isHit': client.getIsHit(),
                'isSpectate': client.getIsSpectate()
            }
            result.append(temp)
        result = sorted(result, key=lambda k: k['address'])

        result.append({'score': self.getScore()})

        tempJson = json.dumps(result)
        for client in self.clients:
            if client.getIsSpectate() == True:
                await client.getWebsocket().send(tempJson)

    class Client:
        def __init__(self, websocket):
            self.websocket = websocket
            self.isHit = False
            self.isSpectate = False

        def getIsHit(self):
            return self.isHit

        def getIsSpectate(self):
            return self.isSpectate

        def setIsHit(self, flag):
            self.isHit = flag

        def setIsSpectate(self, flag):
            self.isSpectate = flag

        def getWebsocket(self):
            return self.websocket

CList = ClientList()

async def server(websocket, path):
    # Register.
    await CList.addClient(websocket)
    try:
        async for message in websocket:
            print(f'[Message] Received msg from {websocket.remote_address}: {message}')
            #print(f'[Test] isMsgEqualHit: {message == "Hit!"}')
            if message == 'Hit!':
                CList.addOneScore()
                await CList.setIsHitBySocket(websocket, True)
                #print(CList.setIsHitBySocket(websocket, True))
                #print(f'[Test] isAllHit: {CList.isAllHit()}')
                if CList.isAllHit() == True:
                    await asyncio.sleep(1)
                    await CList.sendToAll('servodown')
                    await CList.resetAllToFalse()
            
            elif message == 'spectate':
                await CList.setIsSpectateBySocket(websocket, True)
            elif message == 'reset':
                CList.resetScore()
                await CList.sendToAll('servodown')
                await CList.resetAllToFalse()
    except:
        pass
    finally:
        # Unregister on disconnect.
        await CList.removeClient(websocket)

start_server = websockets.serve(server, "192.168.1.2", 5000)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()