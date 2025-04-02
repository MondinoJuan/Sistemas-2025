# Buscar el valor de NVIDIA

import yfinance as yf

# Los ultimos 5 dias
recent_data = yf.download('NVDA', period='5d')
print(recent_data)

# Los ultimos 30 dias
recent_data = yf.download('NVDA', period='30d')
print(recent_data)