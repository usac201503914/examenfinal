import paho.mqtt.client as paho #PJAM libreria para MQTT
import logging                  
import time
import random
import socket       #PJAM Libreria para el uso de TCP
import threading    #PJAM Concurrencia con hilos
import binascii
import os           #PJAM Libreria que permite la utilización de la consola
import sys          
from datetime import datetime
from brokerData_01 import * #PJAM Informacion de la conexion
from serverTCP import *     #PJAM Documento que se encarga del servidor TCP así como del manejo del audio


'''
--------------------------PJAM INICIO Configuración_01 Logging-------------------------------------------------------------------
'''

#PJAM Configuracion inicial de logging
logging.basicConfig(
    level = logging.DEBUG,           ##PJAM Para la version final los únicos mensajes leibles son los de nivel INFORMACIÓN
    format = '[%(levelname)s] (%(processName)-10s) %(message)s'
    )

'''
--------------------------PJAM FINAL Configuración_01 Logging-------------------------------------------------------------------
'''

class InicioMQTT(object):

    def  __init__(self,salas_file,alv,hilo):
        self.alv=alv                ##PJAM Constante que representa la funcion encargada de la verificación y control de los alive, esto con el propósito de poder llamarlo en esta clase
        self.hilo = hilo            ##PJAM Constante que representa la función que se encarga de los demonios que cuentan periodos ALIVE 
        self.tamaño_trama = 0       ##PJAM Variable que no tiene propósito, se dejó ya que quitarla representaba una serie de cambios extensos

        self.server = servidor_tcp()
        self.conf_tcp_mqtt = conf_tcp()

        host=MQTT_HOST              #PJAM Variable exportada del documento broker donde se encuentra constantes del BrokerMQTT
        puerto=MQTT_PORT            #PJAM Variable exportada del documento broker donde se encuentra constantes del BrokerMQTT

        self.__setupMQTTClient(host,puerto)     #PJAM Inicia la configuración del cliente MQTT

        self.__mqttSubscribe(salas_file)        ##PJAM Función para la subscripción de topics en el broker

    def variables(self,no_ok):      #PJAM Función para la introducción de constantes que representan clases exteriores de utilidad
        self.no_ok = no_ok          #PJAM constante de la función que verifica si un usuario esta conectado o no y responde con un OK o un NO

    
    '''
    -------------------PJAM INICIO Configuración del cliente MQTT------------------------------------------------------------------
    '''

    def __setupMQTTClient(self,MQTT_HOST,MQTT_PORT):

        self.client = paho.Client(clean_session=True)       #PJAM Nueva instancia de cliente
        self.client.on_connect = self.on_connect            #PJAM Se configura la funcion "Handler" cuando suceda la conexion
        self.client.on_message = self.on_message
        self.client.username_pw_set(MQTT_USER, MQTT_PASS)       #PJAM Credenciales requeridas por el broker
        self.client.connect(host=MQTT_HOST, port = MQTT_PORT)       #PJAM Conectar al servidor remoto

    '''
    -------------------PJAM INICIO Configuración Subscripcion MQTT-----------------------------------------------------------------
    '''
    
    def __mqttSubscribe(self, salas_file, qos=2):       #PJAM Función para subscribirse a cada uno de los grupos sacados del archivo salas, 
        for i in range(len(salas_file)):                #PJAM así como subscribirse a cada uno de los usuarios
            TOPIC="comandos/25/"+salas_file[i]          
            self.client.subscribe((TOPIC, qos))         #PJAM proceso de subscripcion
            logging.debug(TOPIC)        


    '''
    -------------------PJAM Función publicación MQTT-----------------------------------------------------------------
    '''                       
    def __mqttPublish(self,topic,data):                         #PJAM Invoke one-shot publish to MQTT default broker
        self.client.publish(topic=topic,payload=data,qos=1)     #PJAM esta función solamente es alcanzable para funciones dentro de la clase
        logging.info("FRR SI FUE ENVIADO")

    def mqttPublish(self,topic,data):                              ##PJAM Invoke one-shot publish to MQTT default broker
        self.client.publish(topic=topic,payload=data,qos=1)         #PJAM esta función es alcanzable para funciones fuera de la clase
    
    '''
    -------------------PJAM Recepción mensajes MQTT----------------------------------------------------------------
    '''
    def on_message(self,client, userdata, msg):                 #PJAM Callback que se ejecuta cuando llega un mensaje al topic suscrito
        logging.debug("Ha llegado el mensaje al topic: " + str(msg.topic))      #PJAM Se muestra en pantalla informacion que ha llegado
        logging.debug("El contenido del mensaje es: " + str(msg.payload))       #PJAM Se muestra en un nivel debug, si se desea verlo cambiar de INFO a DEBUG
                                                                                #PJAM en linea 23
        
        entrada = str(msg.payload)                          #PJAM Separación del mensaje de entrada
        mensaje_res = entrada.split("$")                    #PJAM La lista mensaje_res almacena la trama ingresada como mensaje
        instruccion = mensaje_res[0]                        ##PJAM la variable instrucció contiene el comando a ejecutar
        cliente_en_bruto = str(msg.topic)                   #PJAM guarda el cliente pero aún contiene carácteres que no deseo
        cliente_en = cliente_en_bruto.split('/')            ##PJAM separa la información util de los carácteres
        cliente=cliente_en[-1]                              #PJAM cliente guarda el int con el carné del usuario
        logging.debug("CLIENTE:" + str(cliente))
        
        if instruccion[-1] == "4":                          #PJAM Redireccionamiento hacia la instrucción recivida
            #logging.debug("ALIVE RECIVIDO")                #PJAM PUblicación que informa de los ALIVE recibidos
            user_id_crudo=mensaje_res[1]                    ##PJAM Se guarda el valor del carné pero tiene ' entonces se debe quitar
            USER_ID=user_id_crudo.split("'")                 ##PJAM  separa el ' del valor del carné
            self.ACK(USER_ID[0])                              #PJAM Envia a la función ACK que mandara la confirmación 
        elif instruccion[-1] == "3":
            logging.info("FTR RECIBIDO")
            tamaño_audio_crudo=mensaje_res[-1]                  ##PJAM Se guarda el valor del carné pero tiene ' entonces se debe quitar
            self.Tamaño_audio=tamaño_audio_crudo.split("'")      ##PJAM  separa el ' del valor del carné
            destino_sala_usuario = mensaje_res[1]
            logging.info("TAMAÑO DEL AUDIO: "+ str(self.Tamaño_audio[0]))                     
            logging.debug(destino_sala_usuario)
            self.no_ok.verificacion_usuario_alive(destino_sala_usuario,cliente,self.Tamaño_audio,self.server,self.conf_tcp_mqtt)     #PJAM Envía a la función que verifica que el destinatario este conectado
        else:
            pass 

    '''
    -------------------PJAM Función ACK para usuarios---------------------------------------------------------------
    '''
    def ACK(self,USER_ID):                      #PJAM Función que manda al usuario un comando ACK
        messageAlive = "\x05$" + USER_ID
        topic="comandos/25/" + USER_ID              ##PJAM Se agrega el mensaje con el comando especificado y el topic con el carné del usuario
        self.mqttPublish(topic,messageAlive)        
        alv.usuarios_alive_recibido(USER_ID,self.hilo)  #PJAM Después de mandar el ACK envía a la función para indicarle que el usuario si está conectado 

    '''
    -------------------PJAM Función OK para usuarios----------------------------------------------------------------
    '''
    
    def OK(self,cliente,destino_sala_usuario):      ##PJAM FUnción que envía un OK despues de haber verificado que el destinatario
        bandera_envio_recepcion = 1                  ##PJAM la variable bandera, indicará dentro del documento del server TCP si lo que se requier
        messageAlive = "\x06$" + cliente                ##PJAM es recibir un audio o enviar un audio, "1" es para recibir un audio y "2" es para mandar
        topic="comandos/25/" + cliente                  ##PJAM un audio al destinatario conectado
        self.mqttPublish(topic,messageAlive)
        logging.info("OK ENVIADO") 
        self.conf_tcp_mqtt.configuracion_conf_tcp(self.Tamaño_audio,bandera_envio_recepcion,self.server)
        self.FRR(cliente,destino_sala_usuario)
    '''
    -------------------PJAM Función NO para usuarios----------------------------------------------------------------
    '''                                                                                
    def NO(self,cliente):                           #PJAM FUnción para noticar al usuario que el destinatario no se encuentra conectado 
        messageAlive = "\x07$" + cliente
        topic="comandos/25/" + cliente
        self.mqttPublish(topic,messageAlive)

    '''
    -------------------PJAM Función FRR para destinatarios----------------------------------------------------------------
    ''' 
    def FRR(self,cliente,destino_sala_usuario):             #Función para notificar al destinatario que se requiere para enviarle un archivo 
        bandera_envio_recepcion = 2
        messageAlive = "\x02$" + str(cliente) + "$" + str(self.Tamaño_audio[0])
        topic="comandos/25/" + destino_sala_usuario
        logging.info("CLIENTE _____: " + destino_sala_usuario)
        logging.info("TOPIC __________: "+str(topic))
        self.__mqttPublish(topic,messageAlive)
        logging.info("FRR ENVIADO")                                 ##PJAM Se redirecciona hacia la función que maneja el servidor TCP para que lo vuelva a activar para 
        self.conf_tcp_mqtt.configuracion_conf_tcp(self.Tamaño_audio,bandera_envio_recepcion,self.server)
        #self.server.configuracion_tcp(self.Tamaño_audio,bandera_envio_recepcion)      ##PJAM poder enviar el audio al destinatario 

      
    '''
    -------------------PJAM conexión broker MQTT----------------------------------------------------------------
    '''

    
    def on_connect(self,client, userdata, flags, rc):                   #PJAM Handler en caso suceda la conexion con el broker MQTT
        connectionText = "CONNACK recibido del broker con codigo: " + str(rc)
        logging.info(connectionText)

    '''
    -------------------PJAM loop MQTT----------------------------------------------------------------
    '''
    def Client_loop(self):                                                  ##PJAM Función con el objetivo de activar un demonio el cual será el loop del broker MQTT
        inicio_loop_cliente = threading.Thread(name = 'LOOP CLIENT_START',  #PJAM para poder tener una recepción constante de mensajes
                                            target = self.client.loop_start(),
                                            args = (),
                                            daemon = True
                                            )
        inicio_loop_cliente.start()                                             #PJAM Se inicia el demonio

