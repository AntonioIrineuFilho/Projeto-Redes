import psutil

# Verifica se a temperatura está disponível
if hasattr(psutil, "sensors_temperatures"):
    temps = psutil.sensors_temperatures()
    print("Temperaturas disponíveis:", temps)
else:
    print("Leitura de temperatura não suportada no sistema.")