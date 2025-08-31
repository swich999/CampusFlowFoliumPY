from flask import Flask, render_template_string
import folium
from folium.plugins import HeatMap
import psycopg2
import os

app = Flask(__name__)

# Configuração para o Folium funcionar no Railway
folium_defaults = folium.folium._default_js
folium.DefaultJs = folium_defaults[0]
folium.DefaultCss = folium_defaults[1]

def gerar_mapa():
    conn = psycopg2.connect(
        host="ep-red-glitter-adx9s4na-pooler.c-2.us-east-1.aws.neon.tech",
        dbname="neondb",
        user="neondb_owner",
        password="npg_8jbKOq2MDZvT",
        sslmode="require"
    )
    cursor = conn.cursor()
    cursor.execute("""
        SELECT latitude, longitude, COUNT(DISTINCT device) as qtd_pessoas
        FROM access
        GROUP BY latitude, longitude
    """)
    rows = cursor.fetchall()
    conn.close()

    # pega o maior valor para normalizar (evita que 1 já fique vermelho)
    max_qtd = max((qtd for _, _, qtd in rows), default=1)

    # normaliza os valores de 0 a 1
    dados = [[lat, lon, qtd / max_qtd] for lat, lon, qtd in rows]

    # centraliza o mapa nos pontos coletados
    if rows:
        latitudes = [lat for lat, _, _ in rows]
        longitudes = [lon for _, lon, _ in rows]
        centro = [sum(latitudes)/len(latitudes), sum(longitudes)/len(longitudes)]
        mapa = folium.Map(location=centro, zoom_start=13)
    else:
        mapa = folium.Map(location=[-15.788497, -47.879873], zoom_start=13)  # Centro do Brasil

    HeatMap(
        dados,
        radius=24,
        blur=20,
        min_opacity=0.5,
        gradient={0: 'blue', 0.5: 'lime', 0.7: 'yellow', 1: 'red'},
        max_zoom=18,
    ).add_to(mapa)

    # Retorna o HTML completo do mapa
    return mapa.get_root().render()

@app.route("/")
@app.route("/mapa")
def mapa():
    mapa_html = gerar_mapa()
    
    # Template HTML completo para garantir que todos os recursos carreguem
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Mapa de Calor - Campus Flow</title>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        <style>
            body { margin: 0; padding: 0; font-family: Arial, sans-serif; }
            #map { width: 100vw; height: 100vh; }
        </style>
    </head>
    <body>
        <div id="map">{mapa_html}</div>
    </body>
    </html>
    """
    
    return render_template_string(html_template.replace("{mapa_html}", mapa_html))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
