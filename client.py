import socket
import ssl
import json
import os
import psutil
import platform

class Client:
    def __init__(self):
        self.discovery_port = 50000
        self.server_info = None  # Armazenará (ip, porta) do servidor

    def get_cpu_temp_linux(self):
        """Obtém a temperatura do CPU no Linux."""
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
        # Se nenhum caminho funcionar, retorna None
            print("Temperatura do CPU não encontrada.")
            return None
        except Exception as e:
            print(f"Erro ao ler temperatura no Linux: {e}")
            return None

    def get_cpu_temp_windows(self):
        return None     
        
    def discover_server(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.sendto(b'DISCOVER', ('255.255.255.255', self.discovery_port))
            sock.settimeout(5)
            try:
                data, addr = sock.recvfrom(1024)  # addr contém (IP_servidor, porta)
                self.server_info = (addr[0], json.loads(data.decode())['port'])
                return True
            except Exception as e:
                print(f"Erro na descoberta: {e}")
                return False


    def get_system_info(self):
        system = platform.system().lower()
        cpu_temp = self.get_cpu_temp_windows()

        return {
            'processors': os.cpu_count(),
            'free_ram': psutil.virtual_memory().available,
            'free_disk': psutil.disk_usage('/').free,
            'cpu_temp': cpu_temp
        }

    def send_data(self):
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        try:
            with socket.create_connection(self.server_info) as sock:
                with context.wrap_socket(sock, server_hostname=self.server_info[0]) as ssock:
                    ssock.send(json.dumps(self.get_system_info()).encode())
            print("Dados enviados com sucesso!")
        except Exception as e:
            print(f"Erro na conexão: {e}")

    def run(self):
        if self.discover_server():
            self.send_data()

if __name__ == "__main__":
    Client().run()