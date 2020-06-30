import paho.mqtt.client as paho
import logging
import time
import random
import socket                                   #########THCP FUNCIONA SEGÚN PRUEBAS REALIZADAS ENVIANDO ARCHIVOS AL MISMO CLIENTE
import threading #Concurrencia con hilos        #########POR ALGUNA RAZÓN DESCONOCIDA NO FUNCIONÁ A TERCEROS SEGÚN PRUEBAS, SE BUSCÓ EXHAUSTIVAMENTE PERO NO 
import binascii                                 #########SE ENCONTRÓ LA RAZÓN Y EL PROGRMA NO DIÓ NINGUN ERROR
import os
import sys
from datetime import datetime
from brokerData_01 import * #Informacion de la conexion
from clientTCP import *

#USER_ID = "201503914"
#TOPIC_USER_ID="comandos/25/201503914"

'''
--------------------------PJAM INICIO Configuración_01 Logging-------------------------------------------------------------------
'''

#PJAM Configuracion inicial de logging
logging.basicConfig(
    level = logging.INFO, 
    format = '[%(levelname)s] (%(processName)-10s) %(message)s'
    )

'''
--------------------------PJAM FINAL Configuración_01 Logging-------------------------------------------------------------------
'''

class InicioMQTT(object):

    def  __init__(self,salas_file,ack_alive):
        #self.salas_file = salas_file
        self.ack_alive = ack_alive
        logging.debug("init")
        self.bandera_recepcion_trama = 0
        self.trama_entrante = b''
        self.tamaño_trama = 0

        self.tcp_cliente_1 = TCP_CLIENT()

        host=MQTT_HOST
        puerto=MQTT_PORT

        #PJAM Inicia la configuración del cliente MQTT
        self.__setupMQTTClient(host,puerto)

        #PJAM Suscripción a topic
        #self.Configuracion()
        self.__mqttSubscribe(salas_file)

        #self.FUNCION()

    
    '''
    -------------------PJAM LECTURA TEXTO PLANO------------------------------------------------------------------
    '''
    def Configuracion(self):
        salas_file = [] #PJAM lista que guardará el usuario y las salas
        path_to_script = os.path.dirname(os.path.abspath(__file__)) #PJAM instrucción que devuelve la dirección de este archivo
        usuario_conf = os.path.join(path_to_script, "usuario.txt")  #PJAM isntrucción que une la dirección con el nombre del documento .txt
        f= open(usuario_conf, "r")
        for line in f:
            salas_file.append(line)
        f.close()

        salas_conf = os.path.join(path_to_script, "salas.txt")
        f= open(salas_conf, "r")
        for line in f:
            salas_file.append(line)
        f.close()
        for i in range(len(salas_file)):
            salas_file[i] = salas_file[i].replace('\n', '') #PJAM remplaza los saltos de linea con espacio vacío
            if salas_file[i]=="":
                del salas_file[i]
        logging.debug(salas_file)                                                                                                                                                                                                                        
        self.__mqttSubscribe(salas_file)

    '''
    -------------------PJAM INICIO Configuración del cliente MQTT------------------------------------------------------------------
    '''

    def __setupMQTTClient(self,MQTT_HOST,MQTT_PORT):

        self.client = paho.Client(clean_session=True) #PJAM Nueva instancia de cliente
        self.client.on_connect = self.on_connect #PJAM Se configura la funcion "Handler" cuando suceda la conexion
        self.client.on_publish = self.on_publish #PJAM Se configura la funcion "Handler" que se activa al publicar algo
        self.client.on_message = self.on_message
        self.client.username_pw_set(MQTT_USER, MQTT_PASS) #PJAM Credenciales requeridas por el broker
        self.client.connect(host=MQTT_HOST, port = MQTT_PORT) #PJAM Conectar al servidor remoto

    '''
    -------------------PJAM INICIO Configuración Subscripcion MQTT-----------------------------------------------------------------
    '''
    #Función para subscribirse a cada uno de los grupos sacados del archivo salas, subscribirse a los audios y al propio tema
    def __mqttSubscribe(self, salas_file, qos=2):
        self.salas_file = salas_file #globalizamos lista para utilizarla en el resto de la clase
        #TOPIC="usuarios/25"+salas_file[0]
        #self.client.subscribe((TOPIC, qos))
        for i in range(len(salas_file)):
            if i ==0:
                TOPIC="comandos/25/"+salas_file[0]
                self.client.subscribe((TOPIC, qos))
                self.TOPIC_USER_ID=TOPIC    #Guarda el tema de subscripcion comandos/25/usuario
                logging.debug(TOPIC) 
                TOPIC="usuarios/25/"+salas_file[0]
                self.USER_ID = salas_file[0]    #Guarda el numeral de este usuario
            else:
                TOPIC="salas/25/"+salas_file[i]
            self.client.subscribe((TOPIC, qos))
            logging.debug(TOPIC)    
        for i in range(len(salas_file)):
            if i ==0:
                TOPIC="audio/25/"+salas_file[0]
            else:
                TOPIC="audio/25/"+salas_file[i]
            self.client.subscribe((TOPIC, qos))
            logging.debug(TOPIC)        


    '''
    -------------------PJAM Función publicación MQTT-----------------------------------------------------------------
    '''

    #PJAM Invoke one-shot publish to MQTT default broker
    def __mqttPublish(self,topic,data):
        self.client.publish(topic=topic,payload=data,qos=1)

    def mqttPublish(self,topic,data):
        self.client.publish(topic=topic,payload=data,qos=1)
    '''
    -------------------PJAM publicación MQTT----------------------------------------------------------------
    '''
    #PJAM Handler en caso se publique satisfactoriamente en el broker MQTT
    def on_publish(self,client, userdata, mid): 
        publishText = "Publicacion satisfactoria"
        #logging.debug(publishText)

    '''
    -------------------PJAM Recepción mensajes MQTT----------------------------------------------------------------
    '''

    #PJAM Callback que se ejecuta cuando llega un mensaje al topic suscrito
    def on_message(self,client, userdata, msg):
        #end="end"
        #cod=end.encode()
        tema_comandos = "comandos/25/"+self.salas_file[0]
        #Se muestra en pantalla informacion que ha llegado
        logging.debug("Ha llegado el mensaje al topic: " + str(msg.topic))
        logging.debug("El contenido del mensaje es: " + str(msg.payload))

        #Recepción_Audio(msg.topic,msg.payload,self.salas_file)
        if self.bandera_recepcion_trama == 0: 
            if str(msg.topic) == tema_comandos:
                entrada = str(msg.payload)
                mensaje_res = entrada.split("$")
                instruccion = mensaje_res[0]
                if instruccion[-1] == "5":
                    user_id_crudo=mensaje_res[1]    ##PJAM Se guarda el valor del carné pero tiene ' entonces se debe quitar
                    USER_ID_ACK=user_id_crudo.split("'")    ##PJAM  separa el ' del valor del carné
                    if USER_ID_ACK[0]==self.salas_file[0]:  ##PJAM Verifica que el ACK contenga el USER_ID de esta cuenta
                        #logging.debug("ACK RECIVIDO")
                        ack_alive.ACK_Alive(sumando=-1)
                elif instruccion[-1] == "6":
                    user_id_crudo=mensaje_res[1]    ##PJAM Se guarda el valor del carné pero tiene ' entonces se debe quitar
                    USER_ID_ACK=user_id_crudo.split("'")    ##PJAM  separa el ' del valor del carné
                    if USER_ID_ACK[0]==self.salas_file[0]:  ##PJAM Verifica que el ACK contenga el USER_ID de esta cuenta
                        logging.debug("MENSAJE OK RECIBIDO")
                        bandera_envio_recepcion = 1
                        duracion_audio_a_recibir = 0
                        #self.tcp_cliente_1 = TCP_CLIENT(self.tcp)
                        self.tcp_cliente_1.cliente_tcp_recepcion_envio(self.usuario_conf,bandera_envio_recepcion,duracion_audio_a_recibir)
                elif instruccion[-1] == "7":
                    user_id_crudo=mensaje_res[1]    ##PJAM Se guarda el valor del carné pero tiene ' entonces se debe quitar
                    USER_ID_ACK=user_id_crudo.split("'")    ##PJAM  separa el ' del valor del carné
                    if USER_ID_ACK[0]==self.salas_file[0]:  ##PJAM Verifica que el ACK contenga el USER_ID de esta cuenta
                        logging.debug("MENSAJE NO RECIBIDO")
                        logging.error("EL USUARIO O USUARIOS OBJETIVOS NO SE ENCUENTRAN ACTIVOS")
                elif instruccion[-1] == "2":
                    self.clear()
                    logging.info("MENSAJE FFR RECIBIDO")
                    duracion_audio_recibir_crudo = mensaje_res[-1]
                    duracion_audio_recibir = duracion_audio_recibir_crudo.split("'")
                    logging.info("PREPARANDO PARA RECIBIR AUDIO DE : "+ str(mensaje_res[1]))
                    logging.info(str(duracion_audio_recibir[0]))
                    bandera_envio_recepcion = 2
                    duracion_audio_a_recibir = duracion_audio_recibir[0]
                    logging.info("LLEGA ANTES DE ENVIAR")
                    self.tcp_cliente_1.cliente_tcp_recepcion_envio(self.usuario_conf,bandera_envio_recepcion,duracion_audio_a_recibir)
                else:
                    pass 
            for i in range(len(self.salas_file)):
                if i ==0:
                    TOPIC="audio/25/"+self.salas_file[0]
                    TOPIC_1="usuarios/25/"+self.salas_file[0]
                    if (str(msg.topic))== TOPIC:
                        logging.info("PREPARANDO PARA RECIBIR AUDIO DE USUARIO PERSONAL")
                        self.tamaño_trama=int(msg.payload)
                        self.bandera_recepcion_trama = 1
                        logging.debug(self.tamaño_trama)
                        break
                    elif (str(msg.topic))== TOPIC_1:
                        logging.info("MENSAJE ENTRANTE DE USUARIO PERSONAL")
                        logging.info(str(msg.payload))
                        break
                else:
                    TOPIC="audio/25/"+self.salas_file[i]
                    TOPIC_1="salas/25/"+self.salas_file[i]
                    if (str(msg.topic))== TOPIC:
                        logging.info("PREPARANDO PARA RECIBIR AUDIO DE SALA")
                        self.tamaño_trama=int(msg.payload)
                        self.bandera_recepcion_trama = 1
                        break
                    elif (str(msg.topic))== TOPIC_1:
                        logging.info("MENSAJE ENTRANTE DE SALA")
                        logging.info(str(msg.payload))
                        break
            

    '''
    -------------------PJAM conexión broker MQTT----------------------------------------------------------------
    '''

    #PJAM Handler en caso suceda la conexion con el broker MQTT
    def on_connect(self,client, userdata, flags, rc): 
        connectionText = "CONNACK recibido del broker con codigo: " + str(rc)
        logging.info(connectionText)

    '''
    -------------------PJAM loop MQTT----------------------------------------------------------------
    '''
    def Client_loop(self):
        inicio_loop_cliente = threading.Thread(name = 'LOOP CLIENT_START',
                                            target = self.client.loop_start(),
                                            args = (),
                                            daemon = True
                                            )
        inicio_loop_cliente.start()

    '''
    -------------------RMJD Función CLEAR-----------------------------------------------------------------
    '''

    def clear(self):
        os.system('clear')

    #RMJD Creando las funciones integrantes del menu

    '''
    -------------------RMJD Función VOZ-----------------------------------------------------------------
    '''

    def voz(self,duracion,userID): #RMJD lugar donde se graba el mensaje de voz a enviar
        path_to_script = os.path.dirname(os.path.abspath(__file__)) #PJAM instrucción que devuelve la dirección de este archivo
        self.usuario_conf = os.path.join(path_to_script, "prueba_02_examen02.wav")  #PJAM isntrucción que une la dirección con el nombre del documento .txt

        logging.info('Comenzando grabacion')
        os.system('arecord -d' + str(duracion) + ' -f U8 -r 8000 '+ self.usuario_conf)
        tamaño_audio = os.stat(self.usuario_conf).st_size
        logging.debug(tamaño_audio)
        messageAlive = "\x03$" + str(userID) + "$" + str(tamaño_audio)
        logging.debug(userID)
        logging.debug(self.TOPIC_USER_ID)
        self.mqttPublish(self.TOPIC_USER_ID,messageAlive)
        #self.Envio_Voz(userID)

    '''
    -------------------RMJD Función EXIT-----------------------------------------------------------------
    '''
     
    def exit(self): #RMJD funcion que sale de la interfaz de usuario
        self.clear()
        input("\nCerrando la sesion, presione Enter para finalizar")
        logging.warning("Desconectando del broker MQTT...")
        self.client.loop_stop() 
        self.client.disconnect()
        logging.info("Se ha desconectado del broker. Saliendo...")
        sys.exit()