'''
    -------------------RMJD Clase VERIFICACIÓN ALIVE-----------------------------------------------------------------
'''
class Verificacion_Alvie(object):
    def  __init__(self,datos_USER_IDS):
        self.datos_USER_IDS = datos_USER_IDS    #PJAM se recibe una lista con los usuarios
        self.almacenamiento_usuarios() 
    '''
    -------------------PJAM Función Alamacenamiento de los Usuario----------------------------------------------------------------
    '''       
    def almacenamiento_usuarios(self):          #PJAM funcion para guardar los usuarios junto con su estado
        estado=-1                               #PJAM variable que añade el estado de usuario -1 = no conectado
        lista=[]
        self.usuarios_conteo_alive =[]             #PJAM lista que guardará listas de usuario y estado
        self.bandera_stop=[] 
        for i in range(len(self.datos_USER_IDS)): 
            self.bandera_stop.append(0) 
            lista.append(self.datos_USER_IDS[i])    #PJAM agrega a lista el usuario 
            lista.append(estado)                    #PJAM agrega a lista el estado del usuario
            self.usuarios_conteo_alive.append(lista)    #PJAM se agrega a la lista definitiva la lista con el usuario y los datos
            lista=[]                                       #PJAM se vacía la lista para volver a empezar el ciclo y almacenar nuevas variables
        logging.debug(self.usuarios_conteo_alive)

    '''
    -------------------PJAM Función Usuarios Alive Recibido----------------------------------------------------------------
    '''  
    def usuarios_alive_recibido(self,USER_ID,hilo):     #PJAM función que verifica si el Alive es válido y cambia el estado de los usuarios
        self.hilo = hilo                                ##PJAM Variable que guarda el hilo demonio para poder llamarlo
        for i in range(len(self.usuarios_conteo_alive)):        #PJAM verificará en la lista donde se encuentra cada usuario si el alive pertenece a este servidor
            if self.usuarios_conteo_alive[i][0] == USER_ID:             #PJAM Si encuentra coincidencia entonces confirma la llegada del alive 
                logging.info("MENSAJE ALIVE RECIBIDO DE:"+str(USER_ID))
                logging.info("MENSAJE ACK ENVIADO A:"+str(USER_ID))
                logging.debug(USER_ID)
                #logging.debug(self.usuarios_conteo_alive[i][1])
                if self.usuarios_conteo_alive[i][1]==-1:        #PJAM el valor "-1" quiere decir inactivo, por lo tanto si estaba inactivo lo configuramos como activo
                    self.usuarios_conteo_alive[i][1]=0          ##PJAM modifca el estado del usuario a activo, esto se sabe si el numero es positivo
                    self.bandera_stop[i] = 1                    #PJAM para cada usuario existe una bandera la cual dentendrá el conteo del hilo al llegar a 3 ciclos alive
                    logging.debug("usuario:"+str(i))            
                    logging.debug(self.usuarios_conteo_alive[i][1])
                    self.hilo.inicio_hilo(i)                    ##PJAM envía a la clase que dará inicio al demonio el número de usuario conectado
                    
                else:
                    a=i                               
                    self.aumento_conteo_alive(-1,a)                 #PJAM Si el usuario ya se encontraba conectado entonces manda un "-1" para poner el conteo de Alive -
                    #logging.debug(self.usuarios_conteo_alive[i][1])            #PJAM no contestados en 0
    '''
    -------------------PJAM Función Aumento conteo Alive----------------------------------------------------------------
    '''  
    def aumento_conteo_alive(self,aumento,i):             #PJAM FUnción que lleva la cuenta de los ALIVE no mandados por cada usuario que se encuentra en linea
        if self.bandera_stop[i] == 1:                   #PJAM Cada usuario cuenta con su bandera, la cual le dice al hilo si ingresar o no, si el usuario se encuentra
            if aumento == -1:                               #PJAM inactivo no tiene sentido llevar un conteo 
                self.usuarios_conteo_alive[i][1]=0          ##PJAM si se recibe Alive entonces el conteo de alives no contestados que tambien indica el estado del usuario, se pone en 0
            else:
                if self.usuarios_conteo_alive[i][1]>=3:         ##PJAM si se cumplen mas de tres ciclos entonces se indica como inactivo el usuario
                    self.usuarios_conteo_alive[i][1]=-1             #PJAM esto poneindolo en -1
                    self.bandera_stop[i]=0                             #PJAM La bandera del usuario se pone en 0 para no volver a entrar a la verificación
                    logging.debug("usuario:"+str(i))
                    logging.debug(self.usuarios_conteo_alive[i][1])
                else:
                    self.usuarios_conteo_alive[i][1]+=1
                    logging.debug("usuario:"+str(i))
                    logging.debug(self.usuarios_conteo_alive[i][1])     #PJAM se va agregando 1 al contador de alives no contestados
        else:
            pass
    '''
    -------------------PJAM Función VIVO O NO----------------------------------------------------------------
    '''
    def vivo_o_no(self,USER_ID):
        bandera_vivo_o_no = "0"
        for i in range(len(self.usuarios_conteo_alive)):        #PJAM verificará en la lista donde se encuentra cada usuario 
            if self.usuarios_conteo_alive[i][0] == USER_ID:             #PJAM Si encuentra coincidencia entonces verifica si esta activo o no
                if self.usuarios_conteo_alive[i][1] == -1:              #PJAM SI el usuario se encuentra desconectado "-1"
                    bandera_vivo_o_no = 0                               #PJAM Se devuelve la bandera en 0
                    return bandera_vivo_o_no                            
                else:   
                    bandera_vivo_o_no = 1                               #PJAM Si el usuario no esta en "-1" quiere decir que esta conectado
                    return bandera_vivo_o_no
            else:
                bandera_vivo_o_no = 0                                   #PJAM Si el usuario no fue encontrado en la lista se devuelve un 0
                return(bandera_vivo_o_no)
            

