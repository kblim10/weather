import paho.mqtt.client as mqtt
import time
import json
import board
import adafruit_bme280

# --- KONFIGURASI UNTUK SERVER LOKAL ---
MQTT_HOST = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "weather/station/local"

# --- Inisialisasi Sensor ---
try:
    # Inisialisasi sensor I2C untuk Suhu, Kelembaban, Tekanan
    i2c = board.I2C()  # Menggunakan pin SCL dan SDA default
    bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c)
    print("✅ Sensor BME280 (Suhu/Kelembaban) berhasil diinisialisasi.")
except Exception as e:
    print(f"❌ GAGAL menginisialisasi sensor BME280. Pastikan I2C aktif. Error: {e}")
    bme280 = None

# --- Inisialisasi Pin GPIO untuk sensor lain (jika diperlukan) ---
# Anda perlu mencari tahu pin GPIO mana yang digunakan oleh sensor angin dan hujan
# Contoh: WIND_SPEED_PIN = 17
# Contoh: RAIN_GAUGE_PIN = 18


# --- FUNGSI PEMBACAAN SENSOR ---

def baca_suhu_udara():
    """Membaca sensor suhu dan kelembaban BME280."""
    if bme280:
        try:
            suhu = round(bme280.temperature, 2)
            kelembaban = round(bme280.humidity, 2)
            return suhu, kelembaban
        except Exception as e:
            print(f"⚠️ Gagal membaca data dari BME280: {e}")
            return "N/A", "N/A"
    else:
        # Jika sensor gagal diinisialisasi, kembalikan data default
        return "N/A", "N/A"

def baca_kecepatan_angin():
    """
    KERANGKA UNTUK MEMBACA SENSOR KECEPATAN ANGIN.
    Anda perlu mengimplementasikan logika untuk menghitung pulsa dari pin GPIO.
    """
    # KODE ASLI PERLU DIIMPLEMENTASIKAN DI SINI
    return 0.0 # Mengembalikan nilai default untuk sekarang

def baca_arah_angin():
    """
    KERANGKA UNTUK MEMBACA SENSOR ARAH ANGIN.
    Biasanya ini melibatkan pembacaan nilai voltase/resistansi.
    """
    # KODE ASLI PERLU DIIMPLEMENTASIKAN DI SINI
    return "N/A" # Mengembalikan nilai default untuk sekarang

def baca_curah_hujan():
    """
    KERANGKA UNTUK MEMBACA SENSOR CURAH HUJAN.
    Anda perlu mengimplementasikan logika untuk menghitung "tip" dari rain gauge.
    """
    # KODE ASLI PERLU DIIMPLEMENTASIKAN DI SINI
    return 0.0 # Mengembalikan nilai default untuk sekarang

# --- FUNGSI UTAMA PROGRAM ---
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Sensor terhubung ke Broker MQTT Lokal!")
    else:
        print(f"❌ Gagal terhubung ke broker lokal, kode error: {rc}")

def run_station():
    client = mqtt.Client(client_id="sensor-publisher")
    client.on_connect = on_connect
    
    try:
        print(f"🔌 Menghubungkan ke broker di {MQTT_HOST}...")
        client.connect(MQTT_HOST, MQTT_PORT)
    except Exception as e:
        print(f"❌ Gagal terhubung ke broker lokal. Pastikan Mosquitto berjalan. Error: {e}")
        return

    client.loop_start()
    
    try:
        while True:
            suhu, kelembaban = baca_suhu_udara()
            kec_angin = baca_kecepatan_angin()
            arah_angin = baca_arah_angin()
            hujan = baca_curah_hujan()
            
            data_payload = json.dumps({
                "temperature": suhu,
                "humidity": kelembaban,
                "wind_speed_kph": kec_angin,
                "wind_direction": arah_angin,
                "rainfall_mm": hujan,
                "location": "Bandar Lampung"
            })
            
            result = client.publish(MQTT_TOPIC, data_payload)
            
            if result[0] == 0:
                print(f"🛰️  Mengirim data: {data_payload}")
            else:
                print(f"⚠️ Gagal mengirim pesan ke topik {MQTT_TOPIC}")
            
            time.sleep(10)
            
    except KeyboardInterrupt:
        print("\n🛑 Program sensor dihentikan.")
    finally:
        client.loop_stop()
        client.disconnect()

if __name__ == '__main__':
    run_station()
