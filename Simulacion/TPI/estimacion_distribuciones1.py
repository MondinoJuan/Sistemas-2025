#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Estimación de distribuciones de entrada/salida para Place Charles de Gaulle
Versión: fix2 (cruce por min/max, bbox opcional amplio, umbrales más permisivos, debug)
"""

import math
import json
from pathlib import Path
from typing import List, Tuple, Optional

import numpy as np
import pandas as pd

# ===========================
# PARÁMETROS
# ===========================
CSV_PATH = "Archivos/recuento_de_carreteras.csv"  # <- ruta a tu CSV
CENTER_LAT = 48.8738
CENTER_LON = 2.2950

# Umbrales más permisivos (antes INNER=220, OUTER=340)
RADIUS_M = 360
INNER_M  = 180
OUTER_M  = 300

# BBOX opcional: lo dejamos amplio y NO excluyente (si falta geo_point no filtramos).
APPLY_BBOX = True
BBOX = {
    "lat_min": 48.8685,
    "lat_max": 48.8805,
    "lon_min": 2.2820,
    "lon_max": 2.3080,
}

CHUNKSIZE = 200_000
N_LEGS = 12

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
def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371000.0
    phi1 = math.radians(lat1); phi2 = math.radians(lat2)
    dphi = phi2 - phi1
    dl = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dl/2)**2
    return 2*R*math.asin(math.sqrt(a))

def point_within_radius(lat: float, lon: float, clat: float, clon: float, r_m: float) -> bool:
    return haversine_m(lat, lon, clat, clon) <= r_m

def parse_linestring_coords(geo_shape_str: str) -> Optional[List[Tuple[float, float]]]:
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

def angle_from_center(lat: float, lon: float, clat: float, clon: float) -> float:
    dy = lat - clat
    dx = lon - clon
    ang = math.atan2(dy, dx)
    return ang if ang >= 0 else (ang + 2*math.pi)

def bucket_angle_to_leg(angle_rad: float, n_legs: int = N_LEGS) -> int:
    sector = (2*math.pi) / n_legs
    idx = int(angle_rad // sector)
    return int(max(0, min(n_legs-1, idx)))

# ===========================
# LIMPIEZA Y PARSING
# ===========================
def parse_flow(value) -> float:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return float("nan")
    s = str(value).strip()
    if not s:
        return float("nan")
    s = s.replace(",", ".")
    if s.count(".") > 1:
        parts = s.split(".")
        s = "".join(parts[:-1]) + "." + parts[-1]
    try:
        return float(s)
    except Exception:
        return float("nan")

def parse_dt(value) -> pd.Timestamp:
    try:
        return pd.to_datetime(value, utc=True, errors="coerce")
    except Exception:
        return pd.NaT

def parse_geo_point(s: str) -> Optional[Tuple[float, float]]:
    if not isinstance(s, str) or "," not in s:
        return None
    try:
        lat_str, lon_str = [t.strip() for t in s.split(",")]
        return (float(lat_str), float(lon_str))
    except Exception:
        return None

def in_bbox(lat: float, lon: float, bb=BBOX) -> bool:
    return (bb["lat_min"] <= lat <= bb["lat_max"]) and (bb["lon_min"] <= lon <= bb["lon_max"])

# ===========================
# CLASIFICADOR ROBUSTO
# ===========================
def classify_inbound_outbound_robust(coord_seq: List[Tuple[float, float]],
                                     clat: float, clon: float,
                                     inner_m: float = INNER_M,
                                     outer_m: float = OUTER_M) -> Tuple[str, Optional[float]]:
    """
    Nuevo criterio:
      - Considera TODO el tramo: si min(dist) <= inner y max(dist) >= outer -> CRUZA el borde.
      - Si no cruza pero min(dist) <= RADIUS_M y hay clara tendencia de acercarse/alejarse -> clasifica.
      - Si start y end están a distancias muy similares -> 'ring'.
    """
    if not coord_seq or len(coord_seq) < 2:
        return "unknown", None

    dists = [haversine_m(lat, lon, clat, clon) for (lat, lon) in coord_seq]
    dmin, dmax = float(np.min(dists)), float(np.max(dists))
    start_d, end_d = dists[0], dists[-1]
    n = len(dists)
    k = max(1, n // 3)
    head_m = float(np.median(dists[:k]))
    tail_m = float(np.median(dists[-k:]))

    crosses = (dmin <= inner_m and dmax >= outer_m)

    # regla de tendencia clara
    trend_in = (tail_m < head_m - 20)  # márgenes de 20 m
    trend_out = (head_m < tail_m - 20)

    if crosses or (dmin <= RADIUS_M and (trend_in or trend_out)):
        # determinar ángulo usando el extremo más EXTERNO (fuente de la pierna)
        ext = coord_seq[0] if head_m >= tail_m else coord_seq[-1]
        ang = angle_from_center(ext[0], ext[1], clat, clon)
        return ("inbound", ang) if trend_in else ("outbound", ang)

    # anillo si similaridad alta
    if abs(start_d - end_d) < 15 and abs(head_m - tail_m) < 15:
        return "ring", None

    return "unknown", None

# ===========================
# PIPELINE PRINCIPAL
# ===========================
def main():
    center_lat, center_lon = CENTER_LAT, CENTER_LON

    inbound_rows = []
    outbound_rows = []

    usecols = [v for v in COLS.values()]
    read_kwargs = dict(
        chunksize=CHUNKSIZE,
        usecols=lambda c: c in usecols,
        dtype=str,
        sep=None, engine="python"
    )

    total_rows = 0
    kept_after_bbox = 0
    kept_near = 0

    for chunk in pd.read_csv(CSV_PATH, **read_kwargs):
        total_rows += len(chunk)
        chunk = chunk.rename(columns={v: k for k, v in COLS.items()})

        chunk["flow_val"] = chunk["flow"].apply(parse_flow)
        chunk["dt"] = chunk["datetime"].apply(parse_dt)

        # BBOX no excluyente (solo si geo_point existe)
        if APPLY_BBOX:
            chunk["pt"] = chunk["geo_point"].apply(parse_geo_point)
            mask_keep = chunk["pt"].apply(lambda x: in_bbox(x[0], x[1]) if isinstance(x, tuple) else True)
            # En lugar de descartar todo lo que no cae en bbox, mantenemos también algunas filas
            # sin geo_point para ser evaluadas más adelante por geo_shape.
            chunk = chunk[mask_keep | chunk["pt"].isna()]
        kept_after_bbox += len(chunk)

        coords = chunk["geo_shape"].apply(parse_linestring_coords)
        sub = chunk.assign(coords=coords)
        sub = sub[sub["coords"].notna()]

        # Filtro: que alguna coordenada caiga dentro del radio
        def touches_roundabout(cseq):
            for (lat, lon) in cseq:
                if point_within_radius(lat, lon, center_lat, center_lon, RADIUS_M):
                    return True
            return False

        sub = sub[sub["coords"].apply(touches_roundabout)]
        kept_near += len(sub)

        # Clasificación
        classes = sub["coords"].apply(lambda cs: classify_inbound_outbound_robust(cs, center_lat, center_lon))
        sub["io_flag"] = classes.apply(lambda x: x[0])
        sub["angle"] = classes.apply(lambda x: x[1])

        # debug rápido
        vc = sub["io_flag"].value_counts(dropna=False)
        print(f"Flags en chunk: {dict(vc)}")

        sub = sub[sub["io_flag"].isin(["inbound","outbound"]) & sub["angle"].notna()]
        sub["leg"] = sub["angle"].apply(lambda a: bucket_angle_to_leg(a, n_legs=N_LEGS))

        keep_cols = ["dt", "flow_val", "leg", "libelle", "up_id", "down_id"]
        inbound_rows.append(sub[sub["io_flag"]=="inbound"][keep_cols].copy())
        outbound_rows.append(sub[sub["io_flag"]=="outbound"][keep_cols].copy())

    print(f"Leídas {total_rows:,} filas; tras bbox quedan {kept_after_bbox:,}; cerca de CDG {kept_near:,}.")

    inbound = pd.concat(inbound_rows, ignore_index=True) if inbound_rows else pd.DataFrame(columns=["dt","flow_val","leg","libelle","up_id","down_id"])
    outbound = pd.concat(outbound_rows, ignore_index=True) if outbound_rows else pd.DataFrame(columns=["dt","flow_val","leg","libelle","up_id","down_id"])

    print(f"Filas inbound: {len(inbound):,}  |  outbound: {len(outbound):,}")

    # ===========================
    # 1) LLEGADAS POR ENTRADA
    # ===========================
    inbound = inbound[inbound["dt"].notna()].copy()
    inbound["hour"] = inbound["dt"].dt.floor("h")  # 'h' en lugar de 'H'
    arrivals_hour = (inbound.groupby(["leg","hour"], as_index=False)["flow_val"]
                     .sum()
                     .rename(columns={"flow_val":"veh_per_hour"}))
    arrivals_hour["veh_per_min"] = arrivals_hour["veh_per_hour"] / 60.0
    arrivals_hour.to_csv("arrivals_by_leg_hour.csv", index=False)

    inbound["hod"] = inbound["dt"].dt.tz_convert("Europe/Paris").dt.hour
    arrivals_profile = (inbound.groupby(["leg","hod"], as_index=False)["flow_val"].mean()
                        .rename(columns={"flow_val":"veh_per_hour_avg"}))
    arrivals_profile["veh_per_min_avg"] = arrivals_profile["veh_per_hour_avg"] / 60.0
    arrivals_profile.to_csv("arrivals_by_leg_profile.csv", index=False)

    # ===========================
    # 2) SALIDAS POR PIERNA
    # ===========================
    outbound = outbound[outbound["dt"].notna()].copy()
    outbound_total = (outbound.groupby("leg", as_index=False)["flow_val"].sum()
                      .rename(columns={"flow_val":"veh_out_total"}))
    total_out = outbound_total["veh_out_total"].sum()
    if total_out > 0:
        outbound_total["p_exit_global"] = outbound_total["veh_out_total"] / total_out
    else:
        outbound_total["p_exit_global"] = 0.0
    outbound_total.to_csv("exit_distribution_global.csv", index=False)

    outbound["hod"] = outbound["dt"].dt.tz_convert("Europe/Paris").dt.hour
    exit_by_hod = (outbound.groupby(["hod","leg"], as_index=False)["flow_val"].sum()
                   .rename(columns={"flow_val":"veh_out_hod"}))
    totals_hod = exit_by_hod.groupby("hod", as_index=False)["veh_out_hod"].sum().rename(columns={"veh_out_hod":"tot_hod"})
    exit_by_hod = exit_by_hod.merge(totals_hod, on="hod", how="left")
    exit_by_hod["p_exit_hod"] = np.where(exit_by_hod["tot_hod"]>0, exit_by_hod["veh_out_hod"]/exit_by_hod["tot_hod"], 0.0)
    exit_by_hod[["hod","leg","p_exit_hod"]].to_csv("exit_distribution_by_hod.csv", index=False)

    # ===========================
    # 3) LABELS Y DIAGNÓSTICOS
    # ===========================
    def top_labels(df: pd.DataFrame, colname: str, k: int = 8) -> pd.DataFrame:
        if df.empty:
            return pd.DataFrame(columns=["leg",colname,"count"])
        counts = (df.groupby(["leg", colname]).size().reset_index(name="count"))
        return counts.sort_values(["leg","count"], ascending=[True, False]).groupby("leg").head(k)

    labels_in = top_labels(inbound.rename(columns={"libelle":"libelle_in"}), "libelle_in", k=8)
    labels_out = top_labels(outbound.rename(columns={"libelle":"libelle_out"}), "libelle_out", k=8)
    labels_in.to_csv("leg_labels_inbound_top.csv", index=False)
    labels_out.to_csv("leg_labels_outbound_top.csv", index=False)

    in_totals = (inbound.groupby("leg", as_index=False)["flow_val"].sum()
                 .rename(columns={"flow_val":"inbound_veh_total"}))
    out_totals = (outbound.groupby("leg", as_index=False)["flow_val"].sum()
                  .rename(columns={"flow_val":"outbound_veh_total"}))
    diag = in_totals.merge(out_totals, on="leg", how="outer").fillna(0.0)
    sum_in = diag["inbound_veh_total"].sum()
    sum_out = diag["outbound_veh_total"].sum()
    diag["in_pct"] = diag["inbound_veh_total"] / sum_in if sum_in > 0 else 0.0
    diag["out_pct"] = diag["outbound_veh_total"] / sum_out if sum_out > 0 else 0.0
    diag["pct_diff"] = diag["out_pct"] - diag["in_pct"]
    diag.sort_values("pct_diff", ascending=False).to_csv("diagnostics_in_out_balance.csv", index=False)

    p_sum = outbound_total["p_exit_global"].sum() if not outbound_total.empty else 0.0
    print(f"Suma de p_exit_global = {p_sum:.6f} (debe ~1.0)")
    print("Generados archivos: arrivals_by_leg_hour.csv, arrivals_by_leg_profile.csv, exit_distribution_global.csv, exit_distribution_by_hod.csv, leg_labels_* y diagnostics_in_out_balance.csv")

if __name__ == "__main__":
    main()
