import socket
import ssl
import json
import os
import psutil
import platform
import time

class Client:
    def __init__(self):
        self.discovery_port = 50000
        self.server_info = None  # Armazenará (ip, porta) do servidor

    def pegar_cpu_temp_linux(self):
        """Obtém a temperatura da CPU no Linux."""
        try:
            # Tenta o caminho padrão
            try:
                with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                    temp = int(f.read().strip()) / 1000  # Converte de millicelsius para celsius
                    return temp
            except FileNotFoundError:
                pass

            # Procura em /sys/class/hwmon/
            for hwmon_path in os.listdir("/sys/class/hwmon/"):
                try:
                    with open(f"/sys/class/hwmon/{hwmon_path}/temp1_input", "r") as f:
                        temp = int(f.read().strip()) / 1000  # Converte de millicelsius para celsius
                        return temp
                except FileNotFoundError:
                    continue
            print("Temperatura da CPU não encontrada.")
            return None
        except Exception as e:
            print(f"Erro ao ler temperatura no Linux: {e}")
            return None

    def pegar_cpu_temp_windows(self):
        return None     
        
    def descobrir_servidor(self):
        """Descobre o servidor na rede local."""
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            print("Enviando mensagem de descoberta...")
            sock.sendto(b'DISCOVER', ('255.255.255.255', self.discovery_port))
            sock.settimeout(5)
            try:
                data, addr = sock.recvfrom(1024)  # addr contém (IP_servidor, porta)
                print(f"Resposta recebida do servidor: {data.decode()}")  # Log da resposta
                self.server_info = (addr[0], json.loads(data.decode())['port'])
                print(f"Servidor encontrado: {self.server_info}")
                return True
            except Exception as e:
                print(f"Erro na descoberta: {e}")
                return False

    def pegar_specs(self):
        """Coleta informações do sistema."""
        system = platform.system().lower()
        cpu_temp = self.pegar_cpu_temp_windows()

        return {
            'Processadores': os.cpu_count(),
            'RAM Livre': psutil.virtual_memory().available,
            'Disco Livre': psutil.disk_usage('/').free,
            'Temperatura CPU': cpu_temp
        }

    def enviar_dados(self):
        """Envia os dados do sistema para o servidor."""
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        try:
            print(f"Conectando ao servidor: {self.server_info}")
            with socket.create_connection(self.server_info) as sock:
                with context.wrap_socket(sock, server_hostname=self.server_info[0]) as ssock:
                    data = json.dumps(self.pegar_specs()).encode()
                    print(f"Enviando dados: {data}")  # Log dos dados enviados
                    ssock.send(data)
            print("Dados enviados com sucesso!")
        except Exception as e:
            print(f"Erro na conexão: {e}")

    def run(self):
        """Executa o cliente."""
        if self.descobrir_servidor():
            while True:
                self.enviar_dados()
                time.sleep(30)  # Aguarda 30 segundos antes de enviar novamente

if __name__ == "__main__":
    Client().run()