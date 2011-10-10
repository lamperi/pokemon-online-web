# poprotocol.py
# Pokemon Online protocol implemented in Twisted protocol
#
# (c) Toni Fadjukoff 2011
# Licensed under GPL 3.
# See LICENSE.txt for details

from twisted.protocols.basic import Int16StringReceiver

import time
import socket
import struct
import codecs

class PODecoder(object):

    def __init__(self):
        self.codec = codecs.lookup("utf_16_be")

    #### DECODING METHODS

    def decode_number(self, cmd, i, fmt):
        # See http://docs.python.org/library/struct.html#format-characters
        # for explanations of fmt
        l = struct.calcsize(fmt)
        n = struct.unpack(fmt, cmd[i:i+l])[0]
        i+=l
        return (n,i)

    def decode_bytes(self, cmd, i):
        l = struct.unpack("!I", cmd[i:i+4])[0]
        i+=4
        if l == 0xFFFFFFFF:
            b = ""
        else:
            b = cmd[i:i+l]
            i += l
        return (b,i)

    def decode_string(self, cmd, i):
        l = struct.unpack("!I", cmd[i:i+4])[0]
        i+=4
        if l == 0xFFFFFFFF:
            s = ""
        else:
            s = cmd[i:i+l]
            s = self.codec.decode(s)[0]
            i += l
        #print "Extracted \"%s\" (len %d)" % (s,l)
        return (s,i)

    def decode_color(self, cmd, i):
        color = Color()
        color.color_spec, i = self.decode_number(cmd, i, "!b")
        color.alpha, i = self.decode_number(cmd, i, "!H")
        color.red, i = self.decode_number(cmd, i, "!H")
        color.green, i = self.decode_number(cmd, i, "!H")
        color.blue, i = self.decode_number(cmd, i, "!H")
        color.pad, i = self.decode_number(cmd, i, "!H")
        return (color, i)

    def decode_PokeUniqueId(self, cmd, i):
        uid = PokeUniqueId()
        uid.pokenum, i = self.decode_number(cmd, i, "!H")
        uid.subnum, i = self.decode_number(cmd, i, "!B")
        return (uid, i)

    def decode_PlayerInfo(self, cmd, i):
        player = PlayerInfo()
        player.id, i = self.decode_number(cmd, i, "!i")
        player.name, i = self.decode_string(cmd, i)
        player.info, i = self.decode_string(cmd, i)
        player.auth, i = self.decode_number(cmd, i, "!b")
        player.flags, i = self.decode_number(cmd, i, "!B")
        player.rating, i = self.decode_number(cmd, i, "!h")
        for k in range(6):
            player.pokemon[k], i = self.decode_PokeUniqueId(cmd, i)
        player.avatar, i = self.decode_number(cmd, i, "!H")
        player.tier, i = self.decode_string(cmd, i)
        player.color, i = self.decode_color(cmd, i)
        player.gen, i = self.decode_number(cmd, i, "!B")
        return player, i

    def decode_TrainerTeam(self, cmd, i):
        trainerteam = TrainerTeam()
        trainerteam.nick, i = self.decode_string(cmd, i)
        trainerteam.info, i = self.decode_string(cmd, i)
        trainerteam.lose, i = self.decode_string(cmd, i)
        trainerteam.win, i = self.decode_string(cmd, i)
        trainerteam.avatar, i = self.decode_number(cmd, i, "!H")
        trainerteam.defaultTier, i = self.decode_string(cmd, i)
        trainerteam.team, i = self.decode_Team(cmd, i)
        return (trainerteam, i)

    def decode_Team(self, cmd, i):
        team = Team()
        team.gen, i = self.decode_number(cmd, i, "B")
        for k in xrange(6):
            team.poke[k], i = self.decode_PokePersonal(cmd, i)
        return (team, i)

    def decode_PokePersonal(self, cmd, i):
        poke = PokePersonal()
        poke.uniqueid, i = self.decode_PokeUniqueId(cmd, i)
        poke.nickname, i = self.decode_string(cmd, i)
        poke.item, i = self.decode_number(cmd, i, "!H")
        poke.ability, i = self.decode_number(cmd, i, "!H")
        poke.nature, i = self.decode_number(cmd, i, "B")
        poke.gender, i = self.decode_number(cmd, i, "B")
        shiny, i = self.decode_number(cmd, i, "B")
        poke.shiny = shiny > 0
        poke.happiness, i = self.decode_number(cmd, i, "B")
        poke.level, i = self.decode_number(cmd, i, "B")
        #poke.gen, i = self.decode_number(cmd, i, "B")
        for k in xrange(4):
            poke.move[k], i = self.decode_number(cmd, i, "!I")
        for k in xrange(6):
            poke.dv[k], i = self.decode_number(cmd, i, "B")
        for k in xrange(6):
            poke.ev[k], i = self.decode_number(cmd, i, "B")
        return (poke, i)

    def decode_ChallengeInfo(self, cmd, i):
        c = ChallengeInfo()
        c.dsc, i = self.decode_number(cmd, i, "b")
        c.opp, i = self.decode_number(cmd, i, "!i")
        c.clauses, i = self.decode_number(cmd, i, "!I")
        c.mode, i = self.decode_number(cmd, i, "B")
        return (c, i)

    def decode_BattleConfiguration(self, cmd, i):
        bc = BattleConfiguration()
        bc.gen, i = self.decode_number(cmd, i, "B")
        bc.mode, i = self.decode_number(cmd, i, "B")
        bc.id[0], i = self.decode_number(cmd, i, "!i")
        bc.id[1], i = self.decode_number(cmd, i, "!i")
        bc.clauses, i = self.decode_number(cmd, i, "!I")
        return (bc, i)

    def decode_TeamBattle(self, cmd, i):
        tb = TeamBattle()
        for k in xrange(6):
            tb.m_pokemons[k], i = self.decode_PokeBattle(cmd, i)
        return (tb, i)

    def decode_PokeBattle(self, cmd, i):
        pb = PokeBattle()
        pb.num, i = self.decode_PokeUniqueId(cmd, i)
        pb.nick, i = self.decode_string(cmd, i)
        pb.totalLifePoints, i = self.decode_number(cmd, i, "!H")
        pb.lifePoints, i = self.decode_number(cmd, i, "!H")
        pb.gender, i = self.decode_number(cmd, i, "B")
        shiny, i = self.decode_number(cmd, i, "B")
        pb.shiny = shiny > 0
        pb.level, i = self.decode_number(cmd, i, "B")
        pb.item, i = self.decode_number(cmd, i, "!H")
        pb.ability, i = self.decode_number(cmd, i, "!H")
        pb.happiness, i = self.decode_number(cmd, i, "B")
        for k in xrange(5):
            pb.normal_stats[k], i = self.decode_number(cmd, i, "!H")
        for k in xrange(4):
            pb.move[k], i = self.decode_BattleMove(cmd, i)
        for k in xrange(6):
            pb.evs[k], i = self.decode_number(cmd, i, "!i")
        for k in xrange(6):
            pb.dvs[k], i = self.decode_number(cmd, i, "!i")
        return (pb, i)

    def decode_BattleMove(self, cmd, i):
        bm = BattleMove()
        bm.num, i = self.decode_number(cmd, i, "!H")
        bm.PP, i = self.decode_number(cmd, i, "B")
        bm.totalPP, i = self.decode_number(cmd, i, "B")
        return (bm, i)

    def decode_ShallowBattlePoke(self, cmd, i):
