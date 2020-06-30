import socket
import logging
import os
import time
from datetime import datetime
import threading #Concurrencia con hilos

logging.basicConfig(
    level = logging.INFO, 
    format = '[%(levelname)s] (%(processName)-10s) %(message)s'
    )

class Cliente_Tcp(object):
    def __init__(self):
    #def  __init__(self,bandera_envio_recepcion):
        self.SERVER_IP   = '167.71.243.238'
        #self.SERVER_IP = '127.0.0.1' 
        self.SERVER_PORT = 9825
        self.BUFFER_SIZE = 64 * 1024

        #self.bandera_envio_recepcion = bandera_envio_recepcion
        #self.audio_tamaño = duracion_audio_recibir
        

        #path_to_script = os.path.dirname(os.path.abspath(__file__)) #PJAM instrucción que devuelve la dirección de este archivo
        #usuario_conf = os.path.join(path_to_script, "prueba_02_examen02.wav")  #PJAM isntrucción que une la dirección con el nombre del documento .txt

        #direccion = '/home/pablo/Escritorio/USAC/VACACIONES_JUNIO_2020/PROYECTOS/PRUEBAS_PYTHON/EXAMEN_FINAL/USUARIO/prueba_02_examen02.wav'    #QUITAR TRES LINEAS
        #self.audio_tamaño = os.stat(direccion).st_size

        
        #self.configuracion_socket(usuario_conf)
        #self.configuracion_socket(direccion_audio)
          

    def configuracion_socket(self,direccion_audio,bandera_envio_recepcion,duracion_audio_recibir):
        self.bandera_envio_recepcion = int(bandera_envio_recepcion)
        self.audio_tamaño = int(duracion_audio_recibir)
        self.direccion_audio = direccion_audio
        #self.message = mensaje
        # Se crea socket TCP
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Se conecta al puerto donde el servidor se encuentra a la escucha
        server_address = (self.SERVER_IP, self.SERVER_PORT)
        logging.info('Conectando a {} en el puerto {}'.format(*server_address))
        self.sock.connect(server_address)

        if self.bandera_envio_recepcion == 1:
            self.transporte_archivos()
        elif self.bandera_envio_recepcion == 2:
            self.recepcion_audio()
        

    def transporte_archivos(self):
        logging.info("ENTRA A TRANSPORTE ARCHIVOS")
        binario1=b''
        a=1
        #valores = []
        try:

            f= open(self.direccion_audio, "rb")

            while a==1:
                binario=f.read(self.BUFFER_SIZE)
                if binario:
                    binario1+=binario
                    self.sock.sendall(binario)
                else:
                    a=2
            tamaño_audio_enviado = str(len(binario1))
            logging.info("TAMAÑO DE ADUDIO ENVIADO: "+ tamaño_audio_enviado)
            
            logging.info("\n\n")

            # Esperamos la respuesta del ping servidor
            binario_tamaño = tamaño_audio_enviado.encode()
            bytesRecibidos = 0
            bytesEsperados = len(binario_tamaño)

            #TCP envia por bloques de BUFFER_SIZE bytes
            while bytesRecibidos < bytesEsperados:
                data = self.sock.recv(self.BUFFER_SIZE)
                bytesRecibidos += len(data)
                logging.info('Recibido: {!s}'.format(data))

            logging.info("AUDIO ENVIADO")

        finally:
            print('\n\nConexion finalizada con el servidor')
            self.sock.close()

    def recepcion_audio(self):
        logging.debug("ENTRA A ENVIO DE ARCHIVOS")
        data = b''
        try:

            while True:
                data += self.sock.recv(self.BUFFER_SIZE)
                tamaño_recepcion = str(len(data))
                logging.debug('Recibido:' + str(tamaño_recepcion))
                if len(data) < int(self.audio_tamaño):
                    #print('Transmision finalizada desde el servidor')
                    #break
                    pass
                else:
                    print('Transmision finalizada desde el servidor')
                    break
            logging.info("AUDIO  RECIBIDO")
        finally:
            print('\n\nConexion finalizada con el servidor')
            self.sock.close()
            self.Reconstruccion_audio(data)

    def Reconstruccion_audio(self,audio_bits):
        logging.debug("TAMAÑO DATA RECIBIDA: "+ str(len(audio_bits)))

        now = datetime.now()
        timestamp = datetime.timestamp(now)

        nombre_archivo= str(timestamp)+".wav"

        path_to_script = os.path.dirname(os.path.abspath(__file__)) #PJAM instrucción que devuelve la dirección de este archivo
        direccion_audio_recibido = os.path.join(path_to_script, nombre_archivo) 

        q= open(direccion_audio_recibido,'wb')
        q.write(audio_bits)
        logging.debug(type(q))
        q.close()
        Reproduccion_hilos(direccion_audio_recibido,timestamp)

class Reproduccion_hilos(object):
    def  __init__(self,direccion_audio,nombre_audio):
        self.direccion_audio = direccion_audio
        self.nombre_audio = nombre_audio
        self.Creacion_hilos()
        

    def Creacion_hilos(self):
        
        t1 = threading.Thread(name = 'Reproducción Audio' +str(self.nombre_audio),
                            target = self.Reproduccion_audio_reconstruido,
                            args = (()),
                            daemon = False
                            )
        t1.start()

    def Reproduccion_audio_reconstruido(self):
        logging.info('GRABACIÓN FINALIZADA, INCIA REPRODUCCION')
        os.system('aplay '+ self.direccion_audio)

        

#bandera_envio_recepcion = 1
#tcp = Cliente_Tcp(bandera_envio_recepcion)
#time.sleep(10)
#bandera_envio_recepcion = 2
#tcp = Cliente_Tcp(bandera_envio_recepcion)
