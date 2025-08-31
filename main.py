from flask import Flask, render_template_string
import folium
from folium.plugins import HeatMap
import psycopg2
import os

app = Flask(__name__)

@app.route("/")
def hello():
    return "Flask está funcionando! Acesse /mapa para ver o mapa."

def gerar_mapa():
    try:
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

        if not rows:
            # Retorna mapa vazio se não houver dados
            mapa = folium.Map(location=[-15.788497, -47.879873], zoom_start=13)
            return mapa._repr_html_()

        max_qtd = max((qtd for _, _, qtd in rows), default=1)
        dados = [[lat, lon, qtd / max_qtd] for lat, lon, qtd in rows]

        latitudes = [lat for lat, _, _ in rows]
        longitudes = [lon for _, lon, _ in rows]
        centro = [sum(latitudes)/len(latitudes), sum(longitudes)/len(longitudes)]
        
        mapa = folium.Map(location=centro, zoom_start=13)
        
        HeatMap(
            dados,
            radius=24,
            blur=20,
            min_opacity=0.5,
            gradient={0: 'blue', 0.5: 'lime', 0.7: 'yellow', 1: 'red'},
            max_zoom=18,
        ).add_to(mapa)

        return mapa._repr_html_()

    except Exception as e:
        print(f"Erro ao gerar mapa: {e}")
        # Fallback: mapa básico
        mapa = folium.Map(location=[-15.788497, -47.879873], zoom_start=13)
        return mapa._repr_html_()

@app.route("/mapa")
def mapa():
    mapa_html = gerar_mapa()
    return render_template_string(f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Mapa de Calor</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body>
        <div style="width:100%; height:100vh;">
            {mapa_html}
        </div>
    </body>
    </html>
    """)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