#    PROPERTY(QString, nick);
#    PROPERTY(quint32, fullStatus);
#    PROPERTY(Pokemon::uniqueId, num);
#    PROPERTY(bool, shiny);
#    PROPERTY(quint8, gender);
#    PROPERTY(quint8, lifePercent);
#    PROPERTY(quint8, level);
        return (None, i)
        sbp = ShallowBattlePoke()
     
    #### ENCODING METHODS

    def encode_string(self, ustr):
        bytes = self.codec.encode(ustr)[0]
        packed = struct.pack("!I", len(bytes)) + bytes
        return packed

    def encode_bytes(self, bytes):
        packed = struct.pack("!I", len(bytes)) + bytes
        return packed

    def encode_FullInfo(self, fullinfo):
        bytes = self.encode_TrainerTeam(fullinfo.team)
        bytes += struct.pack("B", fullinfo.ladder)
        bytes += struct.pack("B", fullinfo.showteam)
        bytes += self.encode_Color(fullinfo.nameColor)
        return bytes

    def encode_TrainerTeam(self, team):
        bytes = self.encode_string(team.nick)
        bytes += self.encode_string(team.info)
        bytes += self.encode_string(team.lose)
        bytes += self.encode_string(team.win)
        bytes += struct.pack("!H", team.avatar)
        bytes += self.encode_string(team.defaultTier)
        bytes += self.encode_Team(team.team)
        return bytes

    def encode_Team(self, team):
        bytes = struct.pack("B", team.gen)
        for k in xrange(6):
            bytes += self.encode_PokePersonal(team.poke[k])
        return bytes

    def encode_PokePersonal(self, poke):
        bytes = self.encode_PokeUniqueId(poke.uniqueid)
        bytes += self.encode_string(poke.nickname)
        bytes += struct.pack("!HHBBBBB", poke.item, poke.ability, poke.nature, poke.gender, poke.shiny, poke.happiness, poke.level)
        bytes += struct.pack("!4I", *poke.move)
        bytes += struct.pack("!6B", *poke.dv)
        bytes += struct.pack("!6B", *poke.ev)
        return bytes
        
    def encode_PlayerInfo(self, playerInfo):
        return struct.pack("!i", playerInfo.id) +\
        self.encode_string(playerInfo.name) +\
        self.encode_string(playerInfo.info) +\
        struct.pack("!bBh", playerInfo.auth,
        playerInfo.flags, playerInfo.rating) +\
        "".join(self.encode_PokeUniqueId(puid) for puid in playerInfo.pokemon) +\
        struct.pack("!H", playerInfo.avatar) +\
        self.encode_string(playerInfo.tier) +\
        self.encode_Color(playerInfo.color) +\
        struct.pack("!B", playerInfo.gen)

    def encode_PokeUniqueId(self, uid):
        return struct.pack("!HB", uid.pokenum, uid.subnum)

    def encode_Color(self, color):
        return struct.pack("!bhhhhh", color.color_spec, color.alpha, color.red, color.green, color.blue, color.pad)

    def encode_ChallengeInfo(self, info):
        print "info"
        print info.dsc
        print info.opp
        print info.clauses
        print info.mode
        return struct.pack("!biIB", info.dsc, info.opp, info.clauses, info.mode)

    def encode_BattleChoice(self, choice):
        ret = struct.pack("!BB", choice.slot, choice.type)
        if command.type == BattleChoice.SwitchType:
            ret += struct.pack("!b", choice.pokeSlot);
        elif command.type == BattleChoice.AttackType:
            ret += struct.pack("!bb", choice.attackSlot, attackTarget)
        elif command.type == BattleChoice.RearrangeType:
            ret += struct.pack("!bbbbbb", *choice.pokeIndices)
        return ret

class RegistryProtocol(Int16StringReceiver, PODecoder):

    def __init__(self):
        #Int16StringReceiver.__init__(self)
        PODecoder.__init__(self)

    def stringReceived(self, string):
        event = ord(string[0])
        i = 1
        if event == NetworkEvents["PlayersList"]:
             name, i = self.decode_string(string, i)
             desc, i = self.decode_string(string, i)
             nump, i = self.decode_number(string, i, "!h")
             ip, i = self.decode_string(string, i)
             maxp, i = self.decode_number(string, i, "!h")
             port, i = self.decode_number(string, i, "!h")
             self.onPlayersList(name, desc, nump, ip, maxp, port)
        elif event == NetworkEvents["ServerListEnd"]:
             self.onServerListEnd()

    def onPlayersList(self, name, desc, nump, ip, maxp, port):
        """
        Indicates that the registry sent us infornation about one server
        """

    def onServerListEnd(self):
        """
        Indicates that the server list has been sent
        """

