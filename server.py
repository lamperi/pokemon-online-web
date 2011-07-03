from twisted.internet.protocol import Protocol, Factory
from twisted.web import resource
from twisted.web.static import File
from twisted.internet.endpoints import TCP4ClientEndpoint
from twisted.protocols.basic import Int16StringReceiver
from twisted.internet import reactor
from twisted.internet.defer import Deferred

from websocket import WebSocketHandler, WebSocketSite

from struct import pack, unpack
from json import loads, dumps
from hashlib import md5

from poprotocol import POProtocol, RegistryProtocol
from teamloader import loadTeam

class Registry(RegistryProtocol):

    def __init__(self):
        RegistryProtocol.__init__(self)
        self.servers = []
        self.deferred = Deferred()

    def onPlayersList(self, name, desc, numplayers, ip, maxplayers, port):
        self.servers.append([name, desc, numplayers, ip, maxplayers, port])

    def onServerListEnd(self):
        self.deferred.callback(self.servers)

class Receiver(POProtocol):

    def __init__(self):
        POProtocol.__init__(self)
        self.client = None

    # Helpers

    def serializePlayer(self, playerInfo):
        player = { 'id': playerInfo.id, 'name': playerInfo.name, 'info': playerInfo.info, 
                   'auth': playerInfo.auth, 'flags': playerInfo.flags, 
                   'rating': playerInfo.rating, 'avatar': playerInfo.avatar,
                   'tier': playerInfo.tier, 'color': playerInfo.color.__dict__,
                   'gen': playerInfo.gen, 'pokemon': [uid.__dict__ for uid in playerInfo.pokemon]}
        return player

    # PO Events

    def onServerName(self, name):
        self.client.sendObject({'type': 'ServerName', 'name': name})
    
    def onVersionControl(self, version):
        self.client.sendObject({'type': 'VersionControl', 'version': version})

    def onRegister(self):
        self.client.sendObject({'type': 'Register'})

    def onAskForPass(self, salt):
        self.client.sendObject({'type': 'AskForPass', 'salt': salt})

    def onAnnouncement(self, announcement):
        self.client.sendObject({'type': 'Announcement', 'announcement': announcement})

    def onLogin(self, playerInfo):
        player = self.serializePlayer(playerInfo)
        self.client.sendObject({'type': 'Login', 'player': player})

    def onLogout(self, id):
        self.client.sendObject({'type': 'Logout', 'playerId': id})

    def onTierSelection(self, tiers):
        self.client.sendObject({'type': 'TierSelection', 'tiers': tiers})

    def onChannelsList(self, channels):
        self.client.sendObject({'type': 'ChannelsList', 'channels': channels})

    def onPlayersList(self, playerInfo):
        player = self.serializePlayer(playerInfo)
        self.client.sendObject({'type': 'PlayersList', 'player': player})

    def onPlayerBan(self, playerId, srcId):
        self.client.sendObject({'type': 'PlayerBan', 'playerId': playerId, 'srcId': srcId})

    def onPlayerKick(self, playerId, srcId):
        self.client.sendObject({'type': 'PlayerKick', 'playerId': playerId, 'srcId': srcId})

    def onSendTeam(self, playerInfo):
        player = self.serializePlayer(playerInfo)
        self.client.sendObject({'type': 'SendTeam', 'player': player})

    def onChallengeStuff(self, challengeInfo):
        info = { 'dsc': challengeInfo.dsc, 'opp': challengeInfo.opp,
                          'clauses': challengeInfo.clauses, 'mode': challengeInfo.mode} 
        self.client.sendObject({'type': 'SendTeam', 'challengeInfo': info})

    def onEngageBattle(self, battleid, player1, player2, battleConf, teamBattle):
        if player1 == 0:
            self.client.sendObject({'type': 'EngageBattle', 'battleId': battleid, 
                                    'playerId1': player1, 'playerId2': player2,
                                    'battleConf': None, 'teamBattle': None})

        else:
            self.client.sendObject({'type': 'EngageBattle', 'battleId': battleid, 
                                    'playerId1': player1, 'playerId2': player2})

    def onBattleFinished(self, battleid, outcome, winner, loser):
        self.client.sendObject({'type': 'BattleFinished', 'battleId': battleid,
                                'outcome': outcome, 'winner': winner, 'loser': loser})

    def onChannelPlayers(self, chanid, playerlist):
        self.client.sendObject({'type': 'ChannelPlayers', 'chanId': chanid, 'playerList': playerlist})

    def onJoinChannel(self, chanid, playerid):
        self.client.sendObject({'type': 'JoinChannel', 'chanId': chanid, 'playerId': playerid})

    def onLeaveChannel(self, chanid, playerid):
        self.client.sendObject({'type': 'LeaveChannel', 'chanId': chanid, 'playerId': playerid})

    def onChannelBattle(self, chanid, battleid, player1, player2):
        self.client.sendObject({'type': 'ChannelBattle', 'chanId': chanid, 'battleId': battleid, 
                                'player1': player1, 'player2': player2})

    def onChannelMessage(self, chanid, user, message):
        self.client.sendObject({'type': 'ChannelMessage', 'chanId': chanid, 'user': user, 'message': message})

    def onRemoveChannel(self, chanid):
        self.client.sendObject({'type': 'RemoveChannel', 'chanId': chanid})

    def onAddChannel(self, chanid, channame):
        self.client.sendObject({'type': 'AddChannel', 'chanId': chanid, 'chanName': channame})

    def onSendPM(self, playerid, message):
        self.client.sendObject({'type': 'SendPM', 'playerId': playerid, 'message': message})

    def onAway(self, playerid, isAway):
        self.client.sendObject({'type': 'Away', 'playerId': playerid, 'isAway': isAway})

    def onSendMessage(self, user, message):
        self.client.sendObject({'type': 'SendMessage', 'user': user, 'message': message})

    def onHtmlMessage(self, message):
        self.client.sendObject({'type': 'HtmlMessage', 'message': message})
        
    # Other Events

    def connectionLost(self, reason):
        if self.client:
            self.client.sendObject({'type': 'Disconnected', 'reason': str(reason)})
            self.client = None

