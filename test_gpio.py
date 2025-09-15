import lgpio
import time
import sys

# --- KONFIGURASI PIN GPIO UNTUK ORACLE WEATHER STATION HAT ---
# Pin ini adalah standar untuk HAT yang Anda miliki
WIND_SPEED_PIN = 5  # Sensor Kecepatan Angin
RAIN_PIN = 6        # Sensor Hujan

# Variabel untuk menghitung pulsa
wind_clicks = 0
rain_clicks = 0

# --- FUNGSI CALLBACK ---
# Fungsi ini akan dipanggil secara otomatis setiap kali ada sinyal
def wind_callback(chip, gpio, level, tick):
    """Callback untuk sensor angin."""
    global wind_clicks
    wind_clicks += 1
    print(f"💨 Putaran angin terdeteksi! (Total: {wind_clicks})")

def rain_callback(chip, gpio, level, tick):
    """Callback untuk sensor hujan."""
    global rain_clicks
    rain_clicks += 1
    print(f"💧 Tetesan hujan terdeteksi! (Total: {rain_clicks})")


# --- PROGRAM UTAMA ---
try:
    # Buka koneksi ke chip GPIO
    h = lgpio.gpiochip_open(0)

    # Atur callback untuk setiap pin
    # Kita "mendengarkan" sinyal FALLING_EDGE (saat 'klik' terjadi)
    cb_wind = lgpio.callback(h, WIND_SPEED_PIN, lgpio.FALLING_EDGE, wind_callback)
    cb_rain = lgpio.callback(h, RAIN_PIN, lgpio.FALLING_EDGE, rain_callback)

    print("✅ Skrip pengujian berjalan. Menunggu sinyal dari sensor...")
    print("Putar sensor angin atau teteskan air ke sensor hujan.")
    print("Tekan Ctrl+C untuk berhenti.")

    # Biarkan program berjalan untuk mendengarkan
    while True:
        time.sleep(1)

except Exception as e:
    print(f"❌ Terjadi error: {e}")
    print("Pastikan Anda sudah menginstal 'python3-lgpio' dengan 'sudo apt install'.")

finally:
    print("\n🛑 Program berhenti. Membersihkan...")
    # Hentikan callback dan tutup koneksi
    if 'cb_wind' in locals() and cb_wind.is_set():
        cb_wind.cancel()
    if 'cb_rain' in locals() and cb_rain.is_set():
        cb_rain.cancel()
    if 'h' in locals():
        lgpio.gpiochip_close(h)
    print("Selesai.")