class POProtocol(Int16StringReceiver, PODecoder):
    """
    Implements POProtocol
    """

    def __init__(self):
        #Int16StringReceiver.__init__(self)
        PODecoder.__init__(self)

    def stringReceived(self, cmd):
        ev = struct.unpack("B", cmd[:1])[0] 
        cmd = cmd[1:]
        evname = EventNames[ev] if 0 <= ev <= len(EventNames) else None
        if evname is None:
            self.on_ProtocolError(ev, cmd)
        if hasattr(self, "on_"+evname):
            getattr(self, "on_"+evname)(cmd)
        else:
            self.on_NotImplemented(ev, cmd)

    def on_NotImplemented(self, ev, cmd):
        evname = EventNames[ev]
        print "Received command:", evname
        print "Received", len(cmd), "bytes"
        print tuple(ord(i) for i in cmd)

    def on_ProtocolError(self, ev, cmd):
        print "Received unknown byte:", ev
        print "Received", len(cmd), "bytes"
        print tuple(ord(i) for i in cmd)

    #### COMMANDS TO BE SENT TO SERVER

    def login(self, fullinfo):
        logindata=struct.pack('B', NetworkEvents['Login']) + self.encode_FullInfo(fullinfo)
        self.send(logindata)

    def sendMessage(self, message):
        tosend=struct.pack('B', NetworkEvents['SendMessage']) + self.encode_string(message)
        self.send(tosend)

    def register(self):
        tosend=struct.pack('B', NetworkEvents['Register'])
        self.send(tosend)

    def askForPass(self, u):
        tosend = struct.pack('B', NetworkEvents['AskForPass']) + self.encode_string(u)
        self.send(tosend) 

    def sendTeam(self, trainerteam):
        tosend = struct.pack('B', NetworkEvents['SendTeam']) + self.encode_TrainerTeam(trainerteam)
        self.send(tosend)

    def challengeStuff(self, challengeinfo):
        tosend = struct.pack('B', NetworkEvents['ChallengeStuff']) + self.encode_ChallengeInfo(challengeinfo)
        self.send(tosend)

    def battleCommand(self, battleid, slot, battlecommand):
        tosend = struct.pack('Bi', NetworkEvents['BattleCommand']) + slot + self.encode_BattleChoice(battlecommand)
        self.send(tosend)

    def battleFinished(self, battleid, result):
        tosend = struct.pack('!Bii', NetworkEvents['BattleFinished'], battleid, result)
        self.send(tosend)

    def sendPM(self, playerid, message):
        tosend = struct.pack('B', NetworkEvents['SendPM']) + struct.pack("!I", playerid) + self.encode_string(message)
        self.send(tosend)

    def sendChannelMessage(self, chanid, message):
        tosend = struct.pack('B', NetworkEvents['ChannelMessage']) + struct.pack("!I", chanid) + self.encode_string(message)
        self.send(tosend)

    def joinChannel(self, channelname):
        tosend = struct.pack('B', NetworkEvents['JoinChannel']) + self.encode_string(channelname)
        self.send(tosend)

    def partChannel(self, channel):
        tosend = struct.pack('!Bi', NetworkEvents['LeaveChannel'], channel)
        self.send(tosend)

    def kick(self, player):
        tosend = struct.pack('!Bi', NetworkEvents['PlayerKick'], player)
        self.send(tosend)

    def ban(self, player):
        tosend = struct.pack('!Bi', NetworkEvents['PlayerBan'], player)
        self.send(tosend)

    def nameBan(self, name):
        tosend = struct.pack('!Bi', NetworkEvents['CPBan'], self.encode_string(name))
        self.send(tosend)

    def away(self, away):
        tosend = struct.pack('!BB', NetworkEvents['Away'], int(True if away else False))
        self.send(tosend)

    def setProxyIP(self, data):
        tosend = struct.pack('B', NetworkEvents['SetIP']) + self.encode_string(data)
        self.send(tosend)

    def send(self, data):
        data = struct.pack('BB', len(data)/256, len(data)%256)+data
        self.transport.write(data)
        

    ### Battle Messages and their handling

    def handleBattleCommand(self, battleid, bytes):
        msgnro, i = self.decode_number(bytes, 0, "B")
        spot, i = self.decode_number(bytes, i, "B")
        if msgnro in BattleCommands:
            name = BattleCommands[msgnro]
            if hasattr(self, "on_Battle_"+name):
                getattr(self, "on_Battle_"+name)(battleid, spot, bytes[i:])
            else:
                self.on_Battle_NotImplemented(battleid, spot, bytes)
        else:
            self.on_Battle_ProtocolError(battleid, spot, bytes)

    def on_Battle_NotImplemented(self, bid, spot, bytes):
        #print "Error in Battle Protocol:"
        #print tuple(ord(i) for i in bytes)
        pass

    def on_Battle_ProtocolError(self, bid, spot, bytes):
        #print "Error in Battle Protocol:"
        #print tuple(ord(i) for i in bytes)
        pass

    def on_Battle_SendOut(self, bid, spot, bytes):
        silent, i = self.decode_number(bytes, 0, "B")
        prevIndex, i = self.decode_number(bytes, i, "B")
        poke, i = self.decode_ShallowBattlePoke(bytes, i)
        self.onBattleSendOut(bid, spot, silent > 0, prevIndex, poke)

    def onBattleSendOut(self, bid, spot, silent, prevIndex, poke):
        """
        SendOut - called when a pokemon on send on the field
        bid : int - battle id
        spot : int - spot in the field
        silent : bool - should this be announced?
        prevIndex : uint8 - which was the previous index?
        """

    def on_Battle_SendBack(self, bid, spot, bytes):
        self.onBattleSendBack(bid, spot)

    def onBattleSendBack(self, bid, spot):
        """
        SendBack - called when a pokemon is called back
        bid : int - battle id
        spot : int - spot in the field
        """
    def on_Battle_OfferChoice(self, bid, spot, bytes):
        pass # TODO interactive stuff

    def on_Battle_UseAttack(self, bid, spot, bytes):
        attack, i = self.decode_number(bytes, 0, "!H")
        self.onBattleUseAttack(bid, spot, attack)

    def onBattleUseAttack(self, bid, spot, attack):
        """
        UseAttack - called when a pokemon uses a attack
        bid : int - battle id
        spot : int - spot in the field
        attack : uint16 - the number of the used attack
        """

    def on_Battle_BeginTurn(self, bid, spot, bytes):
        turn, i = self.decode_number(bytes, 0, "!H")
        self.onBattleUseAttack(bid, spot, turn)

    def onBattleBeginTurn(self, bid, spot, turn):
        """
        BeginTurn - called when a new turn starts
        bid : int - battle id
        spot : int - spot in the field
        turn : uint16 - the turn which starts
        """
    def on_Battle_ChangePP(self, bid, spot, bytes):
        pass # TODO interactive stuff

    def on_Battle_ChangeHp(self, bid, spot, bytes):
        hp, i = self.decode_number(bytes, 0, "!H") 
        self.onBattleChangeHp(bid, spot, hp)

    def onBattleChangeHp(self, bid, spot, hp):
        """
        ChangeHp - called when HP value changes
        bid : int - battle id
        spot : int - spot in the field
        hp : uint16 - hp value for us, percentage for foe
        """

    def on_Battle_Ko(self, bid, spot, bytes):
        self.onBattleKo(bid, spot)

    def onBattleKo(self, bid, spot):
        """
        Ko - called when someone is KO'd
        bid : int - battle id
        spot : int - spot in the field
        """

    def on_Battle_Effective(self, bid, spot, bytes):
        eff, i = self.decode_number(bytes, 0, "B")
        self.onBattleEffective(bid, spot, eff)

    def onBattleEffective(self, bid, spot, eff):
        """
        Effective - called when a move is not very or super effective
        bid : int - battle id
        spot : int - spot in the field
        eff : byte - the effectiveness of the move
        """

    def on_Battle_Miss(self, bid, spot, bytes):
        self.onBattleMiss(bid, spot)

    def onBattleMiss(self, bid, spot):
        """
        Miss - called when a miss occurs
        bid : int - battle id
        spot : int - spot in the field
        """

    def on_Battle_CriticalHit(self, bid, spot, bytes):
        self.onBattleCriticalHit(bid, spot)

    def onBattleCriticalHit(self, bid, spot):
        """
        CriticalHit - called when a critical hit occurs
        bid : int - battle id
        spot : int - spot in the field
        """

    def on_Battle_Hit(self, bid, spot, bytes):
        self.onBattleHit(bid, spot)

    def onBattleHit(self, bid, spot):
        """
        Hit - called when a hit occurs
        bid : int - battle id 
        spot : int - spot in the field
        """

    def on_Battle_StatChange(self, bid, spot, bytes):
        stat, i = self.decode_number(bytes, 0, "b")
        boost, i = self.decode_number(bytes, i, "b")
        self.onBattleStatChange(bid, spot, stat, boost)

    def onBattleStatChange(self, bid, spot, stat, boost):
        """
        StatChange - a stat changes
        bid : int - battle id
        spot : int - spot in the field
        stat : int8 - the stat affected
        boost : int8 - the boost in the stat
        """

    def on_Battle_StatusChange(self, bid, spot, bytes):
        status, i = self.decode_number(bytes, 0, "b")
        multiturn, i = self.decode_number(bytes, i, "B")
        self.onBattleStatusChange(bid, spot, status, multiturn > 0) 

    def onBattleStatusChange(self, bid, spot, status, multiturn):
        """
        StatusChange - status changes
        bid : int - battle id
        spot : int - spot in the field
        status : int8 - status number
        multiturn : bool - not used
        """

    def on_Battle_StatusMessage(self, bid, spot, bytes):
        statusmessage, i = self.decode_number(bytes, 0, "b")
        self.onBattleStatusMessage(bid, spot, status)

    def onBattleStatusMessage(self, bid, spot, statusmessage):
        """
        StatusMessage - a new status related message
        statusmessage : int8 - the id of the status message
        """

    def on_Battle_Failed(self, bid, spot, bytes):
        self.onBattleFaileD(bid, spot)

    def onBattleFailed(self, bid, spot):
        """
        Failed - a move failed
        """

    def on_Battle_BattleChat(self, bid, spot, bytes):
        message, i = self.decode_string(bytes, 0)
        self.onBattleBattleChat(bid, spot, message)

    def onBattleBattleChat(self, bid, spot, message):
        """
        BattleChat - a player chats
        message : string - the message including player name
        """

    def on_Battle_MoveMessage(self, bid, spot, bytes):
        move, i = self.decode_number(bytes, 0, "!H")
        part, i = self.decode_number(bytes, i, "B")
        type, i = self.decode_number(bytes, i, "b")
        foe, i = self.decode_number(bytes, i, "b")
        other, i = self.decode_number(bytes, i, "!h")
        q, i = self.decode_string(bytes, i)
        self.onBattleMoveMessage(bid, spot, move, part, type, foe, other, q)

    def onBattleMoveMessage(self, bid, spot, move, part, type, foe, other, q):
        """
        MoveMessage - a move related message
        move : uint16 - the move id
        part : uint8 - the sub id of the message
        type : int8 - the elemental type of the message
        foe : int8 - foe spot
        other : int16 - additional numeric information
        q : string - additional string information
        """

    def on_Battle_ItemMessage(self, bid, spot, bytes):
        item, i = self.decode_number(bytes, 0, "!H")
        part, i = self.decode_number(bytes, i, "B")
        foe, i = self.decode_number(bytes, i, "b")
        berry, i = self.decode_number(bytes, i, "!H")
        other, i = self.decode_number(bytes, i, "!H")
        self.onBattleItemMessage(bid, spot, item, part, foe, berry, other)

    def onBattleItemMessage(self, bid, spot, item, part, foe, berry, other):
        """
        ItemMessage - an item related message
        """

    def on_Battle_NoOpponent(self, bid, spot, bytes):
        self.onBattleNoOpponent(bid, spot)

    def onBattleNoOpponent(self, bid, spot):
        """
        NoOpponent - there's no opponent message
        """

    def on_Battle_Flinch(self, bid, spot, bytes):
        self.onBattleFlinch(bid, spot)

    def onBattleFlinch(self, bid, spot):
        """
        Flinch - flinch happened message
        """

    def on_Battle_Recoil(self, bid, spot, bytes):
        damage, i = self.decode_number(bytes, 0, "B")
        self.onBattleRecoil(bid, spot, damage > 0)

    def onBattleRecoil(self, bid, spot, damage):
        """
        Recoil - a recoil or draining happened
        """

    def on_Battle_WeatherMessage(self, bid, spot, bytes):
        wstatus, i = self.decode_number(bytes, 0, "B")
        weather, i = self.decode_number(bytes, i, "B")
        self.onBattleWeatherMessage(bid, spot, wstatus, weather)

    def onBattleWeatherMessage(self, bid, spot, wstatus, weather):
        """
        WeatherMessage
        """

    def on_Battle_StraightDamage(self, bid, spot, bytes):
        damage, i = self.decode_number(bytes, 0, "!H")
        self.onBattleStraightDamage(bid, spot, damage)

    def onBattleStraightDamage(self, bid, spot, damage):
        """
        StraightDamage
        """

    def on_Battle_AbilityMessage(self, bid, spot, bytes):
        ab, i = self.decode_number(bytes, 0, "!H")
        part, i = self.decode_number(bytes, i, "B")
        type, i = self.decode_number(bytes, i, "b")
        foe, i = self.decode_number(bytes, i, "b")
        other, i = self.decode_number(bytes, i, "!h")
        self.onBattleAbilityMessage(bid, spot, ab, part, type, foe, other)

    def onBattleAbilityMessage(self, bid, spot, ab, part, type, foe, other):
        """
        AbilityMessage
        """

    def on_Battle_AbsStatusChange(self, bid, spot, bytes):
        poke, i = self.decode_number(bytes, 0, "b")
        status, i = self.decode_number(bytes, 0, "b")
        self.onBattleAbsStatusChange(bid, spot, poke, status)

    def onBattleAbsStatusChange(self, bid, spot, poke, status):
        """
        AbsStatusChange
        """

    def on_Battle_Substitute(self, bid, spot, bytes):
    def on_Battle_BattleEnd(self, bid, spot, bytes):
    def on_Battle_BlankMessage(self, bid, spot, bytes):
    def on_Battle_CancelMove(self, bid, spot, bytes):
    def on_Battle_Clause (self, bid, spot, bytes):
    def on_Battle_DynamicInfo (self, bid, spot, bytes):
    def on_Battle_DynamicStats (self, bid, spot, bytes):
    def on_Battle_Spectating(self, bid, spot, bytes):
    def on_Battle_SpectatorChat(self, bid, spot, bytes):
    def on_Battle_AlreadyStatusMessage(self, bid, spot, bytes):
    def on_Battle_TempPokeChange(self, bid, spot, bytes):
    def on_Battle_ClockStart (self, bid, spot, bytes):
    def on_Battle_ClocakStop (self, bid, spot, bytes):
    def on_Battle_Rated(self, bid, spot, bytes):
    def on_Battle_TierSection (self, bid, spot, bytes):
    def on_Battle_EndMessage(self, bid, spot, bytes):
    def on_Battle_PointEstimate(self, bid, spot, bytes):
    def on_Battle_MakeYourChoice(self, bid, spot, bytes):
    def on_Battle_Avoid(self, bid, spot, bytes):
    def on_Battle_RearrangeTeam(self, bid, spot, bytes):
    def on_Battle_SpotShifts(self, bid, spot, bytes):


    ### Events from connecting to server

    def on_VersionControl(self, cmd):
        version, i = self.decode_string(cmd, 0)
        self.onVersionControl(version)

    def onVersionControl(self, version):
        """
        Event launched soon after connection is made
        version : unicode - the server version
        """

    def on_ServerName(self, cmd):
        name, i = self.decode_string(cmd, 0)
        self.onServerName(name)

    def onServerName(self, serverName):
        """
        Event launched soon after connection is made
        serverName : unicode - the server name
        """

    def on_Register(self, cmd):
        self.onRegister()

    def onRegister(self):
        """
        Event telling us that we can register our name
        """

    def on_AskForPass(self, cmd):
        salt, i = self.decode_string(cmd, 0)
        self.onAskForPass(salt)

    def on_Login(self, cmd):
        player, i = self.decode_PlayerInfo(cmd, 0)
        self.onLogin(player)

    def onLogin(self, playerInfo):
        """
        Event telling us that player has logged into server
        playerInfo : PlayerInfo - contains the data of the player
        """

    def on_Logout(self, cmd):
        playerid, i = self.decode_number(cmd, 0, "!i")
        self.onLogout(playerid)

    def onLogout(self, playerid):
        """
        Event telling us that a player has logged out
        playerid : int - the id of the player
        """

    def on_Announcement(self, cmd):
        announcement, i = self.decode_string(cmd, 0)
        self.onAnnouncement(announcement)

    def onAnnouncement(self, announcement):
        """
        Event telling us that the server send an announcement
        announcement : unicode - the announcement server send
        """

    def on_KeepAlive(self, cmd):
        pass

    def on_TierSelection(self, cmd):
        tiers = {}
        stack = []
        raw, i = self.decode_bytes(cmd, 0)
        pairs = []
        while i < len(raw):
            currentLevel, i = self.decode_number(raw, i, "B")
            name, i = self.decode_string(raw, i)
            pairs.append((currentLevel, name))
        self.onTierSelection(pairs)

    def onTierSelection(self, pairs):
        """
        Event telling us the Tier list of this server
        pairs : list of [int, unicode] - contains the tree structure of tiers 
        """

    def on_ChannelsList(self, cmd):
        numitems, i = self.decode_number(cmd, 0, "!I")
        channels = []
        for k in xrange(numitems):
            chanid, i = self.decode_number(cmd, i, "!i")
            channame, i = self.decode_string(cmd, i) 
            channels.append([chanid, channame])
        self.onChannelsList(channels)

    def onChannelsList(self, channels):
        """
        Event telling us the channel list of the server
        channels : list of [int, unicode] - contains channel IDs and names
        """

    def on_PlayersList(self, cmd):
        player, i = self.decode_PlayerInfo(cmd, 0)
        self.onPlayersList(player)

    def onPlayersList(self, playerInfo):
        """
        Event containing the info of a player. Sent after log in.
        playerInfo : PlayerInfo - the info of the player
        """

    def on_PlayerBan(self, cmd):
        playerid, i = self.decode_number(cmd, 0, "!i")
        srcid, i = self.decode_number(cmd, i, "!i")
        self.onPlayerBan(playerid, srcid)

    def onPlayerBan(self, player, src):
        """
        Event telling us that someone was banned.
        player : int - the id of the player
        src : int - the id of the banner
        """

    def on_PlayerKick(self, cmd):
        playerid, i = self.decode_number(cmd, 0, "!i")
        srcid, i = self.decode_number(cmd, i, "!i")
        self.onPlayerKick(playerid, srcid)

    def onPlayerKick(self, player, src):
        """
        Event telling us that someone was kicked.
        player : int - the id of the player
        src : int - the id of the kicker
        """

    def on_BattleList(self, cmd):
        print "TODO", "on_BattleList"

    ### Pokemon related events
    def on_SendTeam(self, cmd):
        player, i = self.decode_PlayerInfo(cmd, 0)
        self.onSendTeam(player)

    def onSendTeam(self, playerInfo):
        """
        Event telling us about a team change
        playerInfo : PlayerInfo - the new info of the player
        """

    ### Battle related events

    def on_ChallengeStuff(self, cmd):
        chall, i = self.decode_ChallengeInfo(cmd, 0)
        self.onChallengeStuff(chall)

    def onChallengeStuff(self, challengeInfo):
        """
        Event telling us that we have been challenged
        challengeInfo : ChallengeInfo - the info of the challenge
        """

    def on_EngageBattle(self, cmd):
        battleid, i = self.decode_number(cmd, 0, "!i")
        pid1, i = self.decode_number(cmd, i, "!i")
        pid2, i = self.decode_number(cmd, i, "!i")
        if pid1 == 0:
            battleconf, i = self.decode_BattleConfiguration(cmd, i)
            teambattle, i = self.decode_TeamBattle(cmd, i)
            self.onEngageBattle(battleid, pid1, pid2, battleconf, teambattle)
        else:
            self.onEngageBattle(battleid, pid1, pid2, None, None)

    def onEngageBattle(self, battleid, player1, player2, battleConf, teamBattle):
        """
        Event telling us the basic info when a battle begins
        battleid : int - the id of this battle
        player1 : int - the id of player 1 - if 0, this is our battle
        player2 : int - the id of our enemy
        Following are not None only if this is our battle:
        battleConf : BattleConfiguration - the configuration of this battle
        teamBattle : TeamBattle - contains our team for this battle
        """

    def on_BattleMessage(self, cmd):
        battleid, i = self.decode_number(cmd, 0, "!i")
        b, i = self.decode_bytes(cmd, i)
        self.handleBattleCommand(battleid, b)
        self.onBattleMessage(battleid, b)

    def onBattleMessage(self, battleid, bytes):
        """
        Event telling us that Battle Message was received
        It is recommended to use onBattle* functions which will parse
        the rest of the battle message event too
        battleid : int - the id of the battle
        bytes : bytes - rest of event
        """

    def on_BattleFinished(self, cmd):
        battleid, i = self.decode_number(cmd, 0, "!i")
        result, i = self.decode_number(cmd, i, "!B")
        winner, i = self.decode_number(cmd, i, "!i")
        loser, i = self.decode_number(cmd, i, "!i")
        outcome = ["Forfeit", "Win", "Tie", "Close"][result]
        self.onBattleFinished(battleid, outcome, winner, loser)

    def onBattleFinished(self, battleid, outcome, winner, loser):
        """
        Event telling us that a battle finished
        battleid : int - the id of the battle
        outcome : str - either Forfeit, Win, Tie or Close
        winner : int - the id of the winning player
        loser : int - the id of the losing player
        """
      
    ### Channel related events

    def on_ChannelPlayers(self, cmd):
        chanid, i = self.decode_number(cmd, 0, "!i")
        numitems, i = self.decode_number(cmd, i, "!I")
        playerlist = []
        for k in xrange(numitems):
            playerid, i = self.decode_number(cmd, i, "!i")
            playerlist.append(playerid)
        self.onChannelPlayers(chanid, playerlist)
    
    def onChannelPlayers(self, chanid, playerlist):
        """
        Event telling us the players of a channel
        chanid : int - the id of the channel
        playerlist : list of ints - contains the ids of the players
        """

    def on_JoinChannel(self, cmd):
        chanid, i = self.decode_number(cmd, 0, "!i")
        playerid, i = self.decode_number(cmd, i, "!i")
        self.onJoinChannel(chanid, playerid) 

    def onJoinChannel(self, chanid, playerid):
        """
        Event telling us that a player joined a channel
        chanid : int - the id of the channel
        playerid : int - the id of the player
        """

    def on_LeaveChannel(self, cmd):
        chanid, i = self.decode_number(cmd, 0, "!i")
        playerid, i = self.decode_number(cmd, i, "!i")
        self.onLeaveChannel(chanid, playerid)

    def onLeaveChannel(self, chanid, playerid):
        """
        Event telling us that a player left a channel
        chanid : int - the id of the channel
        playerid : int - the id of the player
        """

    def on_ChannelBattle(self, cmd):
        chanid, i = self.decode_number(cmd, 0, "!i")
        battleid, i = self.decode_number(cmd, 0, "!i")
        player1, i = self.decode_number(cmd, i, "!i")
        player2, i = self.decode_number(cmd, i, "!i")
        self.onChannelBattle(chanid, battleid, player1, player2)

    def onChannelBattle(self, chanid, battleid, player1, player2):
        """
        Event telling us that a battle started and the
        battle should be associated with the channel.
        chanid : int - the id of the channel
        battleid : int - the id of the battle
        player1 : int - the id of the first player
        player2 : int - the id of the second player
        """

    def on_ChannelMessage(self, cmd):
        chanid, i = self.decode_number(cmd, 0, "!i")
        message, i = self.decode_string(cmd, i)
        splitted = message.split(":", 1)
        if len(splitted) == 2:
            user = splitted[0]
            msg = splitted[1].lstrip()
            self.onChannelMessage(chanid, user, msg)
        else:
            self.onChannelMessage(chanid, "", message)

    def onChannelMessage(self, chanid, user, message):
        """
        Event telling us that a player messaged a channel
        chanid : int - the id of the channel
        user : unicode - the name of the user
        message : unicode - the message
        """

    def on_RemoveChannel(self, cmd):
        chanid, i = self.decode_number(cmd, 0, "!i")
        self.onRemoveChannel(chanid)

    def onRemoveChannel(self, chanid):
        """
        Event telling us that a channel was removed
        chanid : int - the id of the channel
        """

    def on_AddChannel(self, cmd):
        channame, i = self.decode_string(cmd, 0)
        chanid, i = self.decode_number(cmd, i, "!i")
        self.onAddChannel(chanid, channame)

    def onAddChannel(self, chanid, channame):
        """
        Event telling us that a channel was removed
        chanid : int - the id of the channel
        channame : unicode - the name of the channel
        """

    def on_HtmlChannel(self, cmd):
        chanid, i = self.decode_number(cmd, 0, "!i")
        message, i = self.decode_string(cmd, i)
        self.onHtmlChannel(chanid, message)
        
    def onHtmlChannel(self, chanid, message):
        """
        Event telling us that a html message was sent to a channel
        """

    ### Global events

    def on_SendPM(self, cmd):
        playerid, i = self.decode_number(cmd, 0, "!i")
        message, i = self.decode_string(cmd, i) 
        self.onSendPM(playerid, message)

    def onSendPM(self, playerid, message):
        """
        Event telling us of a private message
        playerid : int - the id of the sender
        message : unicode - the actual message
        """

    def on_Away(self, cmd):
        playerid, i = self.decode_number(cmd, 0, "!i")
        status, i = self.decode_number(cmd, i, "B")
        self.onAway(playerid, status>0)

    def onAway(self, playerid, isAway):
        """
        Event telling us that some player changed away status
        playerid : int - the id of the player
        isAway : Boolean - is the player away
        """

    def on_SendMessage(self, cmd):
        message, i = self.decode_string(cmd, 0)
        splitted = message.split(":", 1)
        if len(splitted) == 2:
            user = splitted[0]
            msg = splitted[1].lstrip()
            self.onSendMessage(user, msg)
        else:
            self.onSendMessage("", message)

    def onSendMessage(self, user, message):
        """
        Event telling us of a server wide message
        user : unicode - the name of the user
        message - unicode : the real message
        """

    def on_HtmlMessage(self, cmd):
        html, i = self.decode_string(cmd, 0)
        self.onHtmlMessage(html)

    def onHtmlMessage(self, message):
        """
        Event telling us of a server wide HTML message
        message - unicode : the HTML message
        """
  