'''
    -------------------RMJD Clase para la configuracion de los demonios-----------------------------------------------------------------
'''
class HILO_TIEMPO(object):                                                  #PJAM hilo demonio que se encargará de contar periodos ALIVE
    def  __init__(self,alv,cantidad_usuarios):
        self.alv = alv                                                      #PJAM constante que representa la clase Verificacion_Alive
        self.cantidad_usuarios = cantidad_usuarios                          #PJAM constante que nos indica la cantidad de usuarios configurados en el dumento txt
        self.demonio_alive=[]                                               #PJAM lista que contendrá los demonios, existe un demonio para cada usuario y cada usuario cuenta
        self.config_hilo()                                                  #PJAM con una número único identificador

    def config_hilo(self):                                                  #PJAM FUnción para la configuración de los hilos
        for i in range(self.cantidad_usuarios):                     
            self.demonio_alive.append(threading.Thread(name = 'demonio usuario'+str(i),         #PJAM Se agrega a la lista la configuración de un domonio por cada usuario existente
                                    target = contador_alive,
                                    args = (self.alv,i,),
                                    daemon = True
                                    ))

    def inicio_hilo(self,i):                                    #PJAM Función que activará un demonio en específico según el usuario que se encuentre en linea
        self.demonio_alive[i].start()


