from flask import Flask, jsonify, render_template_string
import pywifi
import time
import threading


# ==========================================================
# FLASK
# ==========================================================

app = Flask(__name__)


# ==========================================================
# REDES QUE QUEREMOS MONITOREAR
# ==========================================================

REDES_CONOCIDAS = [
    "IPLAN-016803",
    "casa 2 2.4Ghz_EXT",
    "IPLAN-016803-5G"
]


# ==========================================================
# VARIABLES GLOBALES
# ==========================================================

datos_wifi = []

ultima_actualizacion = "Sin datos todavía"

estado_monitor = "Iniciando..."

lock = threading.Lock()


# ==========================================================
# CALIDAD DE SEÑAL
# ==========================================================

def obtener_calidad(signal):

    if signal >= -50:
        return "Excelente"

    elif signal >= -70:
        return "Buena"

    else:
        return "Débil"


# ==========================================================
# BUSCAR INTERFAZ WIFI
# ==========================================================

def obtener_interfaz():

    try:

        wifi = pywifi.PyWiFi()

        interfaces = wifi.interfaces()

        if not interfaces:

            print("❌ No se encontró ninguna interfaz WiFi.")

            return None

        print()
        print("Interfaces WiFi encontradas:")
        print("------------------------------------------")

        for i, interfaz in enumerate(interfaces):

            try:
                print(f"{i}: {interfaz.name()}")

            except:
                print(f"{i}: Interfaz WiFi")

        print("------------------------------------------")

        iface = interfaces[0]

        print("✅ Interfaz WiFi seleccionada.")

        return iface

    except Exception as e:

        print("❌ Error obteniendo interfaz WiFi:")
        print(e)

        return None


# ==========================================================
# MONITOR WIFI
# ==========================================================

def monitor_wifi():

    global datos_wifi
    global ultima_actualizacion
    global estado_monitor

    print()
    print("==========================================")
    print("       MONITOR WIFI INICIADO")
    print("==========================================")

    print()
    print("Redes que voy a buscar:")

    for red in REDES_CONOCIDAS:
        print(" -", red)

    print()
    print("------------------------------------------")

    iface = None

    while True:

        try:

            # ==============================================
            # BUSCAR ADAPTADOR SI NO TENEMOS UNO
            # ==============================================

            if iface is None:

                print()
                print("🔎 Buscando adaptador WiFi...")

                iface = obtener_interfaz()

                if iface is None:

                    estado_monitor = "Esperando adaptador WiFi..."

                    time.sleep(5)

                    continue


            # ==============================================
            # ESCANEAR
            # ==============================================

            estado_monitor = "Escaneando WiFi..."

            print()
            print("📡 Iniciando escaneo...")

            iface.scan()

            time.sleep(3)


            # ==============================================
            # OBTENER RESULTADOS
            # ==============================================

            resultados = iface.scan_results()

            nuevas_redes = []


            for red in resultados:

                if red.ssid in REDES_CONOCIDAS:

                    signal = red.signal

                    calidad = obtener_calidad(signal)

                    nuevas_redes.append({
                        "ssid": red.ssid,
                        "signal": signal,
                        "calidad": calidad
                    })


            # ==============================================
            # ELIMINAR DUPLICADOS
            # ==============================================

            redes_unicas = {}

            for red in nuevas_redes:

                ssid = red["ssid"]

                if ssid not in redes_unicas:

                    redes_unicas[ssid] = red

                else:

                    if red["signal"] > redes_unicas[ssid]["signal"]:

                        redes_unicas[ssid] = red


            nuevas_redes = list(redes_unicas.values())


            # ==============================================
            # GUARDAR RESULTADOS
            # ==============================================

            with lock:

                datos_wifi = nuevas_redes

                ultima_actualizacion = time.strftime("%H:%M:%S")

                estado_monitor = "Funcionando"


            # ==============================================
            # MOSTRAR EN CONSOLA
            # ==============================================

            print()
            print("==========================================")
            print(
                f"📡 Actualización: {ultima_actualizacion}"
            )
            print("==========================================")


            if nuevas_redes:

                for red in nuevas_redes:

                    print(
                        f"✅ {red['ssid']} | "
                        f"{red['signal']} dBm | "
                        f"{red['calidad']}"
                    )

            else:

                print(
                    "⚠️ No se encontraron las redes conocidas."
                )


            print()
            print("⏳ Próximo escaneo en 5 segundos...")

            time.sleep(5)


        # ==============================================
        # ERROR PYWiFi
        # ==============================================

        except Exception as e:

            print()
            print("==========================================")
            print("⚠️ ERROR DE PYWiFi")
            print("==========================================")
            print(e)
            print("==========================================")


            with lock:

                estado_monitor = (
                    "Reconectando con el adaptador WiFi..."
                )


            iface = None

            print()
            print(
                "🔄 Reiniciando conexión con el adaptador..."
            )

            time.sleep(5)


