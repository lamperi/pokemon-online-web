from poprotocol import *
from xml.dom.minidom import parse

def loadTeam(fn = None):
    if fn is None:
        return loadHardCoded()
    
    def content(element):
        return element.childNodes[0].data
    
    dom = parse(fn)
    
    info = FullInfo()
    info.nameColor = Color()
    info.team = TrainerTeam()
    
    team    = dom.getElementsByTagName('Team')[0]
    trainer = dom.getElementsByTagName('Trainer')[0]
    
    info.team.nick   = content(trainer)
    info.team.info   = trainer.getAttribute('infoMsg')
    info.team.lose   = trainer.getAttribute('loseMsg')
    info.team.win    = trainer.getAttribute('winMsg')
    info.team.avatar = int(trainer.getAttribute('avatar'))
    info.team.defaultTier = team.getAttribute('defaulttier')
    
    info.team.team.gen = int(team.getAttribute('gen'))

    i = 0
    for pokemon in team.getElementsByTagName('Pokemon'):
        p = PokePersonal()
        
        pid  = int(pokemon.getAttribute('Num'))
        form = int(pokemon.getAttribute('Forme'))
        p.uniqueid  = PokeUniqueId(pid, form)
        p.nickname  = pokemon.getAttribute('Nickname')
        p.item      = int(pokemon.getAttribute('Item'))
        p.nature    = int(pokemon.getAttribute('Nature'))
        p.gender    = int(pokemon.getAttribute('Gender'))
        p.shiny     = int(pokemon.getAttribute('Shiny'))
        p.happiness = int(pokemon.getAttribute('Happiness'))
        p.level     = int(pokemon.getAttribute('Lvl'))
        
        p.move = p.dv = p.ev = []
        for move in pokemon.getElementsByTagName('Move'):
            p.move.append(int(content(move)))
        for dv in pokemon.getElementsByTagName('DV'):
            p.dv.append(int(content(dv)))
        for ev in pokemon.getElementsByTagName('Ev'):
            p.ev.append(int(content(ev)))
       
        info.team.team.poke[i] = p
        i += 1
    print info.team
    return info





def loadHardCoded():
    fullinfo = FullInfo()
    fullinfo.team = TrainerTeam()
    fullinfo.team.nick = u"Lamper1"
    fullinfo.team.info = u"Python Client"
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
    fullinfo.showteam = False
    fullinfo.nameColor = Color()
    return fullinfo

