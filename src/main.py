import serial
import struct
import math
from time import sleep
from threading import Event, Thread 
from forno.uart import UART
from services.pid import PID
from forno.forno import Forno
from log.log import Log
from forno.i2c import get_temperatura_ambiente

class Main:
    ligado = Event()
    funcionando = Event()
    aquecendo = Event()
    resfriando = Event()
    enviando = Event()
    
    matricula = [2, 8, 6, 3]
    pid_value = 0
    temperatura_interna = 0
    temperatura_referencia = 0
    temperatura_ambiente = 0

    def __init__(self):
        self.uart = UART('/dev/serial0', 9600, 0.5)
        self.pid = PID()
        self.forno = Forno()
        self.log = Log()
        self.iniciar()

    def liga(self):
        print('\nForno ligado!\n')
        self.enviando.set()
        comando_estado = b'\x01\x16\xd3'

        self.uart.envia(comando_estado, self.matricula, b'\x01', 8)
        dados = self.uart.recebe()

        if dados is not None:
            self.para()
            self.ligado.set()

        self.enviando.clear()

    def desliga(self):
        print('\nForno desligado!\n')
        self.enviando.set()
        comando_estado = b'\x01\x16\xd3'

        self.uart.envia(comando_estado, self.matricula, b'\x00', 8)
        dados = self.uart.recebe()

        if dados is not None:
            self.para()
            self.ligado.clear()

        self.enviando.clear()

    def inicia(self):
        print('Forno ligado!')
        self.enviando.set()
        comando_estado = b'\x01\x16\xd5'

        self.uart.envia(comando_estado, self.matricula, b'\x01', 8)
        dados = self.uart.recebe()

        if dados is not None:
            self.funcionando.set()

        self.enviando.clear()

    def para(self):
        self.enviando.set()
        comando_estado = b'\x01\x16\xd5'

        self.uart.envia(comando_estado, self.matricula, b'\x00', 8)
        dados = self.uart.recebe()

        if dados is not None:
            self.funcionando.clear()

        self.enviando.clear()

    def envia_sinal_controle(self, pid):
        self.enviando.set()
        comando_aquec = b'\x01\x16\xd1'
        valor = (round(pid)).to_bytes(4, 'little', signed=True)

        self.uart.envia(comando_aquec, self.matricula, valor, 11)
        dados = self.uart.recebe()

        self.enviando.clear()

    def seta_forno(self):
        if self.ligado.is_set():
            if self.funcionando.is_set():
                self.pid_value = self.pid.pid_controle(self.temperatura_referencia, self.temperatura_interna)
                print('\n---- pid:', self.pid_value)

                self.envia_sinal_controle(self.pid_value)

                if(self.temperatura_interna < self.temperatura_referencia):
                    print("\nAQUECENDO\n")
                    self.forno.aquecer(int(abs(self.pid_value)))
                    self.forno.resfriar(0)
                    self.aquecendo.set()
                    self.resfriando.clear()

                elif(self.temperatura_interna > self.temperatura_referencia):
                    print("\nRESFRIANDO\n")
                    if (self.pid_value < 0 and self.pid_value > -40):
                        self.forno.resfriar(40)
                    else:
                        self.forno.resfriar(abs(int(self.pid_value)))
                    
                    self.forno.aquecer(0)
                    self.aquecendo.clear()
                    self.resfriando.set()


    def get_botao(self):
        comando_botao = b'\x01\x23\xc3'
        
        self.uart.envia(comando_botao, self.matricula, b'', 7)
        dados = self.uart.recebe()

        if dados is not None:
            botao = int.from_bytes(dados, 'little')%10
            print('botao:', botao)
            if botao == 1:
                self.liga()
            elif botao == 2:
                self.desliga()
            elif botao == 3:
                self.inicia()
            elif botao == 4:
                self.para()

    def get_temperatura_interna(self):
        comando_temp = b'\x01\x23\xc1'

        self.uart.envia(comando_temp, self.matricula, b'', 7)
        dados = self.uart.recebe()

        if dados is not None:
            temp = struct.unpack('f', dados)[0]

            if temp > 0 and temp < 100:
                self.temperatura_interna = temp
            
            self.seta_forno()

    def get_temperatura_referencia(self):
        comando_temp = b'\x01\x23\xc2'

        self.uart.envia(comando_temp, self.matricula, b'', 7)
        dados = self.uart.recebe()

        if dados is not None:
            temp = struct.unpack('f', dados)[0]

            if temp > 0 and temp < 100:
                self.temperatura_referencia = temp

    def envia_temperatura_ambiente(self):
        self.enviando.set()
        
        self.temperatura_ambiente = get_temperatura_ambiente()
        comando_aquec = b'\x01\x16\xd6'
        
        valor = struct.pack('!f', self.temperatura_ambiente)
        valor = valor[::-1]

        self.uart.envia(comando_aquec, self.matricula, valor, 11)
        dados = self.uart.recebe()

        self.enviando.clear()

    def escrever_log(self):
        while True:
            self.log.escrever(round(self.temperatura_interna, 2), round(self.temperatura_ambiente, 2),  round(self.temperatura_referencia), round(self.pid_value, 2))
            sleep(1)


    def rotina(self):
        while True:

            self.get_botao()
            self.get_temperatura_interna()
            self.get_temperatura_referencia()
            self.envia_temperatura_ambiente()
            sleep(1)

            print("\nTEMPERATURA INTERNA:", self.temperatura_interna)
            print("TEMPERATURA DE REFERENCIA:", self.temperatura_referencia)
            print("TEMPERATURA AMBIENTE:", self.temperatura_ambiente, "\n")
    
    def trata_ctrl_c(self):
        try:
            while True:
                sleep(2)
        except KeyboardInterrupt:
            self.para()
            self.desliga()
        else:
            pass

    
    def iniciar(self):
        self.liga()

        thread_rotina = Thread(target=self.rotina, args=())
        thread_rotina.start()

        thread_log = Thread(target=self.escrever_log, args=())
        thread_log.start()

        thread_captura_encerramento = Thread(target=self.trata_ctrl_c, args=())
        thread_captura_encerramento.start()

Main()