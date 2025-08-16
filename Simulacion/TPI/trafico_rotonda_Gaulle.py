# En este codigo se recuperarrá información sobre el tráfico en una rotonda Charles de Gaulle.
# La información será recuperada de diferentes APIs o URLs.
# Se necesitará

import requests

def obtener_composicion_trafico(limit=100):
    base = "https://opendata.paris.fr/api/records/1.0/search/"
    params = {
        'dataset': 'compositions-du-trafic',
        'rows': limit,
        'facet': 'horaire'
    }
    r = requests.get(base, params=params)
    r.raise_for_status()
    return r.json()

def main():
    datos = obtener_composicion_trafico()
    for rec in datos.get('records', [])[:10]:
        campos = rec.get('fields', {})
        print({
            'hora': campos.get('horaire'),
            'vehiculos': campos.get('voitures', 0),
            'utilitarios': campos.get('utilitaires', 0),
            'motos': campos.get('deux_roues_motorises', 0),
            'camiones': campos.get('poids_lourds', 0),
            'autobus': campos.get('autobus', 0),
            'velos': campos.get('velos', 0),
            'autres': campos.get('autres', 0),
            'total': campos.get('total', 0)
        })

if __name__ == "__main__":
    main()

