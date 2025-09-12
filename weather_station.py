import paho.mqtt.client as mqtt
import time
import json
import board
import adafruit_bme280.basic as adafruit_bme280
import lgpio
import spidev
import math

# --- KONFIGURASI PERANGKAT KERAS (MUNGKIN PERLU DISESUAIKAN) ---
WIND_SPEED_PIN = 6  # Pin GPIO untuk sensor kecepatan angin
RAIN_PIN = 5        # Pin GPIO untuk sensor curah hujan
SPI_BUS = 0         # Bus SPI
SPI_DEVICE = 0      # Device SPI (untuk ADC sensor arah angin)
ADC_CHANNEL = 0     # Channel ADC yang terhubung ke sensor arah angin

# --- KONFIGURASI MQTT (LOKAL) ---
MQTT_HOST = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "weather/station/local"

# --- Variabel Global untuk Sensor ---
bme280 = None
lgpio_handle = None

# Variabel untuk menghitung pulsa dari sensor
wind_clicks = 0
rain_tips = 0

# Objek untuk SPI
spi = None

# Tabel referensi untuk Arah Angin (nilai ADC -> Arah)
# Nilai ini adalah standar umum, mungkin perlu kalibrasi
WIND_DIR_LOOKUP = {
    909: "Utara (N)", 802: "Timur Laut (NE)", 859: "Timur (E)",
    473: "Tenggara (SE)", 552: "Selatan (S)", 150: "Barat Daya (SW)",
    291: "Barat (W)", 656: "Barat Laut (NW)"
}

# --- FUNGSI-FUNGSI PROGRAM ---

def wind_callback(chip, gpio, level, tick):
    """Callback yang dipanggil setiap kali sensor angin berputar."""
    global wind_clicks
    wind_clicks += 1

def rain_callback(chip, gpio, level, tick):
    """Callback yang dipanggil setiap kali ember hujan terbalik."""
    global rain_tips
    rain_tips += 1

def setup_sensors():
    """Inisialisasi semua sensor saat program dimulai."""
    global bme280, lgpio_handle, spi
    
    # 1. Setup BME280 (Suhu & Kelembaban)
    try:
        print("Mencoba inisialisasi sensor BME280...")
        i2c = board.I2C()
        bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c)
        print("✅ Sensor BME280 berhasil diinisialisasi.")
    except Exception as e:
        print(f"❌ GAGAL inisialisasi BME280: {e}")
        bme280 = None

    # 2. Setup Sensor Hujan & Angin (GPIO)
    try:
        print("Mencoba inisialisasi sensor GPIO (Hujan & Angin)...")
        lgpio_handle = lgpio.gpiochip_open(0)
        # Set pin sebagai input dengan pull-up resistor internal
        lgpio.gpio_claim_input(lgpio_handle, WIND_SPEED_PIN, lgpio.SET_PULL_UP)
        lgpio.gpio_claim_input(lgpio_handle, RAIN_PIN, lgpio.SET_PULL_UP)
        # Atur callback untuk deteksi pulsa (saat pin menjadi LOW)
        lgpio.callback(lgpio_handle, WIND_SPEED_PIN, lgpio.FALLING_EDGE, wind_callback)
        lgpio.callback(lgpio_handle, RAIN_PIN, lgpio.FALLING_EDGE, rain_callback)
        print("✅ Sensor Hujan & Angin berhasil diinisialisasi.")
    except Exception as e:
        print(f"❌ GAGAL inisialisasi GPIO: {e}")
        
    # 3. Setup ADC untuk Arah Angin (SPI)
    try:
        print("Mencoba inisialisasi ADC (Arah Angin)...")
        spi = spidev.SpiDev()
        spi.open(SPI_BUS, SPI_DEVICE)
        spi.max_speed_hz = 1000000
        print("✅ ADC berhasil diinisialisasi.")
    except Exception as e:
        print(f"❌ GAGAL inisialisasi ADC/SPI: {e}")
        spi = None

def baca_suhu_udara():
    if bme280:
        return round(bme280.temperature, 2), round(bme280.relative_humidity, 2)
    return "N/A", "N/A"

def baca_kecepatan_angin(interval_detik=10):
    global wind_clicks
    # Faktor konversi: 1 putaran/detik = 2.4 km/jam
    # Radius anemometer standar adalah sekitar 9cm
    rotations = wind_clicks / 2.0 # Dua klik per rotasi
    speed_kph = (rotations / interval_detik) * 2.4
    wind_clicks = 0 # Reset counter
    return round(speed_kph, 2)

def baca_curah_hujan():
    global rain_tips
    # Setiap tip ember setara dengan 0.2794 mm hujan
    rainfall_mm = rain_tips * 0.2794
    rain_tips = 0 # Reset counter
    return round(rainfall_mm, 2)

def baca_arah_angin():
    if not spi:
        return "N/A"
    try:
        # Membaca data dari ADC (misal, MCP3008)
        r = spi.xfer2([1, (8 + ADC_CHANNEL) << 4, 0])
        adc_out = ((r[1] & 3) << 8) + r[2]
        
        # Cari nilai ADC yang paling mendekati di tabel lookup
        closest_adc = min(WIND_DIR_LOOKUP.keys(), key=lambda key: abs(key - adc_out))
        return WIND_DIR_LOOKUP[closest_adc]
    except Exception as e:
        print(f"⚠️ Gagal membaca ADC Arah Angin: {e}")
        return "Error"

def on_connect(client, userdata, flags, rc):
    if rc == 0: print("🛰️  Terhubung ke Broker MQTT Lokal!")
    else: print(f"❌ Gagal terhubung ke broker, kode: {rc}")

def run_station(interval_detik=10):
    client = mqtt.Client(client_id="sensor-publisher-real")
    client.on_connect = on_connect
    try: client.connect(MQTT_HOST, MQTT_PORT)
    except Exception as e:
        print(f"❌ Gagal terhubung: {e}"); return
    client.loop_start()
    setup_sensors()
    
    try:
        while True:
            time.sleep(interval_detik)
            
            suhu, kelembaban = baca_suhu_udara()
            kec_angin = baca_kecepatan_angin(interval_detik)
            arah_angin = baca_arah_angin()
            hujan = baca_curah_hujan()
            
            data_payload = json.dumps({
                "temperature": suhu, "humidity": kelembaban,
                "wind_speed_kph": kec_angin, "wind_direction": arah_angin,
                "rainfall_mm": hujan
            })
            
            result = client.publish(MQTT_TOPIC, data_payload)
            if result[0] == 0: print(f"📤 Mengirim data: {data_payload}")
            else: print(f"⚠️ Gagal mengirim pesan.")
            
    except KeyboardInterrupt: print("\n🛑 Program dihentikan.")
    finally:
        print("🔌 Memutuskan koneksi...")
        if lgpio_handle: lgpio.gpiochip_close(lgpio_handle)
        if spi: spi.close()
        client.loop_stop(); client.disconnect()

if __name__ == '__main__':
    run_station(interval_detik=10)
