import socket
import logging
import os
import time

logging.basicConfig(
    level = logging.INFO, 
    format = '[%(levelname)s] (%(processName)-10s) %(message)s'
    )

class servidor_tcp(object):
    #def  __init__(self,tamaño_audio,bandera_envio_recepcion):
    def __init__(self):
        self.IP_ADDR = '167.71.243.238' #La IP donde desea levantarse el server
        #self.IP_ADDR = '127.0.0.1' 
        self.IP_ADDR_ALL = ''       #PJAM En caso que se quiera escuchar en todas las interfaces de red
        self.IP_PORT = 9825         ##PJAM Puerto al que deben conectarse los clientes
        self.BUFFER_SIZE = 64 * 1024    ##PJAM Bloques de 64 KB

    def configuracion_socket(self,tamaño_audio,bandera_envio_recepcion):
        self.bandera_envio_recepcion = int(bandera_envio_recepcion)
        self.tamaño_audio = int(tamaño_audio)
                                                   
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)                ##PJAM Crea un socket TCP
        ##PJAM Bind the socket to the port
        serverAddress = (self.IP_ADDR, self.IP_PORT)                                    ##PJAM Escucha en todas las interfaces
        logging.info('Iniciando servidor en {}, puerto {}'.format(*serverAddress))
        self.sock.bind(serverAddress)                                                    ##PJAM Levanta servidor con parametros especificados
        logging.debug("LLEGA A LA COMPARACION")

        if self.bandera_envio_recepcion == 1:
            self.recepcion_archivos()
        elif self.bandera_envio_recepcion == 2:
            self.envio_archivos()

    def recepcion_archivos(self):                                     ##PJAM Habilita la escucha del servidor en las interfaces configuradas
                          
        self.sock.listen(10)                                            ##PJAM El argumento indica la cantidad de conexiones en cola
        data = b''
        while True:
            ##PJAM  Esperando conexion
            logging.info('Esperando conexion remota')
            connection, clientAddress = self.sock.accept()
            try:
                logging.info('Conexion establecida desde: ' + str(clientAddress))

                ##PJAM  Se envia informacion en bloques de BUFFER_SIZE bytes
                ##PJAM  y se espera respuesta de vuelta

                while True:
                    data += connection.recv(self.BUFFER_SIZE)
                    tamaño_recepcion = str(len(data))
                    binario_tamaño_recepcion = tamaño_recepcion.encode()
                    logging.info('Recibido:' + str(tamaño_recepcion))
                    if data:            ##PJAM  Si se reciben datos (o sea, no ha finalizado la transmision del cliente)
                        logging.debug('Enviando tamaño de audio recibido')
                        connection.sendall(binario_tamaño_recepcion)
                    else:
                        logging.debug('Transmision finalizada desde el cliente ' + str(clientAddress))
                        break
    
            except KeyboardInterrupt:
                self.sock.close()

            finally:
                # Se baja el servidor para dejar libre el puerto para otras aplicaciones o instancias de la aplicacion
                connection.close()
                break
        self.audio_bits = data
        logging.info(len(self.audio_bits))
        self.Reconstruccion_audio(self.audio_bits)

    def envio_archivos(self):
        logging.debug("ENTRA A TRANSPORTE ARCHIVOS")
        self.sock.listen(10)
        binario1=b''
        a=1
        #valores = []
        while True:
            logging.info('Esperando conexion remota')
            connection, clientAddress = self.sock.accept()
            try:
                logging.debug('ENTRA EN TRY')
                logging.info('Conexion establecida desde: ' + str(clientAddress))

                f=open(self.direccion_audio_recibido, "rb")
                logging.info("LLEGA ANTES DEL WHILE")
                while a==1:
                    binario=f.read(self.BUFFER_SIZE)
                    if binario:
                        binario1+=binario
                        connection.sendall(binario)
                    else:
                        a=2
                tamaño_audio_enviado = str(len(binario1))
                logging.debug("TAMAÑO DE ADUDIO ENVIADO: "+ tamaño_audio_enviado)

                logging.info("AUDIO ENVIADO")
            finally:
                # Se baja el servidor para dejar libre el puerto para otras aplicaciones o instancias de la aplicacion
                connection.close()
                break
                
    def Reconstruccion_audio(self,audio_bits):
        logging.debug(len(audio_bits))
        
        nombre_archivo= "AUDIO_RECIBIDO.wav"

        path_to_script = os.path.dirname(os.path.abspath(__file__)) #PJAM instrucción que devuelve la dirección de este archivo
        self.direccion_audio_recibido = os.path.join(path_to_script, nombre_archivo) 

        q= open(self.direccion_audio_recibido,'wb')
        q.write(audio_bits)
        logging.debug(type(q))
        q.close()
  
             


#bandera_envio_recepcion = 1

#tcp = servidor_tcp(bandera_envio_recepcion)
#time.sleep(5)

#tcp.configuracion_socket(2)


