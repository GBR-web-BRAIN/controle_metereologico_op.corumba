import folium
from folium.plugins import MiniMap, Fullscreen, MousePosition

from config import CENTRO_OBRA, ZOOM_INICIAL, LAT_OBRA, LON_OBRA


pontos_fixos_obra = [
    {
        "nome": "Centro da obra - OP. CORUMBÁ",
        "coords": [-19.055932, -57.636584],
        "status": "Centro operacional",
        "icone_cor": "red",
        "descricao": "Ponto central de referência do empreendimento.",
    },
    {
        "nome": "Acesso principal",
        "coords": [-19.055300, -57.637200],
        "status": "Logística",
        "icone_cor": "green",
        "descricao": "Acesso de circulação principal da área operacional.",
    },
]


def cor_marker_frente(status):
    if status == "Paralisada":
        return "red"
    if status == "Operando com restrição":
        return "orange"
    if status == "Monitoramento":
        return "blue"
    if status == "Operando normal":
        return "green"
    return "lightgray"


def criar_mapa_obra(frentes_inteligentes):
    mapa = folium.Map(
        location=CENTRO_OBRA,
        zoom_start=ZOOM_INICIAL,
        control_scale=True,
        tiles="OpenStreetMap",
    )

    folium.TileLayer(
        tiles="https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
        attr="Google Satellite",
        name="Satélite",
        overlay=False,
        control=True,
    ).add_to(mapa)

    folium.TileLayer(
        tiles="https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}",
        attr="Google Hybrid",
        name="Híbrido",
        overlay=False,
        control=True,
    ).add_to(mapa)

    for p in pontos_fixos_obra:
        html_popup = f"""
        <div style="width:260px;">
            <h4 style="margin-bottom:8px;">{p['nome']}</h4>
            <b>Status:</b> {p['status']}<br>
            <b>Descrição:</b> {p['descricao']}
        </div>
        """
        folium.Marker(
            location=p["coords"],
            popup=folium.Popup(html_popup, max_width=280),
            tooltip=p["nome"],
            icon=folium.Icon(color=p["icone_cor"], icon="info-sign"),
        ).add_to(mapa)

    for item in frentes_inteligentes:
        html_popup = f"""
        <div style="width:300px;">
            <h4 style="margin-bottom:8px;">{item['nome']}</h4>
            <b>Status do dia:</b> {item['status']}<br>
            <b>Risco automático:</b> {item['risco_auto']}<br>
            <b>Probabilidade pico:</b> {item['pico_prob']:.0f}%<br>
            <b>Chuva pico:</b> {item['pico_chuva']:.1f} mm/h<br>
            <b>Latitude:</b> {item['latitude']:.6f}<br>
            <b>Longitude:</b> {item['longitude']:.6f}<br>
            <b>Observação:</b> {item['observacao'] or 'Sem observação'}<br>
            <b>Atualizado em:</b> {item['atualizado']}
        </div>
        """
        folium.Marker(
            location=[item["latitude"], item["longitude"]],
            popup=folium.Popup(html_popup, max_width=320),
            tooltip=f"{item['nome']} · {item['status']}",
            icon=folium.Icon(color=cor_marker_frente(item["status"]), icon="flag"),
        ).add_to(mapa)

    MiniMap(toggle_display=True).add_to(mapa)
    Fullscreen(position="topright").add_to(mapa)
    MousePosition(position="bottomright").add_to(mapa)
    folium.LayerControl(collapsed=False).add_to(mapa)

    return mapa


def radar_windy_embed(lat=LAT_OBRA, lon=LON_OBRA, zoom=9, layer="radar"):
    return f"""
    <iframe
        width="100%"
        height="520"
        src="https://embed.windy.com/embed2.html?lat={lat}&lon={lon}&detailLat={lat}&detailLon={lon}&width=650&height=520&zoom={zoom}&level=surface&overlay={layer}&product=ecmwf&menu=&message=true&marker=true&calendar=now&pressure=true&type=map&location=coordinates&detail=true&metricWind=km%2Fh&metricTemp=%C2%B0C"
        frameborder="0">
    </iframe>
    """