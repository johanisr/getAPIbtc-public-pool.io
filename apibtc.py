import requests
import time
from datetime import datetime
import smbus

# I2C address of the LCD
I2C_ADDR = 0x3f  # Sesuaikan dengan alamat I2C LCD Anda

# Define some constants
LCD_CHR = 1  # Sending data
LCD_CMD = 0  # Sending command
LCD_LINE_1 = 0x80  # First line
LCD_LINE_2 = 0xC0  # Second line
LCD_BACKLIGHT = 0x08  # Backlight on
ENABLE = 0b00000100  # Enable bit

# Initialize I2C (SMBus)
bus = smbus.SMBus(1)

def lcd_byte(bits, mode, backlight):
    high_bits = mode | (bits & 0xF0) | backlight
    low_bits = mode | ((bits << 4) & 0xF0) | backlight

    bus.write_byte(I2C_ADDR, high_bits)
    lcd_toggle_enable(high_bits)

    bus.write_byte(I2C_ADDR, low_bits)
    lcd_toggle_enable(low_bits)

def lcd_toggle_enable(bits):
    time.sleep(0.0005)
    bus.write_byte(I2C_ADDR, (bits | ENABLE))
    time.sleep(0.0005)
    bus.write_byte(I2C_ADDR, (bits & ~ENABLE))
    time.sleep(0.0005)

def lcd_init():
    lcd_byte(0x33, LCD_CMD, LCD_BACKLIGHT)  # 110011 Initialize
    lcd_byte(0x32, LCD_CMD, LCD_BACKLIGHT)  # 110010 Initialize
    lcd_byte(0x06, LCD_CMD, LCD_BACKLIGHT)  # Cursor move direction
    lcd_byte(0x0C, LCD_CMD, LCD_BACKLIGHT)  # Turn on display
    lcd_byte(0x28, LCD_CMD, LCD_BACKLIGHT)  # 2 line display
    lcd_byte(0x01, LCD_CMD, LCD_BACKLIGHT)  # Clear display
    time.sleep(0.0005)

def lcd_message(message, line, backlight=LCD_BACKLIGHT):
    lcd_byte(line, LCD_CMD, backlight)
    message = message.ljust(16)[:16]  # Ensure the message fits the display
    for char in message:
        lcd_byte(ord(char), LCD_CHR, backlight)

# Function to fetch data from the API
def fetch_api_data():
    try:
        response = requests.get("https://public-pool.io:40557/api/client/1EcbTSpsvBuosnJ4WfsonTuJrJGT3QFz5C")
        if response.status_code == 200:
            return response.json()
        else:
            print(f"API Error: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error fetching API data: {e}")
        return None

# Function to display the date on the first line
def display_date(backlight):
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M")
    lcd_message(current_date, LCD_LINE_1, backlight)

# Function to display the total bestDifficulty and workersCount
def display_total_data(api_data, backlight):
    if api_data and "workers" in api_data:
        workers = api_data["workers"]
        bestDifficulty = api_data["bestDifficulty"]
                
        # Tampilkan jumlah pekerja
        workers_count = len(workers)

        # Tampilkan total bestDifficulty di baris kedua
        lcd_message(f"bestDiff:{bestDifficulty}", LCD_LINE_2, backlight)
        time.sleep(4)  # Tampilkan selama 4 detik

        # Tampilkan jumlah pekerja
        lcd_message(f"Workers:{workers_count}", LCD_LINE_2, backlight)
        time.sleep(4)  # Tampilkan selama 4 detik
    else:
        lcd_message("No Data Workers", LCD_LINE_2, backlight)

def display_worker_data(api_data, backlight, worker_index):
    if api_data and "workers" in api_data and len(api_data["workers"]) > 0:
        workers = api_data["workers"]
        workers_count = len(workers)
        
        # Pastikan worker_index berada dalam rentang jumlah pekerja
        worker_index = worker_index % workers_count
        worker = workers[worker_index]
        
        # Tampilkan nomor pekerja dan sessionId
        lcd_message(f"Worker{worker_index + 1}:{worker['sessionId'][:8]}", LCD_LINE_2, backlight)
        time.sleep(4)  # Tampilkan selama 4 detik
        
        # Tampilkan hash rate pekerja
        lcd_message(f"HR_W{worker_index + 1}:{float(worker['hashRate']):.1f}H/s", LCD_LINE_2, backlight)
        time.sleep(4)  # Tampilkan selama 4 detik
        
        # Tampilkan best difficulty pekerja
        lcd_message(f"Best_W{worker_index + 1}:{worker['bestDifficulty']}", LCD_LINE_2, backlight)
        time.sleep(4)  # Tampilkan selama 4 detik
    else:
        lcd_message("No Data Workers", LCD_LINE_2, backlight)

lcd_init()

worker_index = 0
while True:
    # Tampilkan tanggal pada baris pertama
    display_date(LCD_BACKLIGHT)

    # Ambil data API
    api_data = fetch_api_data()

    # Tampilkan total data (bestDifficulty dan workersCount)
    display_total_data(api_data, LCD_BACKLIGHT)

    # Tampilkan data pekerja pada baris kedua
    display_worker_data(api_data, LCD_BACKLIGHT, worker_index)

    # Beralih ke pekerja berikutnya
    worker_index += 1

    # Tunggu sebelum mengulangi (4 detik per data pekerja sudah ditangani di fungsi)
    time.sleep(1)

