from poprotocol import *

def loadTeam(fn=None):
    # TODO: read fullinfo from file
    if fn is None:
        return loadHardCoded()
    raise "Not implemented"

def loadHardCoded():
    fullinfo = FullInfo()
    fullinfo.team = TrainerTeam()
    fullinfo.team.nick = u"Lamper1"
    fullinfo.team.info = u"Web Client"
    fullinfo.team.lose = u""
    fullinfo.team.win = u""
    fullinfo.team.avatar = 0
    fullinfo.team.defaultTier = u"Dream World"
    fullinfo.team.team.gen = 5
    fullinfo.team.team.poke[0].uniqueid = PokeUniqueId(149,0)
    fullinfo.team.team.poke[0].nickname = u"Dragonite"
    fullinfo.team.team.poke[0].item = 37
    fullinfo.team.team.poke[0].ability = 136
    fullinfo.team.team.poke[0].nature = 17
    fullinfo.team.team.poke[0].shiny = 0
    fullinfo.team.team.poke[0].happiness = 0
    fullinfo.team.team.poke[0].level = 100
    fullinfo.team.team.poke[0].gender = 1
    fullinfo.team.team.poke[0].move = [434, 89, 245, 126]
    fullinfo.team.team.poke[0].dv = [31, 31, 31, 31, 31 ,31]
    fullinfo.team.team.poke[0].ev = [0, 252, 0, 252, 0, 4]
    fullinfo.team.team.poke[1] = fullinfo.team.team.poke[0]
    fullinfo.team.team.poke[2] = fullinfo.team.team.poke[0]
    fullinfo.team.team.poke[3] = fullinfo.team.team.poke[0]
    fullinfo.team.team.poke[4] = fullinfo.team.team.poke[0]
    fullinfo.team.team.poke[5] = fullinfo.team.team.poke[0]
    fullinfo.ladder = False
    fullinfo.showteam = True
    fullinfo.nameColor = Color()
    return fullinfo

