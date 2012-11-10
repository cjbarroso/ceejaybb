import os
import sys
from local_settings import *
import shelve

dc = shelve.open(CONFIGFILE)

if len(sys.argv) < 2:
    print "Debe invocar con el parametro 'confirmo' para que se genera la BD"
    sys.exit()

# administradores del bot, y los unicos que pueden hacer cambios en la
# configuracion
dc['adminusers'] = set((
                    "cjbarroso@unaffiliated/cjbarroso",
                    ))

# Usuarios autorizados a interactuar con el bot
dc['authusers'] = set(())

# Usuarios que reciben la notificacion de standup
dc['standuppers'] = set(())

dc['botname'] = "ceejaybb"
dc['ircnet'] = "irc.freenode.com"
dc['canal'] = "#machinalis-cpi"

dc['horario_standup_hora'] = 18
dc['horario_standup_minuto'] = 5

dc['nickservpass'] = "caquita00"

dc['verboso'] = True

dc.close()
