
import streamlit as st
import datetime
import matplotlib.pyplot as plt


import pandas as pd



@st._cache_data
def cargadatos():
    data = pd.read_csv("serienueva.csv")
    data.set_index('Mes', inplace=True)
    return data

new=cargadatos()



st.title("Variable")
##st.markdown("MIni Prueba")

lista=[]
for nombre in new.columns:
    if ("named" not in nombre):
          lista.append(nombre)


input="FosfatodiamónicoUSD/t"

input=st.selectbox("Producto",lista)

if input:
    st.write(f"{input} (en USD/kg)")

    nuevo_df = new[[input]]
    nuevo_df_kg = nuevo_df / 1000  # Conversión de USD/ton a USD/kg

    tab1, tab2 = st.tabs(["Chart", "Dataframe"])

    # Gráfico en matplotlib con los valores convertidos
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(nuevo_df_kg.index, nuevo_df_kg[input], marker='o', linestyle='-', color='green')
    ax.set_title(f"{input} (USD/kg)")
    ax.set_xlabel("Mes")
    ax.set_ylabel("USD por kilo")
    ax.grid(True)
    fig.autofmt_xdate()
    tab1.pyplot(fig)

    tab2.dataframe(nuevo_df_kg, height=250, use_container_width=True)

    st.subheader("Estadísticas Resumidas")
    st.write(nuevo_df_kg.describe())

    st.subheader("Datos en bruto (originales)")
    st.dataframe(new)