# Dict for NetworkEvent codes
NetworkEvents = {
        'WhatAreYou': 0,
        'WhoAreYou': 1,
        'Login': 2,
        'Logout': 3,
        'SendMessage': 4,
        'PlayersList': 5,
        'SendTeam': 6,
        'ChallengeStuff': 7,
        'EngageBattle': 8,
        'BattleFinished': 9,
        'BattleMessage': 10,
        'BattleChat': 11,
        'KeepAlive': 12,
        'AskForPass': 13,
        'Register': 14,
        'PlayerKick': 15,
        'PlayerBan': 16,
        'ServNumChange': 17,
        'ServDescChange': 18,
        'ServNameChange': 19,
        'SendPM': 20,
        'Away': 21,
        'GetUserInfo': 22,
        'GetUserAlias': 23,
        'GetBanList': 24,
        'CPBan': 25,
        'CPUnban': 26,
        'SpectateBattle': 27,
        'SpectatingBattleMessage': 28,
        'SpectatingBattleChat': 30,
        'SpectatingBattleFinished': 30,
        'LadderChange': 31,
        'ShowTeamChange': 32,
        'VersionControl': 33,
        'TierSelection': 34,
        'ServMaxChange': 35,
        'FindBattle': 36,
        'ShowRankings': 37,
        'Announcement': 38,
        'CPTBan': 39,
        'CPTUnban': 40,
        'PlayerTBan': 41,
        'GetTBanList': 42,
        'BattleList': 43,
        'ChannelsList': 44,
        'ChannelPlayers': 45,
        'JoinChannel': 46,
        'LeaveChannel': 47,
        'ChannelBattle': 48,
        'RemoveChannel': 49,
        'AddChannel': 50,
        'ChannelMessage': 51,
        'ChanNameChange': 52,
        'HtmlMessage': 53,
        'HtmlChannel': 54,
        'ServerName': 55,
        'SpecialPass': 56,
        'ServerListEnd': 57,
        'SetIP': 58,
}

