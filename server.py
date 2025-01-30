import socket
import ssl
import json
from threading import Thread

class Server:
    def __init__(self):
        self.clients = {}
        self.host = '0.0.0.0'
        self.discovery_port = 50000
        self.tcp_port = 50001
        self.certfile = 'server.crt'
        self.keyfile = 'server.key'
        self.setup_udp()
        Thread(target=self.setup_tcp).start()
        self.user_interface()

    def setup_udp(self):
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.bind((self.host, self.discovery_port))
        Thread(target=self.listen_udp).start()

    def listen_udp(self):
        while True:
            data, addr = self.udp_socket.recvfrom(1024)
            if data.decode() == 'DISCOVER':
                response = json.dumps({'port': self.tcp_port})
                self.udp_socket.sendto(response.encode(), addr)

    def setup_tcp(self):
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_socket.bind((self.host, self.tcp_port))
        self.tcp_socket.listen(5)
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(self.certfile, self.keyfile)
        while True:
            client_socket, addr = self.tcp_socket.accept()
            ssl_socket = context.wrap_socket(client_socket, server_side=True)
            Thread(target=self.handle_client, args=(ssl_socket, addr)).start()

    def handle_client(self, ssl_socket, addr):
        try:
            data = ssl_socket.recv(1024).decode()
            client_data = json.loads(data)
            self.clients[addr[0]] = client_data
            ssl_socket.close()
        except Exception as e:
            print(f"Erro: {e}")

    def calculate_averages(self):
        averages = {}
        for key in ['processors', 'free_ram', 'free_disk', 'cpu_temp']:
            values = [c[key] for c in self.clients.values() if c[key] is not None]
            averages[key] = sum(values)/len(values) if values else None
        return averages

    def user_interface(self):
        while True:
            cmd = input("Comando (list/detalhar/media/sair): ")
            if cmd == "list":
                print("Clientes:", list(self.clients.keys()))
            elif cmd.startswith("detalhar"):
                try:
                    # Extrai o IP do comando
                    ip = cmd.split()[1]
                    
                    # Verifica se o IP existe na lista de clientes
                    if ip in self.clients:
                        client_data = self.clients[ip]
                        print(f"Detalhes do dispositivo {ip}:")
                        for key in ['processors', 'free_ram', 'free_disk', 'cpu_temp']:
                            value = client_data.get(key, "N/A")  # Usa .get() para evitar KeyError
                            print(f"{key}: {value}")
                    else:
                        print(f"Dispositivo com IP {ip} não encontrado.")
                except IndexError:
                    print("Uso correto: detalhar <IP>")
            elif cmd == "media":
                print(self.calculate_averages())
            elif cmd == "sair":
                exit()

if __name__ == "__main__":
    Server()