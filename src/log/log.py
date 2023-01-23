from datetime import datetime

class Log:

    def __init__(self):
        pass

    def escrever(self, temperatura_interna, temperatura_ambiente, temperatura_referencia, pid):
        mensagem = f'Temperatura interna: {temperatura_interna} \nTemperatura externa: {temperatura_ambiente} \nTemperatura de referência: {temperatura_referencia}\nPID: {pid}% \n'

        log = open("log/log.csv", "a")
        log.write(f"{datetime.now()}\n{mensagem}\n")
        log.close()