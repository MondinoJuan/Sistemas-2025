# Mandar un mensaje de whatsapp a 5 contactos diferentes

import pywhatkit as kit
import time
# usa pywin32

# Lista de números con el formato internacional (sin "+" y sin espacios)
contactos = [
    #"5493364218313",            # Mauro
    #"5493416956276",            # Juampi
    #"5493416722031",            # Lucio G
    #"5493413719098",            # Nahuel
    "5493364402114"             # Gustavo
]

imagen_path = "unnamed.png"
mensaje = "RIIIING RIIIIIIIIIIING, Sergio is Calling"

'''
for numero in contactos:
    try:
        kit.sendwhatmsg_instantly(f"+{numero}", mensaje, wait_time=10, tab_close=True)
        print(f"Mensaje enviado a {numero}")
        #time.sleep(5)
    except Exception as e:
        print(f"No se pudo enviar el mensaje a {numero}: {e}")
'''

for numero in contactos:
    try:
        # 1. Enviar mensaje de texto
        #kit.sendwhatmsg_instantly(f"+{numero}", mensaje, wait_time=10, tab_close=True)
        #print(f"Mensaje enviado a {numero}")
        
        #
        # time.sleep(12)  # Esperar un poco más para que se complete el envío y se cierre la pestaña
        
        # 2. Enviar imagen
        kit.sendwhats_image(f"+{numero}", imagen_path, caption=mensaje)
        print(f"Imagen enviada a {numero}")
        
        #time.sleep(10)  # Pausa antes de pasar al siguiente contacto

    except Exception as e:
        print(f"No se pudo enviar el mensaje o la imagen a {numero}: {e}")

