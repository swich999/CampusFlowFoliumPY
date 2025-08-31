from flask import Flask
import folium
from folium.plugins import HeatMap
import psycopg2

app = Flask(__name__)

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
        mapa = folium.Map(zoom_start=2)

    HeatMap(
    dados,
    radius=24,
    blur=20,
    min_opacity=0.5,
    gradient={0: 'blue', 0.5: 'lime', 0.7: 'yellow', 1: 'red'},
    max_zoom=18,
    max_val=50   # 🔥 fixa a escala até 50 pessoas
    ).add_to(mapa)

    return mapa._repr_html_()  # retorna o HTML direto

@app.route("/mapa")
def mapa():
    return gerar_mapa()

if __name__ == "__main__":
    app.run(debug=True)
