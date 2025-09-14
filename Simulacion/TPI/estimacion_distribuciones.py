import math
import json
import pandas as pd
from pathlib import Path

# ===========================
# PARÁMETROS A EDITAR
# ===========================
CSV_PATH = "Archivos/recuento_de_carreteras.csv"  # <- ruta a tu CSV enorme
# Centro aproximado de la rotonda (Arco del Triunfo)
CENTER_LAT = 48.8738
CENTER_LON = 2.2950
# Radio de captura de la rotonda (metros). 220–280 m suele funcionar bien.
RADIUS_M = 260
# Tamaño de chunk (filas) para CSV grande
CHUNKSIZE = 200_000
# Nombre exacto de columnas (según tu ejemplo; ajustá si difiere)
COLS = {
    "libelle": "Libelle",
    "datetime": "Date et heure de comptage",
    "flow": "Débit horaire",
    "occ": "Taux d'occupation",
    "state": "Etat trafic",
    "up_id": "Identifiant noeud amont",
    "down_id": "Identifiant noeud aval",
    "geo_point": "geo_point_2d",
    "geo_shape": "geo_shape"
}

# ===========================
# UTILIDADES GEOMÉTRICAS
# ===========================
def haversine_m(lat1, lon1, lat2, lon2):
    R = 6371000.0
    phi1 = math.radians(lat1); phi2 = math.radians(lat2)
    dphi = phi2 - phi1
    dl = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dl/2)**2
    return 2*R*math.asin(math.sqrt(a))

def point_within_radius(lat, lon, clat, clon, r_m):
    return haversine_m(lat, lon, clat, clon) <= r_m

def parse_linestring_coords(geo_shape_str):
    """
    geo_shape viene como JSON con {"type":"LineString","coordinates":[[lon,lat],...]}
    Devuelve lista de (lat, lon). Robusto a filas raras.
    """
    if not isinstance(geo_shape_str, str) or not geo_shape_str.strip():
        return None
    try:
        o = json.loads(geo_shape_str)
        if o.get("type") != "LineString":
            return None
        coords = o.get("coordinates", [])
        latlon = [(float(c[1]), float(c[0])) for c in coords if isinstance(c, (list, tuple)) and len(c) >= 2]
        return latlon if latlon else None
    except Exception:
        return None

def angle_from_center(lat, lon, clat, clon):
    """
    Ángulo (radianes) desde el centro hacia el punto (0 = Este, sentido antihorario).
    Para agrupar por 'piernas' por ángulo.
    """
    dy = lat - clat
    dx = lon - clon
    ang = math.atan2(dy, dx)
    # normalizar a [0, 2π)
    return ang if ang >= 0 else (ang + 2*math.pi)

def classify_inbound_outbound(coord_seq, clat, clon):
    """
    Usa los extremos de la polilínea:
    - Si el primer punto está más cerca del centro que el último → OUTBOUND (se aleja del centro).
    - Si el último punto está más cerca → INBOUND (se acerca al centro).
    - Si ambos similares → 'ring/unknown' (podría ser el anillo de la rotonda).
    """
    if not coord_seq or len(coord_seq) < 2:
        return "unknown", None
    first = coord_seq[0]
    last = coord_seq[-1]
    d_first = haversine_m(first[0], first[1], clat, clon)
    d_last  = haversine_m(last[0],  last[1],  clat, clon)
    # umbral para considerar "similar"
    if abs(d_first - d_last) < 20:  # 20 m
        return "ring", None
    if d_last < d_first:
        # termina más cerca del centro → entra a la rotonda
        # ángulo de la punta "externa" (entrada)
        ext = first if d_first > d_last else last
        ang = angle_from_center(ext[0], ext[1], clat, clon)
        return "inbound", ang
    else:
        # empieza más cerca del centro → sale de la rotonda
        ext = last if d_last > d_first else first
        ang = angle_from_center(ext[0], ext[1], clat, clon)
        return "outbound", ang