EventNames = [0] * len(NetworkEvents)
for name,number in NetworkEvents.iteritems():
    EventNames[number] = name;

ChallengeDesc = {
     'Sent': 0,
     'Accepted': 1,
     'Cancelled': 2,
     'Busy': 3,
     'Refused': 4,
     'InvalidTeam': 5,
     'InvalidGen': 6,
     'ChallengeDescLast': 7
};

BattleCommands = {   
        'SendOut': 0,
        'SendBack': 1,
        'UseAttack': 2,
        'OfferChoice': 3,
        'BeginTurn': 4,
        'ChangePP': 5,
        'ChangeHp': 6,
        'Ko': 7, 
        'Effective': 8,
        'Miss': 9,
        'CriticalHit': 10, 
        'Hit': 11,
        'StatChange': 12,
        'StatusChange': 13,
        'StatusMessage': 14,
        'Failed': 15,
        'BattleChat': 16,
        'MoveMessage': 17,
        'ItemMessage': 18,
        'NoOpponent': 19,
        'Flinch': 20, 
        'Recoil': 21,
        'WeatherMessage': 22,
        'StraightDamage': 23,
        'AbilityMessage': 24,
        'AbsStatusChange': 25,
        'Substitute': 26,
        'BattleEnd': 27,
        'BlankMessage': 28,
        'CancelMove': 29,
        'Clause': 30, 
        'DynamicInfo': 31, 
        'DynamicStats': 32, 
        'Spectating': 33,
        'SpectatorChat': 34,
        'AlreadyStatusMessage': 35,
        'TempPokeChange': 36,
        'ClockStart': 37, 
        'ClockStop': 38, 
        'Rated': 39,
        'TierSection': 40,
        'EndMessage': 41,
        'PointEstimate': 42,
        'MakeYourChoice': 43,
        'Avoid': 44,
        'RearrangeTeam': 45,
        'SpotShifts': 46
}

