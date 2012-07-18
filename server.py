from twisted.internet.protocol import Protocol, Factory
from twisted.web import resource
from twisted.web.server import Site
from twisted.web.static import File
from twisted.internet.endpoints import TCP4ClientEndpoint
from twisted.internet import reactor
from twisted.internet.defer import Deferred

from txsockjs.factory import SockJSFactory

from struct import pack, unpack
from json import loads, dumps
from hashlib import md5

from poprotocol.interfaces import TwistedClientProtocol, TwistedRegistryProtocol
from poprotocol import ChallengeInfo
from teamloader import loadTeam

class Registry(TwistedRegistryProtocol):

    def __init__(self):
        TwistedRegistryProtocol.__init__(self)
        self.servers = []
        self.announcement = Deferred()
        self.serverlist = Deferred()

    def onAnnouncement(self, announcement):
        self.announcement.callback(announcement)

    def onPlayersList(self, name, desc, numplayers, ip, maxplayers, port, protected):
        self.servers.append([name, desc, numplayers, ip, maxplayers, port, protected])

    def onServerListEnd(self):
        self.serverlist.callback(self.servers)

class Receiver(TwistedClientProtocol):

    def __init__(self):
        TwistedClientProtocol.__init__(self)
        self.client = None

    # Helpers

    def serializePlayer(self, playerInfo):
        player = { 'id': playerInfo.id, 'name': playerInfo.name, 'info': playerInfo.info, 
                   'auth': playerInfo.auth, 'away': playerInfo.away, 
                   'hasLadder': playerInfo.hasLadder,
                   'teams': playerInfo.teams, 'avatar': playerInfo.avatar,
                   'color': playerInfo.color.__dict__ }
        return player

    def serializeTeamBattle(self, teamBattle):
        team = {'m_pokemons': []}
        for poke in teamBattle.m_pokemons:
            pd = poke.__dict__
            pd['num'] = pd['num'].__dict__ # unique id
            for i in range(4):
                pd['move'][i] = pd['move'][i].__dict__ # battlemove
            team['m_pokemons'].append(pd)

        return team

    # PO Events

    def onVersionControl(self, version, name):
        self.client.sendObject({'type': 'VersionControl', 'version': version, 'name': name})

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

    def onPlayersList(self, playerInfos):
        players = []
        for player in playerInfos:
            players.append(self.serializePlayer(player))
        self.client.sendObject({'type': 'PlayersList', 'players': (players)})

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
        self.client.sendObject({'type': 'ChallengeStuff', 'challengeInfo': info})

    def onEngageBattle(self, battleid, player1, player2, battleConf, teamBattle):
        if player1 == 0:
            self.client.sendObject({'type': 'EngageBattle', 'battleId': battleid, 
                                    'playerId1': player1, 'playerId2': player2,
                                    'battleConf': battleConf.__dict__, 'teamBattle': self.serializeTeamBattle(teamBattle)})

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

    def onSendMessage(self, message, hasId=False, hasChannel=False, isHtml=False, id=0, channel=0, user=None):
        self.client.sendObject({'type': 'SendMessage', 'id': id, 'message': message, 'channel': channel, 'hasChannel': hasChannel, 'hasId': hasId, 'isHtml': isHtml})

    def onHtmlMessage(self, message):
        self.client.sendObject({'type': 'HtmlMessage', 'message': message})

    def onHtmlChannel(self, chanid, message):
        self.client.sendObject({'type': 'HtmlChannel', 'message': message, 'chanId':chanid})
        
    # Other Events

    def connectionLost(self, reason):
        if self.client:
            self.client.sendObject({'type': 'Disconnected', 'reason': str(reason)})
            print "DISCONNECTED " + str(reason)
            self.client = None

class POFactory(Factory):
    def buildProtocol(self, addr):
        return POHandler()

class POHandler(Protocol):
    def __init__(self):
        self.proxy = None
        self.pending = []

    def __del__(self):
        print 'Deleting handler'

    def connectionMade(self):
        print 'Connected to client.'
        factory = Factory()
        factory.protocol = Registry
        point = TCP4ClientEndpoint(reactor, "pokemon-online.dynalias.net", 5090)
        d = point.connect(factory)

        def gotRegistry(registry):
            def gotAnnouncement(announcement):
                self.sendObject({'type': 'RegistryAnnouncement', 'announcement': announcement})
            def gotServerList(servers):
                self.sendObject({'type': 'ServerList', 'servers': servers})
                registry.transport.loseConnection()
            registry.announcement.addCallback(gotAnnouncement)
            registry.serverlist.addCallback(gotServerList)

        d.addCallback(gotRegistry)
        d.addErrback(self.cantConnect)

    def dataReceived(self, data):
        json = loads(data)

        if json["type"] == "Connect":
            ip = json.get("ip", None)
            port = json.get("port", None)
            if ip and port:
                self.createProxyConnection(ip, port)
                return

        if not self.proxy:
            self.pending.append(data)
            return

        #try:
        method = "on{0}".format(json["type"])
        if hasattr(self, method):
            getattr(self, method)(json)
        else:
            print "Unknown event:", method
        #except Exception as e:
        #    print "Error handling in JSON event: {0}".format(json.get("type"), "UnknownEvent")
        #    print "{0}: {1}".format(e.__class__.__name__, e) 
            
    def sendObject(self, o):
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
        self.proxy.setProxyIP(self.proxy.transport.getHost().host)
        for p in self.pending:
            self.dataReceived(p)

    def cantConnect(self, msg):
        print 'Can\'t connect: {0}'.format(msg)

    # Handing JSON Events from Websocket client
    def onLogin(self, json):
        self.proxy.login(json['name'], clientType=u'webclient', defaultChannel=u'WebClient')

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

    def onChallengeStuff(self, json):
        self.proxy.challengeStuff(ChallengeInfo(json['info']['type'], json['info']['id'], json['info'].get('clauses', 0), json['info'].get('mode', 0)));

    def onBattleCommand(self, json):
        bc = BattleChoice()
        bc.type = BattleChoice.CancelType;
        bc.spot = json['spot']
        self.proxy.battleCommand(json['battleid'], bc)

    def onBattleFinished(self, json):
        self.proxy.battleFinished(json['battleid'], json['result'])

if __name__ == "__main__":
    # run our websocket server
    # serve index.html from the local directory
    root = File('.')
    factory = Site(root)
    reactor.listenTCP(8080, factory)

    factory = POFactory()
    factory = SockJSFactory(factory)
    reactor.listenTCP(8081, factory)

    reactor.run()

