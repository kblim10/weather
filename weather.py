import paho.mqtt.client as mqtt
import time
import json
import random

# --- (OPSIONAL) GANTI DENGAN LIBRARY SENSOR ANDA ---
# import board
# import adafruit_bme280
# import RPi.GPIO as GPIO
# ---------------------------------------------------


# --- KONFIGURASI WAJIB DIISI ---
# Informasi ini didapat dari dasbor HiveMQ Cloud Anda
HIVEMQ_HOST = "ganti_dengan_hostname_anda"
HIVEMQ_PORT = 8883  # Port standar untuk koneksi aman (TLS)
HIVEMQ_USERNAME = "ganti_dengan_username_anda"
HIVEMQ_PASSWORD = "ganti_dengan_password_anda"

# Topik MQTT bisa diatur sesuka Anda, ini akan menjadi "channel" data Anda
HIVEMQ_TOPIC = "weather/station/lampung"


# --- FUNGSI PEMBACAAN SENSOR ---
#
# GANTI ISI FUNGSI-FUNGSI DI BAWAH INI DENGAN KODE PEMBACAAN SENSOR ANDA YANG SEBENARNYA.
# Saat ini, fungsi-fungsi ini hanya menghasilkan data acak untuk keperluan pengujian.
#
def setup_sensors():
    """Fungsi untuk inisialisasi awal sensor (jika diperlukan)."""
    # Contoh: GPIO.setmode(GPIO.BCM)
    # Contoh: GPIO.setup(17, GPIO.IN)
    print("Inisialisasi sensor...")
    # Anda bisa menambahkan kode setup sensor di sini


def baca_suhu_udara():
    """Membaca sensor suhu dan kelembaban."""
    # CONTOH KODE ASLI:
    # i2c = board.I2C()
    # bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c)
    # return bme280.temperature, bme280.humidity
    
    # KODE SIMULASI:
    suhu = round(random.uniform(28.0, 35.0), 2)
    kelembaban = round(random.uniform(60.0, 90.0), 2)
    return suhu, kelembaban

def baca_kecepatan_angin():
    """Membaca sensor kecepatan angin (anemometer)."""
    # CONTOH KODE ASLI:
    # return kecepatan_angin_dari_gpio
    
    # KODE SIMULASI:
    return round(random.uniform(0.0, 15.0), 2)

def baca_arah_angin():
    """Membaca sensor arah angin (wind vane)."""
    # CONTOH KODE ASLI:
    # return arah_angin_dari_gpio
    
    # KODE SIMULASI:
    return random.choice(["Utara", "Timur Laut", "Timur", "Tenggara", "Selatan", "Barat Daya", "Barat", "Barat Laut"])

def baca_curah_hujan():
    """Membaca sensor curah hujan (rain gauge)."""
    # CONTOH KODE ASLI:
    # return jumlah_curah_hujan_dari_gpio
    
    # KODE SIMULASI:
    return round(random.uniform(0.0, 5.0), 2)


# --- FUNGSI UTAMA PROGRAM ---
def on_connect(client, userdata, flags, rc):
    """Callback yang dipanggil saat koneksi ke broker berhasil."""
    if rc == 0:
        print("✅ Berhasil terhubung ke Broker MQTT!")
    else:
        print(f"❌ Gagal terhubung, kode error: {rc}")

def run_station():
    """Fungsi utama untuk menjalankan stasiun cuaca."""
    # Inisialisasi MQTT Client
    client = mqtt.Client(client_id="raspi-weather-station-lampung")  # ID Klien bisa bebas
    client.username_pw_set(HIVEMQ_USERNAME, HIVEMQ_PASSWORD)
    client.on_connect = on_connect
    
    # Mengaktifkan enkripsi TLS untuk koneksi yang aman
    client.tls_set(tls_version=mqtt.ssl.PROTOCOL_TLS)
    
    # Coba hubungkan ke broker
    try:
        print(f"🔌 Menghubungkan ke broker di {HIVEMQ_HOST}...")
        client.connect(HIVEMQ_HOST, HIVEMQ_PORT)
    except Exception as e:
        print(f"❌ Gagal terhubung ke broker. Cek hostname dan koneksi internet. Error: {e}")
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
            hujan = baca_curah_hujan()
            
            # Buat paket data dalam format JSON (format standar untuk IoT)
            data_payload = json.dumps({
                "temperature": suhu,
                "humidity": kelembaban,
                "wind_speed_kph": kec_angin,
                "wind_direction": arah_angin,
                "rainfall_mm": hujan,
                "location": "Bandar Lampung"
            })
            
            # Kirim (publish) data ke topik MQTT
            result = client.publish(HIVEMQ_TOPIC, data_payload)
            
            # Cek status pengiriman
            status = result[0]
            if status == 0:
                print(f"🛰️  Mengirim data: {data_payload}")
            else:
                print(f"⚠️ Gagal mengirim pesan ke topik {HIVEMQ_TOPIC}")
            
            # Tunggu 30 detik sebelum pengiriman berikutnya
            time.sleep(30)
            
    except KeyboardInterrupt:
        print("\n🛑 Program dihentikan oleh pengguna.")
    finally:
        print("🔌 Memutuskan koneksi...")
        client.loop_stop()
        client.disconnect()
        print("Koneksi terputus. Selamat tinggal!")

if __name__ == '__main__':
    run_station()