BattleCommandNames = [0] * len(BattleCommands)
for name,number in BattleCommands.iteritems():
    BattleCommandNames[number] = name;

### Structs used in Pokemon Online Protocol

class Color(object):
    def __init__(self, color_spec=0, alpha=0, red=0, green=0, blue=0, pad=0):
        self.color_spec = 0
        self.alpha = 0
        self.red = 0
        self.green = 0
        self.blue = 0
        self.pad = 0

    def __repr__(self):
        return "<POProtocol.Color (spec=%d, alpha=%d, red=%d, blue=%d, green=%d, pad=%d)>" % (self.color_spec, self.alpha, self.red, self.blue, self.green, self.pad)

class PlayerInfo(object):
    def __init__(self):
        self.id = 0
        self.name = ""
        self.info = ""
        self.auth = 0
        self.flags = 0
        self.rating = 0
        self.pokemon = [0]*6
        self.avatar = 0
        self.tier = ""
        self.color = 0
        self.gen = 0
        self.away = False
        self.channels = {}

    def update(self, o):
        if self.id != o.id:
            raise "Updating with different ID!"
        self.name = o.name
        self.info = o.info
        self.auth = o.auth
        self.flags = o.flags
        self.rating = o.rating
        self.pokemon = o.pokemon
        self.avatar = o.avatar
        self.tier = o.tier
        self.color = o.color
        self.gen = o.gen
        self.away = o.away

    def __repr__(self):
        return "<POProtocol.PlayerInfo (id=%d, name=%r)>" % (self.id, self.name)