'''
    -------------------PJAM Clase para la función que actuará como demonio-----------------------------------------------------------------
''' 
class OK_NO_1(object):                                       
    def  __init__(self,alv,mqtt,solo_salas,data_entera):
        self.alv = alv                                      
        self.mqtt=mqtt                                      
        self.solo_salas = solo_salas                        
        self.data_entera = data_entera                      

    def verificacion_usuario_alive_1(self,destino_sala_usuario,cliente,tamaño_audio,server):  
        bandera_vivo_o_no=alv.vivo_o_no(destino_sala_usuario)            
        if bandera_vivo_o_no == 1:                          
            logging.info("OK")
            self.mqtt.OK(cliente,destino_sala_usuario)                       
            self.mqtt.FRR(cliente,destino_sala_usuario)                                 
                                                                                
        else:                                               
            contador_conectados = 0                         
            logging.debug("NO")
            logging.debug(self.solo_salas)
            logging.debug(destino_sala_usuario)
            for i in range(len(self.solo_salas)):                           
                if str(destino_sala_usuario) == str(self.solo_salas[i]):                 
                    logging.debug("ES UNA SALA")
                    for e in range(len(self.data_entera)):                 
                        for o in range(len(self.data_entera[e])):           
                            logging.debug(self.data_entera[e][o])          
                            if str(self.data_entera[e][o])==str(destino_sala_usuario):                        
                                bandera_vivo_o_no_1=alv.vivo_o_no(self.data_entera[e][0])       
                                if bandera_vivo_o_no_1 == 1:
                                    contador_conectados += 1
                                    logging.info("contador_conectados: "+str(contador_conectados))
                                    if contador_conectados == 1:                                     #PJAM Compara para saber si es el primer conectado que detecta
                                        logging.info("OK")                                          #PJAM Si es el primer conectado que detecta manda la confirmación OK al cliente
                                        self.mqtt.OK(cliente,destino_sala_usuario)                       #PJAM se realiza esto para no enviar una confirmación OK al cliente por cada usuario conectado
                                        self.mqtt.FRR(cliente,destino_sala_usuario)
                                    else:                                                           #PJAM Si no es el primer conectado que detecta entonces no manda la confirmación OK 
                                        self.mqtt.FRR(cliente,destino_sala_usuario)                 #PJAM directamente redirecciona hacia el comando FRR para el envío de archivos
                                    break
                                elif bandera_vivo_o_no_1 == 0:                                      #PJAM Si nadie se encuentra conectado en la sala envía una negación NO
                                    logging.info("NO") 
                                    mqtt.NO(cliente)
                        break  