class POhandler(WebSocketHandler):
    def __init__(self, transport):
        WebSocketHandler.__init__(self, transport)
        self.proxy = None
        self.pending = []

    def __del__(self):
        print 'Deleting handler'

    def connectionMade(self):
        print 'Connected to client.'
        factory = Factory()
        factory.protocol = Registry
        point = TCP4ClientEndpoint(reactor, "pokemon-online.dynalias.net", 5081)
        d = point.connect(factory)


        def gotRegistry(registry):
            def gotServerList(servers):
                self.sendObject({'type': 'ServerList', 'servers': servers})
                registry.transport.loseConnection()
            registry.deferred.addCallback(gotServerList)

        d.addCallback(gotRegistry)
        d.addErrback(self.cantConnect)

    def frameReceived(self, frame):
        json = loads(frame)
        if not json.has_key("type"):
            return

        if json["type"] == "Connect":
            ip = json.get("ip", None)
            port = json.get("port", None)
            if ip and port:
                self.createProxyConnection(ip, port)
                return

        if not self.proxy:
            self.pending.append(frame)
            return

        try:
            method = "on{0}".format(json["type"])
            print method
            if hasattr(self, method):
                getattr(self, method)(json)
            else:
                print "Unknown event"
        except Exception as e:
            print "Error handling in JSON event: {0}".format(json.get("type"), "UnknownEvent")
            print "{0}: {1}".format(e.__class__.__name__, e) 
            
    def sendObject(self, o):
        print dumps(o)
        self.transport.write(dumps(o))

    def createProxyConnection(self, ip, port):
        factory = Factory()
        factory.protocol = Receiver
        point = TCP4ClientEndpoint(reactor, ip, port)
        d = point.connect(factory)
        d.addCallback(self.gotProxy)
        d.addErrback(self.cantConnect)

    def connectionLost(self, reason):
        print 'Lost connection.'
        if self.proxy:
            self.proxy.transport.loseConnection()
        self.proxy = None

    def gotProxy(self, proxy):
        print "Connected!"
        self.proxy = proxy
        proxy.client = self
        self.proxy.setProxyIP("127.0.0.1")
        for p in self.pending:
            self.frameReceived(p)

    def cantConnect(self, msg):
        print 'Can\'t connect: {0}'.format(msg)

    # Handing JSON Events from Websocket client
    def onLogin(self, json):
        print "Tries to login!"
        info = loadTeam()
        info.team.nick = json['name']
        self.proxy.login(info)

    def onChannelMessage(self, json):
        self.proxy.sendChannelMessage(json['chanId'], json['message'])

    def onJoinChannel(self, json):
        self.proxy.joinChannel(json['chanName'])

    def onLeaveChannel(self, json):
        self.proxy.partChannel(json['chanId'])

    def onRegister(self, json):
        self.proxy.register()

    def onAskForPass(self, json):
        pw = json["password"]
        salt = json["salt"]
        s = md5(md5(pw.decode("utf-8").encode("iso-8859-1", "ignore")).hexdigest() + salt.encode("iso-8859-1", "ignore")).hexdigest()
        u = s.decode("iso-8859-1")
        self.proxy.askForPass(u)

    def onSendPM(self, json):
        self.proxy.sendPM(json['playerId'], json['message'])



class FlashSocketPolicy(Protocol):
    """ A simple Flash socket policy server.
    See: http://www.adobe.com/devnet/flashplayer/articles/socket_policy_files.html
    """
    def connectionMade(self):
        policy = '<?xml version="1.0"?><!DOCTYPE cross-domain-policy SYSTEM ' \
                 '"http://www.macromedia.com/xml/dtds/cross-domain-policy.dtd">' \
                 '<cross-domain-policy><allow-access-from domain="*" to-ports="*" /></cross-domain-policy>'
        self.transport.write(policy)
        self.transport.loseConnection()



if __name__ == "__main__":
    # run our websocket server
    # serve index.html from the local directory
    root = File('.')
    site = WebSocketSite(root)
    site.addHandler('/test', POhandler)
    reactor.listenTCP(8080, site)
    # run policy file server
    #factory = Factory()
    #factory.protocol = FlashSocketPolicy
    #reactor.listenTCP(843, factory)
    reactor.run()