class FullInfo(object):
    def __init__(self):
        self.team = 0 # TrainerTeam
        self.ladder = False # Bool
        self.showteam = False # Bool
        self.nameColor = 0 # Color

class TrainerTeam(object):
    def __init__(self):
        self.nick = ""
        self.info = ""
        self.lose = ""
        self.win = ""
        self.avatar = 0
        self.defaultTier = ""
        self.team = Team()
    def __repr__(self):
        return "<POProtocol.TrainerTeam (nick=%r, team=%r)>" % (self.nick, self.team)

class Team(object):
    def __init__(self):
        self.gen = 0
        self.poke = [0]*6
        for k in xrange(6):
            self.poke[k] = PokePersonal() 
    def __repr__(self):
        return "<POProtocol.Team (gen=%d, team=%r)>" % (self.gen, self.poke)

class PokePersonal(object):
    def __init__(self):
        self.uniqueid = PokeUniqueId()
        self.nickname = ""
        self.item = 0
        self.nature = 0
        self.gender = 0
        self.shiny = 0
        self.happiness = 0
        self.level = 0
        self.move = [0]*4
        self.dv = [0]*6
        self.ev = [0]*6
    def __repr__(self):
        return "<POProtocol.PokePersonal (uniqueid=%r, nickname=%e)>" % (self.uniqueid, self.nickname)