class clase_menu(object):
    def  __init__(self,mqtt):
        self.mqtt = mqtt
        
    '''
    -------------------RMJD Función MENU-----------------------------------------------------------------
    '''

    def menu(self): #RMJD 
        self.clear()
        logging.info("1. Enviar Texto")
        logging.info("2. Enviar mensaje de voz")
        logging.info("3. Exit")
        choice = input("\nIngrese la opcion: ")

        if choice == "1":
            self.enviarTexto()
        elif choice == "2":
            self.enviarVoz()
        elif choice == "3":
            self.mqtt.exit()

        else:
            self.clear()
            self.errorOpcion()
            self.menu()

    '''
    -------------------RMJD Función DESTINO-----------------------------------------------------------------
    '''

    def destino(self): #RMJD Imprime las opciones de destino
        logging.info("\nEscoja destino:\n")
        logging.info("a. Enviar a usuario ")
        logging.info("b. Enviar a sala")
        logging.info("c. Regresar a menu\n")

    '''
    -------------------RMJD Función CLEAR-----------------------------------------------------------------
    '''

    def clear(self):
        os.system('clear')

    '''
    -------------------RMJD Función ERROR-----------------------------------------------------------------
    '''

    def errorOpcion(self): #RMJD error que aparece solo si no se ingresa un valor valido
        self.clear()
        logging.info("No ha ingresado una opcion valida.  Intente de nuevo")

    '''
    -------------------RMJD Función ENVIAR TEXTO-----------------------------------------------------------------
    '''

    def enviarTexto(self): # RMJD funcion correspondiente a enviar un texto
        self.clear()
        logging.info ("\nEnviar mensaje de Texto")
        self.destino()
        choice2 = input()

        if choice2 == "a":
            logging.info("\nEnviar mensaje privado a: ")
            userID = input() #Variable donde se ingresa el ID del usuario
            self.mensaje()
            topic="usuarios/25/"+str(userID)
            self.mqtt.mqttPublish(topic,self.msj)
            logging.info("\nMensaje enviado a " + userID)
            self.finalOpcion()
    
        elif choice2 == "b":
            logging.info("\nEnviar mensaje a la sala: ")
            salaID = input() #Variable que guarda el ID de la sala destino
            self.mensaje()
            topic="salas/25/"+str(salaID)
            self.mqtt.mqttPublish(topic,self.msj)
            logging.info("\nMensaje enviado a " + salaID)
            self.finalOpcion()

    
        elif choice2 == "c":
            self.menu()

        else:
            self.errorOpcion()
            self.enviarTexto()

    '''
    -------------------RMJD Función MENSAJE-----------------------------------------------------------------
    '''

    def mensaje(self): #RMJD lugar donde se ingresa el mensaje a enviar
        logging.info("Escriba el mensaje que desea enviar")
        self.msj = input()
        logging.info("El mensaje enviado es: \n" + self.msj)

    '''
    -------------------RMJD Función OPCION FINAL-----------------------------------------------------------------
    '''

    def finalOpcion(self): #RMJD metodo donde el usuario escoge si regresa o no al menu
        logging.info("Ingrese:\n 1. Salir a menu \n 2. Cerrar chat")
        p = input()

        if p == "1":
            self.menu()

        elif p == "2":
            self.mqtt.exit()

        else:
            self.errorOpcion()
            self.finalOpcion()

    '''
    -------------------RMJD Función ENVIAR VOZ-----------------------------------------------------------------
    '''

    def enviarVoz(self): # RMJD funcion correspondiente a enviar mensaje de voz
        self.clear()
        logging.info ("\nEnviar mensaje de Voz")
        self.destino()
        choice2 = input()

        if choice2 == "a":
            logging.info("\nEnviar mensaje privado a: ")
            userID = input() #Variable donde se ingresa el ID del usuario
            topic=str(userID)
            logging.info("\nIngrese duracion en segundos")
            duracion = input()# Variable que guarda la duracion del mensaje de voz
            self.mqtt.voz(duracion,topic)
            logging.info("\nMensaje enviado a " + userID)
            self.finalOpcion()

        elif choice2 == "b":
            logging.info("\nEnviar mensaje a la sala: ")
            salaID = input() #Variable que guarda el ID de la sala destino
            topic=str(salaID)
            logging.info("\nIngrese duracion en segundos")
            duracion = input()# Variable que guarda la duracion del mensaje de voz
            self.mqtt.voz(duracion,topic)
            logging.info("\nMensaje enviado a " + salaID)
            self.finalOpcion()

        elif choice2 == "c":
            self.menu()
        else:
            self.errorOpcion()
            self.enviarVoz()

