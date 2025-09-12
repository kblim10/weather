import paho.mqtt.client as mqtt
import time
import json
import random

# --- (OPSIONAL) GANTI DENGAN LIBRARY SENSOR ANDA ---
# Anda mungkin perlu library seperti lgpio atau adafruit_circuitpython_bme280
# import lgpio
# import board
# import adafruit_bme280
# ---------------------------------------------------


# --- KONFIGURASI UNTUK SERVER LOKAL ---
# Broker MQTT adalah Raspberry Pi itu sendiri
MQTT_HOST = "localhost"  # atau "127.0.0.1"

# Port standar MQTT (tanpa enkripsi)
MQTT_PORT = 1883

# Topik MQTT untuk komunikasi lokal
MQTT_TOPIC = "weather/station/local"


# --- FUNGSI PEMBACAAN SENSOR ---
#
# PENTING: FUNGSI DI BAWAH INI MASIH SIMULASI.
# GANTI ISI FUNGSI-FUNGSI INI DENGAN KODE ASLI UNTUK MEMBACA
# SENSOR DARI ORACLE WEATHER STATION HAT ANDA.
#
def setup_sensors():
    """Fungsi untuk inisialisasi awal sensor (jika diperlukan)."""
    print("Inisialisasi sensor...")
    # Anda bisa menambahkan kode setup sensor di sini


def baca_suhu_udara():
    """Membaca sensor suhu dan kelembaban."""
    # KODE SIMULASI:
    suhu = round(random.uniform(25.0, 34.0), 2)
    kelembaban = round(random.uniform(60.0, 95.0), 2)
    return suhu, kelembaban

def baca_kecepatan_angin():
    """Membaca sensor kecepatan angin (anemometer)."""
    # KODE SIMULASI:
    return round(random.uniform(0.0, 15.0), 2)

def baca_arah_angin():
    """Membaca sensor arah angin (wind vane)."""
    # KODE SIMULASI:
    return random.choice(["Utara", "Timur", "Selatan", "Barat"])

def baca_curah_hujan():
    """Membaca sensor curah hujan (rain gauge)."""
    # KODE SIMULASI:
    return round(random.uniform(0.0, 5.0), 2)


# --- FUNGSI UTAMA PROGRAM ---
def on_connect(client, userdata, flags, rc):
    """Callback yang dipanggil saat koneksi ke broker berhasil."""
    if rc == 0:
        print("✅ Sensor terhubung ke Broker MQTT Lokal!")
    else:
        print(f"❌ Gagal terhubung ke broker lokal, kode error: {rc}")

def run_station():
    """Fungsi utama untuk menjalankan stasiun cuaca."""
    # Inisialisasi MQTT Client
    client = mqtt.Client(client_id="sensor-publisher")
    client.on_connect = on_connect
    
    # Coba hubungkan ke broker
    try:
        print(f"🔌 Menghubungkan ke broker di {MQTT_HOST}...")
        client.connect(MQTT_HOST, MQTT_PORT)
    except Exception as e:
        print(f"❌ Gagal terhubung ke broker lokal. Pastikan Mosquitto sudah terinstal dan berjalan. Error: {e}")
        return

    # Menjalankan loop di background untuk menjaga koneksi
    client.loop_start()
    
    # Panggil fungsi setup sensor sekali di awal
    setup_sensors()
    
    try:
        while True:
            # Baca semua data dari sensor
            suhu, kelembaban = baca_suhu_udara()
            kec_angin = baca_kecepatan_angin()
            arah_angin = baca_arah_angin()
            
            # Buat paket data dalam format JSON
            data_payload = json.dumps({
                "temperature": suhu,
                "humidity": kelembaban,
                "wind_speed_kph": kec_angin,
                "wind_direction": arah_angin,
                "rainfall_mm": baca_curah_hujan() # Contoh memanggil langsung
            })
            
            # Kirim (publish) data ke topik MQTT
            result = client.publish(MQTT_TOPIC, data_payload)
            
            status = result[0]
            if status == 0:
                print(f"🛰️  Mengirim data ke web server lokal: {data_payload}")
            else:
                print(f"⚠️ Gagal mengirim pesan ke topik {MQTT_TOPIC}")
            
            # Tunggu 10 detik sebelum pengiriman berikutnya
            time.sleep(10)
            
    except KeyboardInterrupt:
        print("\n🛑 Program sensor dihentikan oleh pengguna.")
    finally:
        print("🔌 Memutuskan koneksi sensor...")
        client.loop_stop()
        client.disconnect()

if __name__ == '__main__':
    run_station()
