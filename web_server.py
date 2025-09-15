from flask import Flask, render_template
import paho.mqtt.client as mqtt
import json
import threading

app = Flask(__name__)

latest_weather_data = {
    "temperature": "N/A", "humidity": "N/A",
    "wind_speed_kph": "N/A", "wind_direction": "N/A",
    "rainfall_mm": "N/A"
}

MQTT_HOST = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "weather/station/local"

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Web Server terhubung ke Broker MQTT Lokal!")
        client.subscribe(MQTT_TOPIC)
    else:
        print(f"❌ Gagal terhubung ke broker lokal, kode: {rc}")

def on_message(client, userdata, msg):
    global latest_weather_data
    print(f"Menerima data di topik {msg.topic}: {msg.payload.decode()}")
    try:
        latest_weather_data = json.loads(msg.payload.decode())
    except json.JSONDecodeError:
        print("⚠️ Gagal mem-parsing data JSON")

def run_mqtt_client():
    client = mqtt.Client(client_id="weather-web-server")
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_HOST, MQTT_PORT, 60)
    client.loop_forever()

@app.route('/')
def index():
    return render_template('index.html', data=latest_weather_data)

if __name__ == '__main__':
    mqtt_thread = threading.Thread(target=run_mqtt_client)
    mqtt_thread.daemon = True
    mqtt_thread.start()
    app.run(host='0.0.0.0', port=5000, debug=False)