# ===========================
# LIMPIEZA Y PARSING
# ===========================
def parse_flow(value):
    """
    Convierte strings como '2.460.056', '5955.0', '138,222', '' a float o NaN.
    Regla:
      - quitar separadores de miles (puntos o espacios) cuando hay >1 punto
      - cambiar coma decimal por punto
    """
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return float("nan")
    s = str(value).strip()
    if not s:
        return float("nan")
    # reemplazar coma decimal por punto
    s = s.replace(",", ".")
    # si hay más de un punto, asumimos que eran miles + decimal: quitamos todos salvo el último
    if s.count(".") > 1:
        parts = s.split(".")
        s = "".join(parts[:-1]) + "." + parts[-1]
    try:
        return float(s)
    except Exception:
        return float("nan")

def parse_dt(value):
    try:
        return pd.to_datetime(value, utc=True, errors="coerce")
    except Exception:
        return pd.NaT

# ===========================
# AGRUPACIÓN DE PIERNAS
# ===========================
def bucket_angle_to_leg(angle_rad, n_legs=12):
    """
    Asigna el ángulo a un 'leg' (0..n_legs-1) dividiendo el círculo en sectores iguales.
    En CDG normalmente hay ~12 avenidas.
    """
    sector = (2*math.pi) / n_legs
    idx = int(angle_rad // sector)
    return int(max(0, min(n_legs-1, idx)))

# ===========================
# PIPELINE PRINCIPAL
# ===========================
def main():
    center_lat, center_lon = CENTER_LAT, CENTER_LON
    r_m = RADIUS_M
    n_legs = 12  # podés ajustar si querés menos/más grueso

    # Acumuladores
    inbound_rows = []
    outbound_rows = []

    usecols = [v for v in COLS.values()]
    # Algunos CSV usan separador TAB; otros coma. Intentamos ambos.
    # Primero probamos con sep=None (engine='python') que autodetecta.
    read_kwargs = dict(
        chunksize=CHUNKSIZE,
        usecols=lambda c: c in usecols,
        dtype=str,  # leemos todo como str para limpieza robusta
        sep=None, engine="python"
    )

    total_rows = 0
    kept_rows = 0

    for chunk in pd.read_csv(CSV_PATH, **read_kwargs):
        total_rows += len(chunk)

        # Parse mínimo
        chunk = chunk.rename(columns={v: k for k, v in COLS.items()})

        # parseo de flow y datetime
        chunk["flow_val"] = chunk["flow"].apply(parse_flow)
        chunk["dt"] = chunk["datetime"].apply(parse_dt)
        # descartamos filas sin tiempo o sin geometría
        chunk = chunk[chunk["dt"].notna() & chunk["geo_shape"].notna()]

        # parseamos geometría y filtramos por radio
        coords = chunk["geo_shape"].apply(parse_linestring_coords)
        chunk = chunk.assign(coords=coords)
        chunk = chunk[chunk["coords"].notna()]

        # ¿toca la geocerca?
        def touches_roundabout(cseq):
            for (lat, lon) in cseq:
                if point_within_radius(lat, lon, center_lat, center_lon, r_m):
                    return True
            return False

        mask_round = chunk["coords"].apply(touches_roundabout)
        sub = chunk[mask_round].copy()
        kept_rows += len(sub)

        # Clasificar inbound/outbound y ángulo
        classes = sub["coords"].apply(lambda cs: classify_inbound_outbound(cs, center_lat, center_lon))
        sub["io_flag"] = classes.apply(lambda x: x[0])
        sub["angle"] = classes.apply(lambda x: x[1])

        # Solo nos interesan inbound / outbound
        sub = sub[sub["io_flag"].isin(["inbound","outbound"]) & sub["angle"].notna()]

        # bucket de pierna
        sub["leg"] = sub["angle"].apply(lambda a: bucket_angle_to_leg(a, n_legs=n_legs))

        # Guardamos mínimos campos
        keep_cols = ["dt", "flow_val", "io_flag", "leg", "libelle", "up_id", "down_id"]
        sub = sub[keep_cols]

        # dividir y acumular
        inb = sub[sub["io_flag"]=="inbound"].drop(columns=["io_flag"])
        outb = sub[sub["io_flag"]=="outbound"].drop(columns=["io_flag"])

        inbound_rows.append(inb)
        outbound_rows.append(outb)

    print(f"Leídas {total_rows:,} filas; retenidas {kept_rows:,} cerca de CDG.")

    if not inbound_rows and not outbound_rows:
        print("No se detectaron arcos cerca de la rotonda. Probá aumentar RADIUS_M o revisá nombres de columnas.")
        return

    inbound = pd.concat(inbound_rows, ignore_index=True) if inbound_rows else pd.DataFrame(columns=["dt","flow_val","leg","libelle","up_id","down_id"])
    outbound = pd.concat(outbound_rows, ignore_index=True) if outbound_rows else pd.DataFrame(columns=["dt","flow_val","leg","libelle","up_id","down_id"])

    # ===========================
    # 1) LLEGADAS POR ENTRADA (serie horaria)
    # ===========================
    # Sumamos el flow por leg y hora
    inbound["hour"] = inbound["dt"].dt.floor("H")
    arrivals_hour = (inbound
                     .groupby(["leg","hour"], as_index=False)["flow_val"]
                     .sum()
                     .rename(columns={"flow_val":"veh_per_hour"}))
    arrivals_hour["veh_per_min"] = arrivals_hour["veh_per_hour"] / 60.0
    arrivals_hour.to_csv("arrivals_by_leg_hour.csv", index=False)

    # Perfil medio por hora del día (para AnyLogic "Profiles"/"Rate schedule")
    inbound["hod"] = inbound["dt"].dt.tz_convert(None).dt.hour  # hora local-naive
    arrivals_profile = (inbound.groupby(["leg","hod"], as_index=False)["flow_val"].mean()
                        .rename(columns={"flow_val":"veh_per_hour_avg"}))
    arrivals_profile["veh_per_min_avg"] = arrivals_profile["veh_per_hour_avg"] / 60.0
    arrivals_profile.to_csv("arrivals_by_leg_profile.csv", index=False)

    # ===========================
    # 2) SALIDAS POR PIERNA
    # ===========================
    outbound_total = (outbound.groupby("leg", as_index=False)["flow_val"].sum()
                      .rename(columns={"flow_val":"veh_out_total"}))
    total_out = outbound_total["veh_out_total"].sum()
    if total_out > 0:
        outbound_total["p_exit_global"] = outbound_total["veh_out_total"] / total_out
    else:
        outbound_total["p_exit_global"] = 0.0
    outbound_total.to_csv("exit_distribution_global.csv", index=False)

    # ===========================
    # INFO AUXILIAR PARA MAPEAR PIERNAS
    # ===========================
    # Damos una tabla de “nombres más frecuentes” por leg para ayudarte a identificar qué leg es qué avenida.
    def top_labels(df, k=5):
        if df.empty: 
            return pd.DataFrame(columns=["leg","label","count"])
        counts = (df.groupby(["leg","libelle"]).size().reset_index(name="count"))
        return counts.sort_values(["leg","count"], ascending=[True, False]).groupby("leg").head(k)

    labels_in = top_labels(inbound, k=8).rename(columns={"libelle":"libelle_in"})
    labels_out = top_labels(outbound, k=8).rename(columns={"libelle":"libelle_out"})
    labels_in.to_csv("leg_labels_inbound_top.csv", index=False)
    labels_out.to_csv("leg_labels_outbound_top.csv", index=False)

    print("Listo:")
    print(" - arrivals_by_leg_hour.csv")
    print(" - arrivals_by_leg_profile.csv")
    print(" - exit_distribution_global.csv")
    print(" - leg_labels_inbound_top.csv (ayuda para asignar ‘leg’ a avenidas)")
    print(" - leg_labels_outbound_top.csv (ayuda para asignar ‘leg’ a avenidas)")

if __name__ == "__main__":
    main()