class PokeUniqueId(object):
    def __init__(self, pokenum=0, subnum=0):
        self.pokenum = pokenum
        self.subnum = subnum
    def __repr__(self):
        return "<POProtocol.PokeUniquiId (pokenum=%d, subnum=%d)>" % (self.pokenum, self.subnum)

class ChallengeInfo(object):
    def __init__(self, opp = 0, dsc = 0, clauses = 0, mode = 0):
        self.dsc = opp
        self.opp = dsc
        self.clauses = clauses
        self.mode = mode
    def __repr__(self):
        return "<POProtocol.ChallengeInfo (dsc=%d, opp=%d, clauses=%d, mode=%d)>" % (self.dsc, self.opp, self.clauses, self.mode)

class BattleConfiguration(object):
    def __init__(self):
        self.gen = 0
        self.mode = 0
        self.id = [0, 0]
        self.clauses = 0
    def __repr__(self):
        return "<POProtocol.BattleConfiguration (gen=%d, mode=%d, id=%r, clauses=%d)>" % (self.gen, self.mode, self.id, self.clauses)

class TeamBattle(object):
    def __init__(self):
        self.m_pokemons = [None]*6
    def __repr__(self):
        return "<POProtocol.TeamBattle (m_pokemons=%r)>" % (self.m_pokemons)

class PokeBattle(object):
    def __init__(self):
        self.num = PokeUniqueId()
        self.nick = ""
        self.totalLifePoints = 0
        self.lifePoints = 0
        self.gender = 0
        self.shiny = False
        self.item = 0
        self.ability = 0
        self.happiness = 0
        self.normal_stats = [0]*5
        self.move = [0]*4
        self.evs = [0]*6
        self.dvs = [0]*6
    def __repr__(self):
        return "<POProtocol.PokeBattle (num=%r, nick=%r)>" % (self.num, self.nick)

class BattleChoice(object):
    def __init__(self):
        self.slot = 0
        self.type = 0

    def __repr__(self):
        return "<POProtocol.BattleChoice (type=%r, slot=%r)>" % (self.type, self.slot)

class BattleMove(object):
    def __init__(self):
        self.num = 0
        self.PP = 0
        self.totalPP = 0
    def __repr__(self):
        return "<POProtocol.BattleMove (num=%d, PP=%d, totalPP=%d)>" % (self.num, self.PP, self.totalPP)

class Channel(object):
    def __init__(self, chanid, channame):
        self.id = chanid
        self.name = channame
        self.players = {}
    def __repr__(self):
        return "<POProtocol.Channel (id=%d, name=%r, playercount=%d)>" % (self.id, self.name.encode('utf-8'), len(self.players))

class Battle(object):
    def __init__(self, battleid, enemyid, battleconf, myteam):
        self.id = battleid
        self.enemy = enemyid
        self.conf = battleconf
        self.team = myteam

    def __repr__(self):
        return "<POProtocol.Battle (id=%d, enemy=%d, team=%r)>" % (self.id, self.enemy, self.team)