# ==========================================================
# API
# ==========================================================

@app.route("/api/redes")
def api_redes():

    with lock:

        return jsonify({
            "redes": datos_wifi,
            "ultima_actualizacion": ultima_actualizacion,
            "estado": estado_monitor
        })


# ==========================================================
# PAGINA WEB
# ==========================================================

@app.route("/")
def inicio():

    return render_template_string("""
<!DOCTYPE html>

<html lang="es">

<head>

<meta charset="UTF-8">

<meta name="viewport"
      content="width=device-width, initial-scale=1.0">

<title>Monitor WiFi | Casa</title>


<style>

/* ========================================================
   VARIABLES
   ======================================================== */

:root {

    --fondo-1: #07111f;
    --fondo-2: #0d1f35;

    --texto: #f4f8ff;
    --texto-suave: #91a4ba;

    --verde: #27e58c;
    --amarillo: #ffd166;
    --rojo: #ff5c72;
    --azul: #55b8ff;

}


/* ========================================================
   RESET
   ======================================================== */

* {

    box-sizing: border-box;

}


body {

    margin: 0;

    min-height: 100vh;

    font-family:
        Arial,
        Helvetica,
        sans-serif;

    color: var(--texto);

    background:

        radial-gradient(
            circle at 15% 10%,
            rgba(46, 145, 255, 0.18),
            transparent 30%
        ),

        radial-gradient(
            circle at 85% 80%,
            rgba(39, 229, 140, 0.10),
            transparent 30%
        ),

        linear-gradient(
            145deg,
            var(--fondo-1),
            var(--fondo-2)
        );

    padding: 25px;

}


/* ========================================================
   CONTENEDOR
   ======================================================== */

.app {

    width: 100%;

    max-width: 1100px;

    margin: auto;

}


/* ========================================================
   ENCABEZADO
   ======================================================== */

.header {

    position: relative;

    overflow: hidden;

    padding: 32px;

    margin-bottom: 22px;

    border-radius: 28px;

    background:
        linear-gradient(
            135deg,
            rgba(255,255,255,0.10),
            rgba(255,255,255,0.04)
        );

    border: 1px solid rgba(255,255,255,0.10);

    box-shadow:
        0 25px 70px rgba(0,0,0,0.35);

}


.header::before {

    content: "";

    position: absolute;

    width: 250px;

    height: 250px;

    border-radius: 50%;

    background:
        radial-gradient(
            circle,
            rgba(85,184,255,0.18),
            transparent 70%
        );

    right: -80px;

    top: -120px;

}


.header-content {

    position: relative;

    z-index: 2;

}


.logo {

    font-size: 50px;

    margin-bottom: 5px;

}


h1 {

    margin: 0;

    font-size: clamp(30px, 6vw, 48px);

    letter-spacing: -1px;

}


.subtitle {

    margin-top: 8px;

    color: var(--texto-suave);

    font-size: 16px;

}


/* ========================================================
   ESTADO GENERAL
   ======================================================== */

.status {

    display: flex;

    flex-wrap: wrap;

    align-items: center;

    gap: 12px;

    margin-top: 25px;

}


.status-pill {

    display: inline-flex;

    align-items: center;

    gap: 8px;

    padding: 10px 16px;

    border-radius: 50px;

    background: rgba(39,229,140,0.10);

    border: 1px solid rgba(39,229,140,0.20);

    color: var(--verde);

    font-weight: bold;

}


.status-dot {

    width: 9px;

    height: 9px;

    border-radius: 50%;

    background: var(--verde);

    box-shadow:
        0 0 12px var(--verde);

    animation: pulse 1.5s infinite;

}


.update {

    color: var(--texto-suave);

    font-size: 14px;

}


@keyframes pulse {

    0% {
        transform: scale(1);
        opacity: 1;
    }

    50% {
        transform: scale(1.5);
        opacity: 0.5;
    }

    100% {
        transform: scale(1);
        opacity: 1;
    }

}


/* ========================================================
   TITULO DE REDES
   ======================================================== */

.section-title {

    display: flex;

    justify-content: space-between;

    align-items: center;

    margin: 25px 5px 15px;

}


.section-title h2 {

    margin: 0;

    font-size: 21px;

}


.network-count {

    color: var(--texto-suave);

    font-size: 14px;

}


/* ========================================================
   GRID
   ======================================================== */

.network-grid {

    display: grid;

    grid-template-columns:
        repeat(
            auto-fit,
            minmax(280px, 1fr)
        );

    gap: 18px;

}


/* ========================================================
   TARJETA
   ======================================================== */

.network {

    position: relative;

    overflow: hidden;

    padding: 25px;

    min-height: 290px;

    border-radius: 25px;

    background:
        linear-gradient(
            145deg,
            rgba(255,255,255,0.10),
            rgba(255,255,255,0.045)
        );

    border: 1px solid rgba(255,255,255,0.09);

    box-shadow:
        0 18px 45px rgba(0,0,0,0.25);

    transition:
        transform 0.3s,
        border-color 0.3s,
        box-shadow 0.3s;

}


.network:hover {

    transform: translateY(-6px);

    box-shadow:
        0 25px 55px rgba(0,0,0,0.40);

}


.network::after {

    content: "";

    position: absolute;

    width: 150px;

    height: 150px;

    right: -70px;

    bottom: -80px;

    border-radius: 50%;

    background:
        radial-gradient(
            circle,
            var(--accent),
            transparent 70%
        );

    opacity: 0.12;

}


/* ========================================================
   COLORES SEGUN CALIDAD
   ======================================================== */

.network.excelente {

    --accent: var(--verde);

    border-color:
        rgba(39,229,140,0.25);

}


.network.buena {

    --accent: var(--amarillo);

    border-color:
        rgba(255,209,102,0.25);

}


.network.debil {

    --accent: var(--rojo);

    border-color:
        rgba(255,92,114,0.25);

}


/* ========================================================
   NOMBRE
   ======================================================== */

.network-name {

    font-size: 19px;

    font-weight: bold;

    word-break: break-word;

    margin-bottom: 22px;

}


.wifi-icon {

    margin-right: 8px;

}


/* ========================================================
   SEÑAL
   ======================================================== */

.signal-container {

    text-align: center;

    margin: 10px 0 22px;

}


.signal-number {

    font-size: 38px;

    font-weight: 800;

    letter-spacing: -1px;

}


.signal-unit {

    font-size: 14px;

    color: var(--texto-suave);

    margin-left: 4px;

}


/* ========================================================
   BARRA
   ======================================================== */

.signal-bar {

    width: 100%;

    height: 12px;

    margin-top: 16px;

    background: rgba(255,255,255,0.08);

    border-radius: 20px;

    overflow: hidden;

}


.signal-fill {

    height: 100%;

    border-radius: 20px;

    background: var(--accent);

    box-shadow:
        0 0 15px var(--accent);

    transition:
        width 0.7s ease;

}


/* ========================================================
   CALIDAD
   ======================================================== */

.quality {

    display: inline-flex;

    align-items: center;

    gap: 7px;

    padding: 8px 13px;

    border-radius: 50px;

    background: rgba(255,255,255,0.07);

    color: var(--accent);

    font-weight: bold;

    font-size: 13px;

}


.quality-dot {

    width: 7px;

    height: 7px;

    border-radius: 50%;

    background: var(--accent);

}


/* ========================================================
   GRAFICO
   ======================================================== */

.chart-title {

    margin-top: 25px;

    margin-bottom: 8px;

    color: var(--texto-suave);

    font-size: 12px;

}


canvas {

    width: 100% !important;

    height: 65px !important;

    opacity: 0.85;

}


/* ========================================================
   SIN RED
   ======================================================== */

.empty {

    grid-column: 1 / -1;

    padding: 50px 25px;

    text-align: center;

    border-radius: 25px;

    background:
        rgba(255,255,255,0.05);

    border: 1px dashed
        rgba(255,255,255,0.15);

}


.empty-icon {

    font-size: 45px;

    margin-bottom: 15px;

}


.empty h3 {

    margin: 0 0 8px;

}


.empty p {

    color: var(--texto-suave);

    margin: 0;

}


/* ========================================================
   FOOTER
   ======================================================== */

.footer {

    text-align: center;

    color: var(--texto-suave);

    font-size: 13px;

    padding: 25px 0 10px;

}


/* ========================================================
   CELULAR
   ======================================================== */

@media (max-width: 600px) {

    body {

        padding: 12px;

    }


    .header {

        padding: 25px 20px;

        border-radius: 22px;

    }


    .logo {

        font-size: 40px;

    }


    .network {

        min-height: auto;

    }


    .signal-number {

        font-size: 34px;

    }

}

</style>

</head>


<body>


<div class="app">


    <!-- ==============================================
         ENCABEZADO
    =============================================== -->

    <header class="header">

        <div class="header-content">

            <div class="logo">
                📡
            </div>

            <h1>
                Monitor WiFi
            </h1>

            <div class="subtitle">
                Estado de las redes de casa
            </div>


            <div class="status">

                <div class="status-pill">

                    <span class="status-dot"></span>

                    <span id="estado">
                        Iniciando...
                    </span>

                </div>


                <div class="update">

                    Última actualización:

                    <strong id="hora">
                        --:--:--
                    </strong>

                </div>

            </div>

        </div>

    </header>



    <!-- ==============================================
         TITULO
    =============================================== -->

    <div class="section-title">

        <h2>
            Redes monitoreadas
        </h2>

        <div class="network-count">

            <span id="cantidad">
                0
            </span>

            detectadas

        </div>

    </div>



    <!-- ==============================================
         REDES
    =============================================== -->

    <main
        id="redes"
        class="network-grid"
    >

        <div class="empty">

            <div class="empty-icon">
                📡
            </div>

            <h3>
                Buscando redes...
            </h3>

            <p>
                El monitor está realizando el primer escaneo.
            </p>

        </div>

    </main>



    <!-- ==============================================
         FOOTER
    =============================================== -->

    <footer class="footer">

        🔄 Actualización automática cada 5 segundos

    </footer>


</div>



<script>


// ========================================================
// HISTORIAL DE SEÑAL
// ========================================================

const historial = {};


// ========================================================
// CONVERTIR DBM A PORCENTAJE VISUAL
// ========================================================

function calcularPorcentaje(signal) {

    // -30 dBm = 100%
    // -90 dBm = 0%

    let porcentaje =
        ((signal + 90) / 60) * 100;


    porcentaje =
        Math.max(
            0,
            Math.min(
                100,
                porcentaje
            )
        );


    return Math.round(porcentaje);

}


// ========================================================
// CREAR GRAFICO
// ========================================================

function dibujarGrafico(canvas, valores) {

    const ctx =
        canvas.getContext("2d");


    const width =
        canvas.width =
        canvas.clientWidth * window.devicePixelRatio;


    const height =
        canvas.height =
        canvas.clientHeight * window.devicePixelRatio;


    ctx.scale(
        window.devicePixelRatio,
        window.devicePixelRatio
    );


    const w =
        canvas.clientWidth;


    const h =
        canvas.clientHeight;


    ctx.clearRect(
        0,
        0,
        w,
        h
    );


    if (valores.length < 2) {

        return;

    }


    const min =
        Math.min(...valores) - 3;


    const max =
        Math.max(...valores) + 3;


    const rango =
        max - min || 1;


    ctx.beginPath();


    valores.forEach(
        (valor, indice) => {

            const x =
                (indice /
                (valores.length - 1))
                * w;


            const y =
                h -
                ((valor - min) / rango)
                * h;


            if (indice === 0) {

                ctx.moveTo(
                    x,
                    y
                );

            } else {

                ctx.lineTo(
                    x,
                    y
                );

            }

        }
    );


    ctx.strokeStyle =
        "rgba(255,255,255,0.65)";


    ctx.lineWidth = 2;


    ctx.stroke();

}


// ========================================================
// ACTUALIZAR WIFI
// ========================================================

async function actualizarWifi() {

    try {

        const respuesta =
            await fetch(
                "/api/redes"
            );


        const datos =
            await respuesta.json();


        // ================================================
        // ESTADO
        // ================================================

        document.getElementById(
            "estado"
        ).textContent =
            datos.estado;


        document.getElementById(
            "hora"
        ).textContent =
            datos.ultima_actualizacion;


        document.getElementById(
            "cantidad"
        ).textContent =
            datos.redes.length;


        const contenedor =
            document.getElementById(
                "redes"
            );


        // ================================================
        // NO HAY REDES
        // ================================================

        if (datos.redes.length === 0) {

            contenedor.innerHTML = `

                <div class="empty">

                    <div class="empty-icon">
                        📡
                    </div>

                    <h3>
                        No se encontraron redes
                    </h3>

                    <p>
                        Las redes conocidas no están
                        disponibles en este momento.
                    </p>

                </div>

            `;

            return;

        }


        // ================================================
        // LIMPIAR
        // ================================================

        contenedor.innerHTML = "";


        // ================================================
        // CREAR TARJETAS
        // ================================================

        datos.redes.forEach(
            (red, indice) => {


                // ----------------------------------------
                // PORCENTAJE
                // ----------------------------------------

                const porcentaje =
                    calcularPorcentaje(
                        red.signal
                    );


                // ----------------------------------------
                // CLASE
                // ----------------------------------------

                let clase = "";


                if (
                    red.calidad ===
                    "Excelente"
                ) {

                    clase =
                        "excelente";

                }

                else if (
                    red.calidad ===
                    "Buena"
                ) {

                    clase =
                        "buena";

                }

                else {

                    clase =
                        "debil";

                }


                // ----------------------------------------
                // HISTORIAL
                // ----------------------------------------

                if (
                    !historial[red.ssid]
                ) {

                    historial[red.ssid] =
                        [];

                }


                historial[red.ssid].push(
                    red.signal
                );


                // Máximo 20 puntos

                if (
                    historial[red.ssid].length
                    > 20
                ) {

                    historial[red.ssid].shift();

                }


                // ----------------------------------------
                // TARJETA
                // ----------------------------------------

                const tarjeta =
                    document.createElement(
                        "article"
                    );


                tarjeta.className =
                    `network ${clase}`;


                tarjeta.innerHTML = `

                    <div class="network-name">

                        <span class="wifi-icon">
                            📶
                        </span>

                        ${red.ssid}

                    </div>


                    <div class="signal-container">

                        <div class="signal-number">

                            ${red.signal}

                            <span class="signal-unit">
                                dBm
                            </span>

                        </div>


                        <div class="signal-bar">

                            <div
                                class="signal-fill"
                                style="
                                    width:
                                    ${porcentaje}%
                                "
                            ></div>

                        </div>

                    </div>


                    <div class="quality">

                        <span
                            class="quality-dot"
                        ></span>

                        ${red.calidad}

                    </div>


                    <div class="chart-title">

                        Historial de señal

                    </div>


                    <canvas></canvas>

                `;


                contenedor.appendChild(
                    tarjeta
                );


                // ----------------------------------------
                // DIBUJAR HISTORIAL
                // ----------------------------------------

                const canvas =
                    tarjeta.querySelector(
                        "canvas"
                    );


                dibujarGrafico(
                    canvas,
                    historial[red.ssid]
                );

            }
        );


    }

    catch (error) {

        console.error(
            "Error actualizando WiFi:",
            error
        );

    }

}


// ========================================================
// PRIMERA CARGA
// ========================================================

actualizarWifi();


// ========================================================
// ACTUALIZAR CADA 5 SEGUNDOS
// ========================================================

setInterval(
    actualizarWifi,
    5000
);


</script>


</body>

</html>
""")


# ==========================================================
# INICIAR PROGRAMA
# ==========================================================

if __name__ == "__main__":

    print()
    print("==========================================")
    print("       INICIANDO MONITOR WIFI")
    print("==========================================")

    hilo = threading.Thread(
        target=monitor_wifi,
        daemon=True
    )

    hilo.start()


    print()
    print("🌐 Servidor Flask:")
    print("http://127.0.0.1:5000")

    print()
    print("📱 Para otros dispositivos:")
    print("http://IP-DE-TU-PC:5000")

    print()
    print("==========================================")


    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False,
        use_reloader=False
    )