'''
    -------------------PJAM Clase para la verificion de ACK y Alive-----------------------------------------------------------------
'''

class Verificacion_ACK_Alive(object):       #Clase que verifica si para cada Alive enviado exite un ACK recibido 
    def  __init__(self):
        self.contador=0                 #Llevará la cuenta de cuantos Alive existen sin contestar

    def ACK_Alive(self,sumando):
        if sumando == -1:                   #Si recibe un -1 quiere decir que se recibió un ACK
            sumando = -(self.contador)      
            self.contador=self.contador+sumando     #Se pone el contador a 0
            #logging.debug(self.contador)
        else:
            self.contador=self.contador+sumando     #Sumara los Alive enviados sin contestación de ACK
            #logging.debug(self.contador)
            if self.contador > 3 and self.contador < 202:   
                TIME_SLEEP(tiempo=0.1)
            elif self.contador > 203:                  ##Si el contador llega a 20 segundos entonces se cierra el programa
                logging.critical("SERVIDOR NO RESPONDE")
                sys.exit()
            else:
                TIME_SLEEP(tiempo=2)

'''
    -------------------PJAM Clase para la Rediracción hacia tcp-----------------------------------------------------------------
'''
class TCP_CLIENT(object):
    def  __init__(self):
        self.envio = Cliente_Tcp()

    def cliente_tcp_recepcion_envio(self,direccion_audio,bandera_envio_recepcion,duracion_audio_recibir):
        logging.info("ENTRA A CLIENTE_TCP_RECEPCION_ENVIO")
        self.envio.configuracion_socket(direccion_audio,int(bandera_envio_recepcion),int(duracion_audio_recibir))

