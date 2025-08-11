import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders

# CONFIGURACIÓN DEL CORREO
remitente = "juancm.2000@hotmail.com"
destinatario = "nahuel.berli@gmail.com"
asunto = "Reporte de compras"
mensaje = "Adjunto el reporte en PDF generado desde la base de datos."

# CREAR MENSAJE
msg = MIMEMultipart()
msg['From'] = remitente
msg['To'] = destinatario
msg['Subject'] = asunto

# Cuerpo del correo
msg.attach(MIMEText(mensaje, 'plain'))

# Adjuntar el PDF
nombre_pdf = "salida_compras_tabla.pdf"
with open(nombre_pdf, "rb") as adjunto:
    part = MIMEBase('application', 'octet-stream')
    part.set_payload(adjunto.read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', f'attachment; filename="{nombre_pdf}"')
    msg.attach(part)

# ENVIAR EL CORREO (Ejemplo con Gmail SMTP)
try:
    servidor = smtplib.SMTP('smtp.gmail.com', 587)
    servidor.starttls()
    servidor.login(remitente, 'TU_CLAVE_O_APP_PASSWORD')
    servidor.send_message(msg)
    servidor.quit()
    print("Correo enviado con éxito.")
except Exception as e:
    print(f"Error al enviar el correo: {e}")