class OK_NO(object):                                                 #PJAM Clase que verifica si los destinatarios se encuentran conectados o no 
    def  __init__(self,alv,mqtt,solo_salas,data_entera):            
        self.alv = alv                                              #PJAM constante que representa la clase Verificacion_Alive
        self.mqtt=mqtt                                              #PJAM constante que representa la clase principal de MQTT
        self.solo_salas = solo_salas                                #PJAM variable que contiene solo las salas existentes en el archivo de configuración
        self.data_entera = data_entera                              #PJAM constante que contiene toda la información de todos los usuarios

    def verificacion_usuario_alive(self,USER_ID,cliente,tamaño_audio,server,conf_tcp):   #PJAM Función que verifica si el usuario destinatario se encuentre en una sala o no esta en linea
        bandera_vivo_o_no=alv.vivo_o_no(USER_ID)                        #PJAM envía el destinatario a una función de la clase Verificación_Alive
        if bandera_vivo_o_no == 1:                                      #PJAM Si el destinatario es un usuario personal y se encuentra en linea entonces regresará un 1
            logging.info("OK")                                            #PJAM Se envía a la función OK para enviarlo y que inicie la transmisión        
            self.mqtt.OK(cliente,USER_ID)                                   ##PJAM despues de haber enviado el OK se manda a notificar
            conf_tcp.hilo_tcp()
            
        else:                                                         #PJAM Si el destinatario es una sala o es un usuario que no esta en linea se recibe una bandera = 0
            contador_conectados = 0
            logging.debug("NO")                                        
            logging.debug(self.solo_salas)
            logging.debug(USER_ID)
            for i in range(len(self.solo_salas)):                      #PJAM Se crea un ciclo para verificar si el destinatario es una sala
                if str(USER_ID) == str(self.solo_salas[i]):             #PJAM Si el destinatario es una sala encontrará coincidencias
                    logging.debug("ES UNA SALA")
                    for e in range(len(self.data_entera)):                  #PJAM Si es una sala entonces se inicia a verificar que usuario se encuentra en ella 
                        for o in range(len(self.data_entera[e])):           #PJAM se crea un ciclo para la verificación de la lista
                            logging.debug(self.data_entera[e][o])                #PJAM la lista data_entera contiene en cada una de sus posiciones una lista con los datos de un usuario 
                            if str(self.data_entera[e][o])==str(USER_ID):           #PJAM Si encuentra que algún usuario esta suscrito a la sala entonces envía su carné
                                bandera_vivo_o_no_1=alv.vivo_o_no(self.data_entera[e][0])   #PJAM a verificar si el usuario está conectado o no lo esta
                                if bandera_vivo_o_no_1 == 1:
                                    contador_conectados += 1
                                    if contador_conectados == 1:                                     #PJAM Compara para saber si es el primer conectado que detecta
                                        logging.info("OK")                                          #PJAM Si es el primer conectado que detecta manda la confirmación OK al cliente
                                        self.mqtt.OK(cliente,USER_ID)                       #PJAM se realiza esto para no enviar una confirmación OK al cliente por cada usuario conectado
                                    else:                                                           #PJAM Si no es el primer conectado que detecta entonces no manda la confirmación OK 
                                        self.mqtt.FRR(cliente,USER_ID)                 #PJAM directamente redirecciona hacia el comando FRR para el envío de archivos
                                    break
                        break
                else:
                    logging.info("NO") 
                    mqtt.NO(cliente)


