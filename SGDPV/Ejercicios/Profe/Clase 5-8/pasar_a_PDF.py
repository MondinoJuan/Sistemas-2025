import pyodbc
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors

# Conexión a SQL Server
conn = pyodbc.connect(
    'DRIVER={ODBC Driver 17 for SQL Server};'
    'SERVER=localhost\\SQLEXPRESS;'
    'DATABASE=WideWorldImportersDW;'
    'Trusted_Connection=yes;'
)
cursor = conn.cursor()

# Consulta (limita a 400 filas para no saturar)
cursor.execute("SELECT TOP 400 * FROM WideWorldImportersDW.Fact.Purchase")

# Obtener encabezados
columns = [desc[0] for desc in cursor.description]

# Obtener filas
data = [columns]  # Agregamos los encabezados como primera fila
for row in cursor:
    data.append([str(cell) for cell in row])

# Crear PDF con tabla
pdf_file = "salida_compras_tabla.pdf"
doc = SimpleDocTemplate(pdf_file, pagesize=letter)
elements = []

# Crear tabla
table = Table(data, repeatRows=1)

# Estilos para la tabla
style = TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),        # Fondo encabezado
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),   # Color texto encabezado
    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),                 # Alineación de texto
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),     # Fuente encabezado
    ('FONTSIZE', (0, 0), (-1, -1), 8),                   # Tamaño de fuente
    ('BOTTOMPADDING', (0, 0), (-1, 0), 6),               # Padding encabezado
    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),      # Fondo filas
    ('GRID', (0, 0), (-1, -1), 0.25, colors.black),      # Bordes
])

table.setStyle(style)
elements.append(table)

# Generar PDF
doc.build(elements)
print(f"PDF generado: {pdf_file}")
