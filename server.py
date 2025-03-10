import socket
import ssl
import json
from threading import Thread
import time

sair = False

class Server:
    def __init__(self):
        self.clients = {}  # Armazena {ip: {'data': client_data, 'last_update': timestamp}}
        self.host = '0.0.0.0'
        self.discovery_port = 50000
        self.tcp_port = 50001
        self.certfile = 'server.crt'
        self.keyfile = 'server.key'
        self.udp_socket = None
        self.tcp_socket = None
        self.setup_udp()
        Thread(target=self.setup_tcp).start()
        Thread(target=self.checar_cliente_inativo).start()  # Inicia a verificação de clientes inativos
        self.user_interface()

    def setup_udp(self):
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.bind((self.host, self.discovery_port))
        Thread(target=self.listen_udp).start()

    def listen_udp(self):
        while not sair:
            try:
                data, addr = self.udp_socket.recvfrom(1024)
                if data.decode() == 'DISCOVER':
                    response = json.dumps({'port': self.tcp_port})
                    self.udp_socket.sendto(response.encode(), addr)
            except Exception as e:
                if not sair:
                    print(f"Erro no UDP: {e}")

    def setup_tcp(self):
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_socket.bind((self.host, self.tcp_port))
        self.tcp_socket.listen(5)
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(self.certfile, self.keyfile)
        while not sair:
            try:
                client_socket, addr = self.tcp_socket.accept()
                ssl_socket = context.wrap_socket(client_socket, server_side=True)
                Thread(target=self.manter_cliente, args=(ssl_socket, addr)).start()
            except Exception as e:
                if not sair:
                    print(f"Erro no TCP: {e}")

    def manter_cliente(self, ssl_socket, addr):
        try:
            data = ssl_socket.recv(1024).decode()
            client_data = json.loads(data)
            self.clients[addr[0]] = {
                'data': client_data,
                'last_update': time.time()  # Armazena o timestamp da última atualização
            }
            ssl_socket.close()
        except Exception as e:
            print(f"Erro: {e}")

    def checar_cliente_inativo(self):
        """Remove clientes inativos por mais de 30 segundos."""
        while not sair:
            time.sleep(10)  # Verifica a cada 10 segundos
            current_time = time.time()
            inactive_clients = [
                ip for ip, client in self.clients.items()
                if current_time - client['last_update'] > 30
            ]
            for ip in inactive_clients:
                print(f"Removendo cliente inativo: {ip}")
                del self.clients[ip]

    def calcular_media(self):
        medias = {}
        for key in ['Processadores', 'RAM Livre', 'Disco Livre', 'Temperatura CPU']:
            values = [c['data'][key] for c in self.clients.values() if c['data'][key] is not None]
            medias[key] = sum(values)/len(values) if values else None
        return medias

    def user_interface(self):
        global sair
        while not sair:
            cmd = input("Comando (Listar/Detalhar <IP>/Media/Sair): ").upper()
            if cmd == "LISTAR":
                print("Clientes:", list(self.clients.keys()))
            elif cmd.startswith("DETALHAR"):
                try:
                    ip = cmd.split()[1]
                    if ip in self.clients:
                        client_data = self.clients[ip]['data']
                        print(f"Detalhes do dispositivo {ip}:")
                        for key in ['Processadores', 'RAM Livre', 'Disco Livre', 'Temperatura CPU']:
                            value = client_data.get(key, "N/A")
                            print(f"{key}: {value}")
                    else:
                        print(f"Dispositivo com IP {ip} não encontrado.")
                except IndexError:
                    print("Uso correto: detalhar <IP>")
            elif cmd == "MEDIA":
                print(self.calcular_media())
            elif cmd == "SAIR":
                sair = True
                self.udp_socket.close()
                self.tcp_socket.close()
                break

if __name__ == "__main__":
    Server()