'''
-------------------PJAM LECTURA TEXTO PLANO------------------------------------------------------------------
 '''
def Configuracion():
    salas_file = [] #PJAM lista que guardará el usuario y las salas
    path_to_script = os.path.dirname(os.path.abspath(__file__)) #PJAM instrucción que devuelve la dirección de este archivo
    usuario_conf = os.path.join(path_to_script, "usuario.txt")  #PJAM isntrucción que une la dirección con el nombre del documento .txt
    f= open(usuario_conf, "r")
    for line in f:
        salas_file.append(line)
    f.close()

    salas_conf = os.path.join(path_to_script, "salas.txt")
    f= open(salas_conf, "r")
    for line in f:
        salas_file.append(line)
    f.close()
    for i in range(len(salas_file)):
        salas_file[i] = salas_file[i].replace('\n', '') #PJAM remplaza los saltos de linea con espacio vacío
        if salas_file[i]=="":
            del salas_file[i]
    logging.debug(salas_file)                                                                                                                                                                                                                        
    return(salas_file)

'''
-------------------PJAM Funcion ALIVE----------------------------------------------------------------
'''
def PubAlive(USER_ID,TOPIC_USER_ID,mqtt,ack_alive):
    while 1:
        messageAlive = "\x04$" + USER_ID
        mqtt.mqttPublish(TOPIC_USER_ID,messageAlive)
        #logging.debug("MENSAJE ALIVE ENVIADO")
        ack_alive.ACK_Alive(sumando=1)

def TIME_SLEEP(tiempo):
    time.sleep(tiempo)

'''
-------------------PJAM HILO PRINCIPAL ----------------------------------------------------------------
'''
salas_file = Configuracion()    ##PJAM extrea del documento de texto el usuario y las salas

USER_ID=salas_file[0]           ##PJAM guarda en USER_ID el valor del asuario
TOPIC_USER_ID = "comandos/25/"+salas_file[0]    ##Crea el topic para la comunicación con el broker

ack_alive = Verificacion_ACK_Alive()

mqtt = InicioMQTT(salas_file,ack_alive)       ##Inicia la configuración del MQTT
mqtt.Client_loop()                  ##Incia el loop para recibir mensajes del broker
    
demonio_alive = threading.Thread(name = 'ALIVE',
                        target = PubAlive,
                        args = (USER_ID,TOPIC_USER_ID,mqtt,ack_alive),
                        daemon = True
                        )
demonio_alive.start()
logging.debug("INICIO MENSAJES ALIVE")

interfaz = clase_menu(mqtt)

while 1:
    interfaz.menu()

