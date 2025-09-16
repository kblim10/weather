import time
import board
import adafruit_dht
import paho.mqtt.client as mqtt
import json

# --- PENGATURAN - GANTI SESUAI KEBUTUHAN ANDA ---
MQTT_BROKER     = "ALAMAT_IP_SERVER_ANDA"
MQTT_PORT       = 1883
MQTT_TOPIC      = "iot/weather/data"
MQTT_USERNAME   = "user_iot" # Username MQTT yang Anda buat
MQTT_PASSWORD   = "PASSWORD_MQTT_ANDA" # Password untuk user di atas
SENSOR_PIN      = board.D4   # Pin GPIO tempat data sensor terhubung (GPIO 4)
INTERVAL_DETIK  = 10         # Jeda waktu pengiriman data (dalam detik)
# --- AKHIR PENGATURAN ---

# Inisialisasi sensor DHT11
dht_device = adafruit_dht.DHT11(SENSOR_PIN)

# Fungsi yang akan dipanggil saat berhasil terhubung ke MQTT Broker
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Berhasil terhubung ke MQTT Broker!")
    else:
        print(f"Gagal terhubung, kode status: {rc}")

# Inisialisasi MQTT Client
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, "raspberrypi-dht11")
client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
client.on_connect = on_connect

# Coba terhubung ke broker
try:
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
except Exception as e:
    print(f"Gagal terhubung ke broker. Cek alamat IP dan koneksi. Error: {e}")
    exit()

client.loop_start() # Memulai loop untuk menangani koneksi di background

while True:
    try:
        # Baca data dari sensor
        suhu = dht_device.temperature
        lembap = dht_device.humidity

        # DHT11 kadang gagal membaca, cek apakah datanya valid
        if suhu is not None and lembap is not None:
            print(f"Membaca data: Suhu={suhu:.1f}°C, Kelembapan={lembap:.1f}%")

            # Siapkan data dalam format JSON
            payload = json.dumps({
                "suhu": suhu,
                "lembap": lembap
            })

            # Kirim data ke MQTT Broker
            result = client.publish(MQTT_TOPIC, payload)

            if result[0] == 0:
                print(f"Data terkirim ke topik '{MQTT_TOPIC}'")
            else:
                print("Gagal mengirim data.")

        else:
            print("Gagal membaca data dari sensor, coba lagi...")

    except RuntimeError as error:
        # Error ini biasa terjadi pada DHT sensor, abaikan dan coba lagi
        print(error.args[0])
    except Exception as e:
        dht_device.exit()
        client.loop_stop()
        raise e

    # Tunggu sesuai interval sebelum membaca lagi
    time.sleep(INTERVAL_DETIK)
