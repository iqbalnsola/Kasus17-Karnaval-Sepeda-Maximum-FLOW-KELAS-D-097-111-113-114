import math
import requests
import polyline
import pandas as pd
import folium


ASAL = (-7.594776, 110.939914)
TUJUAN = (-7.59674260198687, 110.95958031499016)


VIA = {
    1: [(-7.595175878904789, 110.93984370864753), (-7.595324, 110.940467),(-7.597605542855908, 110.95013822159355), (-7.598291, 110.952973), (-7.597458, 110.957858), (-7.59674260198687, 110.95958031499016)],    # contoh: [(-7.5950, 110.9450), (-7.5958, 110.9520)]
    2: [(-7.594776, 110.939914), (-7.595331, 110.940464), (-7.593971721665238, 110.94095833716284), (-7.598468, 110.957354), (-7.59674260198687, 110.95958031499016)],
    3: [(-7.594776, 110.939914), (-7.596485, 110.940146), (-7.599175, 110.952562), (-7.598428, 110.957444), (-7.595770, 110.959188), (-7.59674260198687, 110.95958031499016)],
}

INTERVAL = 100   
WARNA = ["#1a47e0", "#ff6d00", "#d500f9"]


def haversine(a, b):
    R = 6371000
    p1, p2 = math.radians(a[0]), math.radians(b[0])
    dp, dl = p2 - p1, math.radians(b[1] - a[1])
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))


def jarak_kumulatif(titik):
    cum = [0.0]
    for a, b in zip(titik[:-1], titik[1:]):
        cum.append(cum[-1] + haversine(a, b))
    return cum


def titik_pada(titik, cum, d):
    """Koordinat pada jarak d meter dari awal garis (interpolasi linear)."""
    for i in range(1, len(cum)):
        if cum[i] >= d:
            seg = cum[i] - cum[i - 1]
            t = 0 if seg == 0 else (d - cum[i - 1]) / seg
            return (titik[i - 1][0] + t * (titik[i][0] - titik[i - 1][0]),
                    titik[i - 1][1] + t * (titik[i][1] - titik[i - 1][1]))
    return titik[-1]


def bangun_node(titik, maneuvers):
    cum = jarak_kumulatif(titik)
    info = {0: "Mulai", len(titik) - 1: "Tiba"}
    for m in maneuvers:
        idx = m["begin_shape_index"]
        if idx not in info:
            info[idx] = m.get("instruction", "-")
    kunci = sorted(info)

    node = []
    for k, idx in enumerate(kunci):
        tipe = "asal" if idx == 0 else "tujuan" if idx == len(titik) - 1 else "belokan"
        node.append({"tipe": tipe, "lat": titik[idx][0], "lon": titik[idx][1],
                     "jarak_m": cum[idx], "instruksi": info[idx]})
        if k + 1 < len(kunci):
            awal, akhir = cum[idx], cum[kunci[k + 1]]
            panjang = akhir - awal
            n = round(panjang / INTERVAL)
            for j in range(1, n):            
                d = awal + j * panjang / n
                lat, lon = titik_pada(titik, cum, d)
                node.append({"tipe": "interval", "lat": lat, "lon": lon,
                             "jarak_m": d, "instruksi": "-"})
    return node


def minta_rute(via=None, alternatif=0):
    lokasi = [{"lat": ASAL[0], "lon": ASAL[1]}]
    for v in (via or []):
        lokasi.append({"lat": v[0], "lon": v[1], "type": "through"})
    lokasi.append({"lat": TUJUAN[0], "lon": TUJUAN[1]})
    body = {"locations": lokasi, "costing": "pedestrian",
            "directions_options": {"units": "kilometers", "language": "id-ID"}}
    if alternatif:
        body["alternates"] = alternatif
    r = requests.post("https://valhalla1.openstreetmap.de/route", json=body, timeout=60)
    r.raise_for_status()
    d = r.json()
    return [d["trip"]] + [a["trip"] for a in d.get("alternates", [])]


# ---- ambil rute ----
trips = []
if any(VIA.values()):
    print("Mode VIA (mengikuti titik singgah)")
    for i in sorted(VIA):
        if VIA[i] or (i == 1):
            trips.append(minta_rute(via=VIA[i])[0])
else:
    print("Mode otomatis (alternatif Valhalla)")
    trips = minta_rute(alternatif=2)
print(f"Ditemukan {len(trips)} rute")

# ---- peta ----
pusat = ((ASAL[0] + TUJUAN[0]) / 2, (ASAL[1] + TUJUAN[1]) / 2)
peta = folium.Map(location=pusat, zoom_start=15, tiles=None)
folium.TileLayer(
    tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}",
    attr="Esri", name="Peta Jalan").add_to(peta)
folium.TileLayer(
    tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    attr="Esri", name="Satelit", show=False).add_to(peta)

semua_node = []
for i, trip in enumerate(trips):
    nama = f"Rute {i + 1}"
    warna = WARNA[i % len(WARNA)]
    leg = trip["legs"][0]
    titik = polyline.decode(leg["shape"], 6)
    node = bangun_node(titik, leg["maneuvers"])
    total_km = trip["summary"]["length"]

    grup = folium.FeatureGroup(name=f"{nama} ({total_km:.2f} km, {len(node)} node)")
    folium.PolyLine(titik, color="white", weight=9, opacity=0.9).add_to(grup)
    folium.PolyLine(titik, color=warna, weight=5, tooltip=f"{nama} | {total_km:.2f} km").add_to(grup)

    for n_idx, n in enumerate(node, start=1):
        semua_node.append({"rute": nama, "urutan": n_idx, "tipe": n["tipe"],
                           "lat": round(n["lat"], 7), "lon": round(n["lon"], 7),
                           "jarak_kumulatif_m": round(n["jarak_m"], 1),
                           "instruksi": n["instruksi"]})
        besar = n["tipe"] != "interval"
        folium.CircleMarker(
            (n["lat"], n["lon"]), radius=6 if besar else 3,
            color="black" if besar else "white", weight=1.5 if besar else 1,
            fill=True, fill_color=warna, fill_opacity=1,
            popup=folium.Popup(
                f"<b>{nama}</b> | node {n_idx} ({n['tipe']})<br>{n['instruksi']}<br>"
                f"{n['lat']:.7f}, {n['lon']:.7f}<br>{n['jarak_m']:.0f} m dari awal",
                max_width=260),
        ).add_to(grup)

    grup.add_to(peta)
    print(f"{nama}: {total_km:.2f} km, {len(node)} node "
          f"({sum(1 for n in node if n['tipe'] != 'interval')} penting)")

folium.Marker(ASAL, tooltip="Asal", icon=folium.Icon(color="green")).add_to(peta)
folium.Marker(TUJUAN, tooltip="Tujuan", icon=folium.Icon(color="red")).add_to(peta)
folium.LayerControl().add_to(peta)

peta.save("peta_rute.html")
pd.DataFrame(semua_node).to_csv("node_rute.csv", index=False)
print("Selesai: peta_rute.html, node_rute.csv")