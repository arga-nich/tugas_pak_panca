import network
import time
from microdot import Microdot, send_file
import machine

# ==== PIN SETUP ====
soil_pin = machine.ADC(machine.Pin(35))
soil_pin.atten(machine.ADC.ATTN_11DB)
soil_pin.width(machine.ADC.WIDTH_12BIT)

relay_pin = machine.Pin(33, machine.Pin.OUT)
relay_pin.value(1)  # MATI di awal

# ==== BATAS KELEMBAPAN ====
# Nilai aman untuk SEMUA sensor tanah
DRY = 1800        # kering = nilai besar
MOIST = 1300      # lembab
WET = 1000        # basah

# ==== WIFI ====
SSID = "@Ruijie-sDFB6_iot_5G"
PASSWORD = "Iot@12345678"

def wifi_connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)
    print("Connecting WiFi...")
    while not wlan.isconnected():
        time.sleep(0.4)
        print(".", end="")
    print("\nConnected:", wlan.ifconfig())
    return wlan.ifconfig()[0]

ip = wifi_connect()

# ====== MICRO TIME ======
def get_time_str():
    t = time.localtime()
    return "{:02}:{:02}:{:02}".format(t[3], t[4], t[5])

# ==== SENSOR ====
def read_soil():
    total = 0
    for _ in range(10):
        total += soil_pin.read()
        time.sleep(0.01)
    return total // 10

# ==== MODE ====
manual_mode = False
relay_state = "MATI"
last_change_time = "Belum ada perubahan"

def update_relay_auto(value):
    global relay_state, last_change_time

    # LOGIKA AUTO PALING MURNI & PASTI JALAN
    if value > DRY:
        relay_pin.value(0)
        relay_state = "MENYIRAM"
    else:
        relay_pin.value(1)
        relay_state = "MATI"

    last_change_time = get_time_str()


# ==== MICRODOT ====
app = Microdot()

@app.route("/")
def index(request):
    return send_file("templates/uhuy.html")

@app.route("/api/data")
def api_data(request):
    soil_val = read_soil()

    # kategori tanah
    if soil_val > DRY:
        kondisi = "Kering"
    elif soil_val > MOIST:
        kondisi = "Lembab"
    else:
        kondisi = "Basah"

    # AUTO MODE
    if not manual_mode:
        update_relay_auto(soil_val)

    return {
        "soil": soil_val,
        "kategori": kondisi,
        "relay": relay_state,
        "waktu": last_change_time,
        "mode_manual": manual_mode
    }

@app.route("/api/relay/on")
def relay_on(request):
    global manual_mode, relay_state, last_change_time
    manual_mode = True
    relay_pin.value(0)
    relay_state = "MENYIRAM"
    last_change_time = get_time_str()
    return {"status": "ON"}

@app.route("/api/relay/off")
def relay_off(request):
    global manual_mode, relay_state, last_change_time
    manual_mode = True
    relay_pin.value(1)
    relay_state = "MATI"
    last_change_time = get_time_str()
    return {"status": "OFF"}

@app.route("/api/relay/auto")
def relay_auto(request):
    global manual_mode
    manual_mode = False
    return {"status": "AUTO"}

# ==== RUN ====
print("Server jalan di http://{}:5000".format(ip))
app.run(host="0.0.0.0", port=5000)

