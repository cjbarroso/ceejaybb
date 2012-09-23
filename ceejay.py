"""
Bot monocanal.
Este es el archivo principal del bot.

TODO: Hacer que reconozca los usuarios usando nicks de IRC y no solo el
nickname pelado

"""
import re
import os
import time
import shelve
import logging
import logging.handlers

from ircutils import bot, events
from local_settings import *
from apscheduler.scheduler import Scheduler

from trellocards import TrelloQuerier

class TrelloBot(bot.SimpleBot):

    def __init__(self, *args, **kwargs):

        self.db = shelve.open(CONFIGFILE)
        if not self.db:
            print "No hay configuracion. Ejecute makeconfig"
            return False
        super(TrelloBot, self).__init__(self.db['botname'])
        self.__c_inicializar()


    # Helpers {{{

    def __c_inicializar(self, *args, **kwargs):
        """Iniciacion de variables. Reinicia el bot"""
        # abrimos el archivo de configuracion
        self.querier = TrelloQuerier()
        # por si queremos que este mudo
        self.mudo = False
        # Para disparar eventos a determinados horarios
        self.sched = Scheduler()
        self.sched.start()
        self.configurar_eventos()

    def cargar_configuracion(self):
        """Carga la configuracion desde el disco"""
        self.db = shelve.open(CONFIGFILE)
        if not self.db:
            print "No hay configuracion. Ejecute makeconfig"
            return False

    def configurar_eventos(self):
        """Agrega los recordatorios y la standup al calendario
        """
        # agrego tareas periodicas de standup
        self.sched.add_cron_job(self.recordatorio_standup,
                hour=int(self.db['horario_standup_hora']),
                minute=(int(self.db['horario_standup_minuto']) - 3) % 60)

        self.sched.add_cron_job(self.__c_sdpbg,
                hour=int(self.db['horario_standup_hora']),
                minute=int(self.db['horario_standup_minuto'])
                )

    def loguear_mensaje(self, event):
        """Logs al disco"""
        logging.debug("<%s> %s" % (event.source, event.message))

    def buscar_tarjeta_trello(self, event):
        m = re.findall("\s(:\d+)", event.message)
        for e in m:
            jeje = self.querier.buscar_carta(e)
            self.decir(mensaje=str(jeje), event=event)

    def recordatorio_standup(self):
        self.decir(
                mensaje="Standup inminente... %s" % ", ".join(
            [i.split("@")[0] for i in self.db['standuppers']]
            ))

    def buscar_ultimas_palabras(self, quien):
        fp = open(
                LOG_DEST,
                "r"
                )
        for linea in reversed(fp.readlines()):
            if linea.find("<%s>" % quien) >= 0:
                return linea

    def identificacion_nickserv(self):
        """
        Se identifica en nickserv
        """
        self.identify(self.db['nickservpass'])

    def conectarse(self):
        self.connect(self.db['ircnet'])

    def usuario_autorizado(self, event):
        nickhandle = "%s@%s" % (
                event.source,
                event.host
                )
        return nickhandle in self.db['authusers'] or \
               nickhandle in self.db['adminusers']

    def usuario_admin(self, event):
        nickhandle = "%s@%s" % (
                event.source,
                event.host
                )

        return nickhandle in self.db['adminusers']

    def decir(self, *args, **kwargs):
        try:
           destino = kwargs['event'].source,
        except KeyError:
            destino = ""

        if len(destino) == 1:
            destino = destino[0]

        if not self.mudo:
            self.send_message(
                    self.db['canal'],
                    "%s: %s" % (
                        destino,
                        kwargs['mensaje']
                        )
                    )

    def comando_a_funcion(self, comando):
        """
        Convierte un string que representa un comando en un nombre
        de funcion bien formado, de acuerdo a:

        Converte ".<nombre>" en "_TrelloBot__c_<nombre>"
        """
        if not comando.startswith("."):
            return False

        return "_TrelloBot__c_%s" % comando[1:]
    # Helpers }}}

    # Comandos del bot {{{

    def __c_sdpbg(self, *args, **kwargs):
        """Imprime el banner de comienzo de standup

        Avisa a los participantes de la standup y coloca el banner de inicio

        """
        self.decir(mensaje="Standup! %s" % ", ".join(
                    [i.split("@")[0] for i in self.db['standuppers']]
                    )
                )
        self.decir(mensaje=BANNER_STANDUP_BEGIN)

    def __c_sdpend(self, *args, **kwargs):
        """Imprime el banner de final de standup
        Imprime el banner de final de standup
        TODO: Buen punto para tomar el log y enviarlo a alguna parte

        """
        self.decir(mensaje=BANNER_STANDUP_END)

    # decorador: needs event
    def __c_config(self, *args, **kwargs):
        """Muestra las variables de configuracion del bot"""
        for e,v in self.db.iteritems():

            # protejo informacion sensible
            if e in ('adminusers','nickservpass'):
                continue

            self.decir(
                    mensaje="%s -> %s" % (e, v),
                    event=kwargs['event']
                    )

    def extrae_primer_linea_docstring(self, funcion):
        """Extrae la primera linea del docstring de la funcion indicada"""
        fp = getattr(self, funcion)
        docstring = fp.__doc__
        dstrings = docstring.split("\n")
        return dstrings[0]

    # decorador: needs event
    def __c_ayuda(self, *args, **kwargs):
        """Muestra un texto de ayuda para cada comando del bot, y como se usa"""
        for i in [e for e in dir(self) if e.startswith("_TrelloBot__c_")]:
            self.decir(
                    mensaje=".%s -> %s" % (
                        str(i)[14:],
                        self.extrae_primer_linea_docstring(i)
                        ),
                    event=kwargs['event']
                    )
            # para evitar baneo del ircserver
            time.sleep(0.5)


    # decorador: needs event
    def __c_last(self, *args, **kwargs):
        """Lo ultimo que dijo alguien en este canal hoy. Uso: .last <nick>

        Se puede extender para buscar en logs anteriores

        Parametros:

        nick: El nick a buscar
        """

        if len(args) < 1:
            self.decir(
                    mensaje="A quien buscas piscui?",
                    event=kwargs['event']
                    )
            return

        ultimas_palabras = self.buscar_ultimas_palabras(
                args[0]
                )

        if not ultimas_palabras:
            self.decir(
                    mensaje="Hoy no he visto a %s" % args['0'],
                    event=kwargs['event']
                    )
        else:
            self.decir(
                mensaje="Lo ultimo que supe es:",
                event=kwargs['event']
                )

            self.decir(
                mensaje=ultimas_palabras.strip(),
                event=kwargs['event']
                )


    # decorador: needs event
    def __c_add_standup(self, *args, **kwargs):
        """Te agrega a la lista de standup
        Agrega el nick del usuario que lo solicita a la lista de
        notificacion de standup
        """
        nickhandle = "%s@%s" % (
                kwargs['event'].source,
                kwargs['event'].host
                )

        sduppers = self.db['standuppers']

        if nickhandle in sduppers:
            self.decir(
                    event=kwargs['event'],
                    mensaje="%s ya esta en la lista" % nickhandle
                    )
            return

        # si no esta, lo agrego
        sduppers.add(nickhandle)
        self.db['standuppers'] = sduppers
        self.db.sync()

        self.decir(
                mensaje="Agregado %s a la lista de standup" % nickhandle,
                event=kwargs['event']
                )

    # decorador: needs event
    def __c_del_standup(self, *args, **kwargs):
        """Te elimina de la lista de standup
        Elimina el nick del usuario que lo solicita a la lista de
        notificacion de standup
        """
        nickhandle = "%s@%s" % (
                kwargs['event'].source,
                kwargs['event'].host
                )

        sduppers = self.db['standuppers']

        if nickhandle not in sduppers:
            self.decir(
                    mensaje="%s NO esta en la lista" % nickhandle,
                    event=kwargs['event']
                    )
            return

        # si esta, lo elimino
        sduppers.remove(nickhandle)

        self.db['standuppers'] = sduppers
        self.db.sync()

        self.decir(
                mensaje="Eliminado %s de la lista de standup" % nickhandle,
                event=kwargs['event']
                )

    # decorador: needs event
    # decorador: needs admin
    def __c_add_auth(self, *args, **kwargs):
        """Agrega usuario al bot. Uso: .add_auth <nick@host>
        Agrega el nick de un usuario a la lista de
        autorizados a operar el bot
        """
        if len(args) < 1:
            self.decir(
                    mensaje="A quien buscas piscui?",
                    event=kwargs['event']
                    )
            return

        adduser = args[0]

        if "@" not in adduser:
            self.decir(
                    mensaje="Formato de username: <nick>@<host>",
                    event=kwargs['event']
                    )

        authusers = self.db['authusers']

        if adduser in authusers:
            self.decir(
                    mensaje="%s ya esta en la lista" % adduser,
                    event=kwargs['event']
                    )
            return


        # si no esta, lo agrego
        authusers.add(adduser)
        self.db['authusers'] = authusers
        self.db.sync()

        self.decir(
                mensaje="Agregado %s a la lista de authusers" % (adduser),
                event=kwargs['event']
                )

    # decorador: needs event
    # decorador: needs admin
    def __c_del_auth(self, *args, **kwargs):
        """Elimina un usuario del bot. Uso: .del_auth <nick@host>
        Elimina el nick del usuario que lo solicita a la lista de
        notificacion de standup
        """
        if len(args) < 1:
            self.decir(
                    mensaje="A quien buscas piscui?",
                    event=kwargs['event']
                    )
            return

        deluser = args[0]

        if "@" not in deluser:
            self.decir(
                    mensaje="Formato de username: <nick>@<host>",
                    event=kwargs['event']
                    )

        authusers = self.db['authusers']

        if deluser not in authusers:
            self.decir(
                    mensaje="%s NO esta en la lista" % deluser,
                    event=kwargs['event']
                    )
            return


        # si esta, lo elimino
        authusers.remove(deluser)

        self.db['authusers'] = authusers
        self.db.sync()

        self.decir(
                mensaje="Eliminado %s a la lista de authusers" % (deluser),
                event=kwargs['event']
                )

    def __c_mudo(self, *args, **kwargs):
        """Enmudece al bot"""
        self.decir(mensaje="Me quedo muzza...")
        self.mudo = True

    def __c_habla(self, *args, **kwargs):
        """Desenmudece al bot"""
        self.mudo = False
        self.decir(mensaje="Me estaba mordiendo la lengua...")

    # decorador: needs admin
    def __c_set(self, *args, **kwargs):
        """Asigna una variable de configuracion. Uso: .set <variable> <valor>
        """
        # TODO: Esto esta mal y es peligroso
        self.db[args[0]] = eval(args[1])
        self.db.sync()
        self.decir(mensaje="Asignacion exitosa")

    # Comandos del bot }}}

    # triggers de la libreria IRC {{{

    def on_welcome(self, event):
        self.join(self.db['canal'])


    def on_channel_message(self, event):
        self.loguear_mensaje(event)

        message = event.message.split()
        command = message.pop(0).lower()

        if not command.startswith("."):
            # no es un comando, continuo silenciosamente
            self.buscar_tarjeta_trello(event)
            return

        if not self.usuario_autorizado(event):
            if self.db['verboso']:
                self.decir(mensaje="No esta autorizado para comandarme!")
            return

        try:

            nfunc = self.comando_a_funcion(command)
            fp = getattr(self, nfunc)

        except AttributeError:
            if self.db['verboso']:
                self.decir(
                        mensaje="%s: Comando no reconocido. Intente .ayuda" % command
                        )
            return

        except TypeError:
            # No se pudo interpretar el parametro a getattr
            if self.db['verboso']:
                self.decir(
                        mensaje="%s: Comando mal formado" % command
                        )
            return

        try:
            fp(*message, event=event)
        except Exception, e:
            print "?=?????????????????????EXCEPTION"
            print e

    # triggers de la libreria IRC }}}


if __name__ == "__main__":
    LOGGING_DATE_FORMAT     = '%Y%m%d'
    logging.basicConfig(
            level = logging.DEBUG,
            datefmt=LOGGING_DATE_FORMAT
            )
    root_logger = logging.getLogger('')
    logger = logging.handlers.TimedRotatingFileHandler(LOG_DEST,
            "midnight", 1)
    root_logger.addHandler(logger)
    # Create an instance of the bot
    trello_bot = TrelloBot()
    trello_bot.conectarse()
    trello_bot.identificacion_nickserv()

    # Start running the bot
    trello_bot.start()

# vim: foldmethod=marker ts=4 sw=4 expandtab