'''
-------------------RMJD Clase TCP SERVER-----------------------------------------------------------------
'''                 
class TCP_SERVER(object):                                               #PJAM Clase que se encargará del direccionamiento hacia TCP
    #def  __init__(self,tamaño_audio,bandera_envio_recepcion):
    def __init__(self):
        #self.tamaño_audio = tamaño_audio
        #self.servidor_tcp_init(tamaño_audio,bandera_envio_recepcion)
        self.servidor_tcp_init()

    #def servidor_tcp_init(self,bandera_envio_recepcion):                #PJAM 
    def servidor_tcp_init(self):
        #self.envio = servidor_tcp(tamaño_audio,bandera_envio_recepcion)
        self.envio = servidor_tcp()
        return self.envio
    def __repr__(self):
        return self.envio
    #def configuracion_tcp(self,tamaño_audio,bandera_envio_recepcion):
        #self.envio.configuracion_socket(tamaño_audio,bandera_envio_recepcion)


class conf_tcp(object): 
    def __init__(self):
        self.hilo_tcp_01=[]
        self.datos_hilo = []

    def configuracion_conf_tcp(self,tamaño_audio,bandera_envio_recepcion,server):
        self.tamaño_audio = tamaño_audio[0]
        self.bandera_envio_recepcion = bandera_envio_recepcion
        self.server = server
        self.ingresar_datos()

    def ingresar_datos(self):
        self.datos_hilo.append(self.tamaño_audio)
        self.datos_hilo.append(self.bandera_envio_recepcion)
        self.datos_hilo.append("$")
        logging.info("DATOS_HILO: ")
        logging.info(self.datos_hilo)

    def hilo_tcp(self):
        self.hilo_tcp_01 = (threading.Thread(name = 'hilo tcp',         #PJAM Se agrega a la lista la configuración de un domonio por cada usuario existente
                                    target = configuracion_tcp,
                                    args = (self.datos_hilo,self.server),
                                    daemon = False
                                    ))
        self.hilo_tcp_01.start()
    #def inicio_hilo_tcp(self):
        #self.hilo_tcp_01.start()

