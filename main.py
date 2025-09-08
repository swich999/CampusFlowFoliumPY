from flask import Flask,  Response, render_template_string
import folium
from folium.plugins import HeatMap
import psycopg2
import pandas as pd
import matplotlib.pyplot as plt
import threading
from io import BytesIO
import base64

app = Flask(__name__)

def gerar_grafico():
    conn = psycopg2.connect( 
        host="ep-red-glitter-adx9s4na-pooler.c-2.us-east-1.aws.neon.tech",
        dbname="neondb",
        user="neondb_owner",
        password="npg_8jbKOq2MDZvT",
        sslmode="require"
    )
    cursor = conn.cursor()
    cursor.execute('SELECT DEVICE FROM access;')
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    df = pd.DataFrame(rows, columns=['DEVICE'])
    contagem = df['DEVICE'].value_counts()

    plt.figure(figsize=(10,6))
    contagem.plot(kind='bar', color='skyblue')
    plt.title('Quantidade de acessos por DEVICE')
    plt.xlabel('DEVICE')
    plt.ylabel('Quantidade')
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    img = BytesIO()
    plt.savefig(img, format='png')
    plt.close()
    img.seek(0)
    # codifica em base64 para inserir no HTML
    img_base64 = base64.b64encode(img.getvalue()).decode()
    return img_base64

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

    max_qtd = max((qtd for _, _, qtd in rows), default=1)
    dados = [[lat, lon, qtd / max_qtd] for lat, lon, qtd in rows]

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
        max_val=50   
    ).add_to(mapa)

    return mapa._repr_html_() 

@app.route("/DeviceGrafico")
def device_grafico():
    img_base64 = gerar_grafico()
    html = f"""
    <html>
        <head><title>Gráfico de Dispositivos</title></head>
        <body>
            <h1>Gráfico de Devices</h1>
            <img src="data:image/png;base64,{img_base64}" />
        </body>
    </html>
    """
    return html

@app.route("/mapa")
def mapa():
    return gerar_mapa()

if __name__ == "__main__":
    # roda o gráfico em uma thread separada
    threading.Thread(target=gerar_grafico).start()
    app.run(debug=True)
