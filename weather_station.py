import paho.mqtt.client as mqtt
import time
import json
import random
import board

# Import library BME280 dengan cara yang benar untuk versi baru
import adafruit_bme280.basic as adafruit_bme280

# --- KONFIGURASI UNTUK SERVER LOKAL ---
MQTT_HOST = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "weather/station/local"

# Variabel global untuk menyimpan objek sensor
# Ini memungkinkan kita mengaksesnya dari berbagai fungsi
bme280 = None


# --- FUNGSI-FUNGSI PROGRAM ---

def setup_sensors():
    """
    Fungsi untuk inisialisasi awal semua sensor.
    Ini dijalankan sekali saat program dimulai.
    """
    global bme280
    try:
        print("Mencoba inisialisasi sensor BME280 (Suhu & Kelembaban)...")
        # Inisialisasi bus I2C di Raspberry Pi
        i2c = board.I2C()
        # Buat objek sensor BME280 menggunakan nama class yang benar
        bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c)
        print("✅ Sensor BME280 berhasil diinisialisasi.")
    except Exception as e:
        # Jika sensor tidak terdeteksi atau ada error lain
        print(f"❌ GAGAL inisialisasi sensor BME280. Data suhu/kelembaban tidak akan tersedia. Error: {e}")
        bme280 = None
    
    # Anda bisa menambahkan inisialisasi untuk sensor angin dan hujan di sini

def baca_suhu_udara():
    """Membaca data dari sensor suhu dan kelembaban BME280."""
    if bme280 is not None:
        # Jika objek sensor berhasil dibuat saat setup
        try:
            suhu = round(bme280.temperature, 2)
            # Nama atribut yang benar di library baru adalah 'relative_humidity'
            kelembaban = round(bme280.relative_humidity, 2)
            return suhu, kelembaban
        except Exception as e:
            print(f"⚠️ Gagal membaca data dari BME280: {e}")
            return "Error", "Error"
    else:
        # Jika sensor tidak terinisialisasi
        return "N/A", "N/A"

# --- FUNGSI SIMULASI UNTUK SENSOR LAIN ---
#
# PENTING: GANTI ISI FUNGSI-FUNGSI DI BAWAH INI DENGAN KODE ASLI
# UNTUK MEMBACA SENSOR ANGIN DAN HUJAN ANDA.
#
def baca_kecepatan_angin():
    """Membaca sensor kecepatan angin (anemometer)."""
    # KODE SIMULASI:
    return round(random.uniform(0.0, 15.0), 2)

def baca_arah_angin():
    """Membaca sensor arah angin (wind vane)."""
    # KODE SIMULASI:
    return random.choice(["Utara", "Timur", "Selatan", "Barat"])


# --- FUNGSI UTAMA & MQTT ---
def on_connect(client, userdata, flags, rc):
    """Callback yang dipanggil saat koneksi ke broker berhasil."""
    if rc == 0:
        print("🛰️  Skrip sensor terhubung ke Broker MQTT Lokal!")
    else:
        print(f"❌ Gagal terhubung ke broker lokal, kode error: {rc}")

def run_station():
    """Fungsi utama untuk menjalankan stasiun cuaca."""
    client = mqtt.Client(client_id="sensor-publisher")
    client.on_connect = on_connect
    
    try:
        client.connect(MQTT_HOST, MQTT_PORT)
    except Exception as e:
        print(f"❌ Gagal terhubung ke broker lokal. Pastikan Mosquitto berjalan. Error: {e}")
        return

    client.loop_start()
    
    # Jalankan setup sensor sekali di awal
    setup_sensors()
    
    try:
        while True:
            # Baca semua data dari setiap sensor
            suhu, kelembaban = baca_suhu_udara()
            kec_angin = baca_kecepatan_angin()
            arah_angin = baca_arah_angin()
            
            # Buat paket data dalam format JSON
            data_payload = json.dumps({
                "temperature": suhu,
                "humidity": kelembaban,
                "wind_speed_kph": kec_angin,
                "wind_direction": arah_angin
            })
            
            # Kirim (publish) data ke topik MQTT
            result = client.publish(MQTT_TOPIC, data_payload)
            
            if result[0] == 0:
                print(f"📤 Mengirim data: {data_payload}")
            else:
                print(f"⚠️ Gagal mengirim pesan ke topik {MQTT_TOPIC}")
            
            # Tunggu 10 detik sebelum pengiriman berikutnya
            time.sleep(10)
            
    except KeyboardInterrupt:
        print("\n🛑 Program sensor dihentikan.")
    finally:
        print("🔌 Memutuskan koneksi sensor...")
        client.loop_stop()
        client.disconnect()

if __name__ == '__main__':
    run_station()