def configuracion_tcp(datos_hilo,server):
    tamaño_bandera = []
    for i in range(len(datos_hilo)):
        if datos_hilo[i]=="$":
            logging.info("DATOS DEL HILO: ")
            logging.info(tamaño_bandera)
            while 1:
                server.configuracion_socket(int(datos_hilo[0]),int(datos_hilo[1]))
                break
            tamaño_bandera = []
            logging.info("SALIÓ DEL WHILE")
        else:
            tamaño_bandera.append(datos_hilo[i])

'''
    -------------------RMJD Funcion Demonio Contador Alive-----------------------------------------------------------------
'''      
def contador_alive(alv,i):
    while 1:
        time.sleep(2)
        alv.aumento_conteo_alive(1,i)
'''
-------------------PJAM LECTURA TEXTO PLANO------------------------------------------------------------------
 '''
def Configuracion():
    salas_file = [] #PJAM lista que guardará el usuario y las salas
    datos_usuario = []  #PJAM almacena los datos extraidos del documento usuarios
    datos_usuario_1 = []  #PJAM almacena los datos extraidos del documento usuarios
    datos_USER_IDS = [] #PJAM almacena exclusivament los USER_ID'S de los usuarios
    solo_salas = [] #PJAM almacena solo las salas en una lista
    path_to_script = os.path.dirname(os.path.abspath(__file__)) #PJAM instrucción que devuelve la dirección de este archivo
    '''
    usuario_conf = os.path.join(path_to_script, "usuario.txt")  #PJAM isntrucción que une la dirección con el nombre del documento .txt
    f= open(usuario_conf, "r")
    for line in f:
        salas_file.append(line)
    f.close()
    '''
    usuarios_conf = os.path.join(path_to_script, "usuarios.txt")  #PJAM isntrucción que une la dirección con el nombre del documento .txt
    q=open(usuarios_conf, "r")          #PJAM abre el documento en formato de lectura
    for line in q:
        datos_usuario.append(line)      #PJAM Guarda todas las lineas del documento en una lista
    q.close
    for i in range (len(datos_usuario)):
        datos_usuario_1.append(datos_usuario[i].split(','))     # PJAMSe guardan todos los datos de cada usuario como una lista individual dentro de una posicón en otra lista
    for i in range (len(datos_usuario_1)):
        for e in range(len(datos_usuario_1[i])):
            datos_usuario_1[i][e] = datos_usuario_1[i][e].replace('\n', '') #PJAM remplaza los saltos de linea con espacio vacío
            if e == 0:
                salas_file.append(datos_usuario_1[i][e])        #PJAM Se guardan los carné de cada usuario en una variable que será enviada al mqtt
                datos_USER_IDS.append(datos_usuario_1[i][e])    #PJAM Se guardan los carné de cada usuario en una variable que será enviado a la verficiación de ALIVE
    logging.debug(datos_usuario_1)
    
    salas_conf = os.path.join(path_to_script, "salas.txt")
    f= open(salas_conf, "r")
    for line in f:
        salas_file.append(line)
    f.close()
    for i in range(len(salas_file)):
        salas_file[i] = salas_file[i].replace('\n', '') #PJAM remplaza los saltos de linea con espacio vacío
        if salas_file[i]=="":
            del salas_file[i]
    for i in range(len(datos_USER_IDS),len(salas_file)):
        solo_salas.append(salas_file[i])
    logging.debug(solo_salas)                                                                                                                                                                                                                        
    return(salas_file,datos_USER_IDS,datos_usuario_1,solo_salas)

'''
-------------------PJAM HILO PRINCIPAL ----------------------------------------------------------------
'''
salas_file,datos_USER_IDS, data_entera,solo_salas = Configuracion()    ##PJAM extrea del documento de texto el usuario y las salas
logging.info(data_entera)
logging.info(solo_salas)
cantidad_usuarios = len(datos_USER_IDS)     ##PJAM se guardará la cantidad de usuarios que estn configurados, esto con el objetivo de que cada usuario tenga 
                                            ##su propio demonio

alv= Verificacion_Alvie(datos_USER_IDS)
hilo = HILO_TIEMPO(alv,cantidad_usuarios)
mqtt = InicioMQTT(salas_file,alv,hilo)       ##Inicia la configuración del MQTT
mqtt.Client_loop()                  ##Incia el loop para recibir mensajes del broker
no_ok = OK_NO(alv,mqtt,solo_salas,data_entera)
mqtt.variables(no_ok)

while 1:
    logging.info("")
    time.sleep(60)


