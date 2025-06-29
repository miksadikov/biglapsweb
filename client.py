import socketio
import subprocess
import os
from datetime import datetime

# Настройки клиента
SERVER_URL = "wss://your-project-name.amvera.app"  # Замените на домен, предоставленный Amvera
EVENTHANDLER_PATH = "/home/orangepi/nettools/eventhandler-net.sh"
CLIENT_ID_PATH = "/home/orangepi/nettools/client_id.txt"
LOG_FILE = "/tmp/client.log"

def put_to_log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"{timestamp} {message}\n")

try:
    with open(CLIENT_ID_PATH, 'r') as file:
        client_id = file.read().strip()
except FileNotFoundError:
    put_to_log(f"Error: File {CLIENT_ID_PATH} Not Found.")
    exit(0)
except Exception as e:
    put_to_log(f"Error: {e}")
    exit(0)

# Создаем WebSocket-клиент
sio = socketio.Client()

@sio.event
def connect():
    put_to_log(f"Клиент {client_id} подключился к серверу")
    sio.emit('register', {'client_id': client_id})

@sio.event
def disconnect():
    put_to_log(f"Клиент {client_id} отключился от сервера")

@sio.event
def command(data):
    command = data['command']
    command_data = data.get('data', {})
    put_to_log(f"Клиент {client_id} получил команду: {command}")

    if command == 'disconnect':
        sio.emit('response', {'client_id': client_id, 'response': 'Disconnect Ok', 'command': command})
        put_to_log(f"Клиент {client_id} отправил Disconnect Ok и завершает работу")
        sio.disconnect()

    elif command == 'read_param':
        param_name = command_data['param_name']
        cmd = f"Cmd=getparam={param_name.lower().replace(' ', '_')}"
        response = subprocess.run([EVENTHANDLER_PATH, cmd], capture_output=True, text=True).stdout.strip()
        sio.emit('response', {'client_id': client_id, 'response': response, 'command': command, 'param_name': param_name})

    elif command == 'write_param':
        param_name = command_data['param_name']
        value = command_data['value']
        cmd = f"Cmd=setparam={value}"
        response = subprocess.run([EVENTHANDLER_PATH, cmd], capture_output=True, text=True).stdout.strip()
        sio.emit('response', {'client_id': client_id, 'response': response, 'command': command})

    elif command == 'heater':
        action = command_data['action']
        cmd = "Cmd=setparam=heater_on" if action == "turn_on" else "Cmd=setparam=heater_off"
        response = subprocess.run([EVENTHANDLER_PATH, cmd], capture_output=True, text=True).stdout.strip()
        sio.emit('response', {'client_id': client_id, 'response': response, 'command': command})

    elif command == 'test_photo':
        cmd = "Cmd=testshot"
        response = subprocess.run([EVENTHANDLER_PATH, cmd], capture_output=True, text=True).stdout.strip()
        if response == "OK":
            photo_path = "test_photo.jpg"
            sio.emit('response', {'client_id': client_id, 'response': f"PHOTO_OK:{photo_path}", 'command': command})
        else:
            sio.emit('response', {'client_id': client_id, 'response': response, 'command': command})

try:
    sio.connect(SERVER_URL)
    sio.wait()
except Exception as e:
    put_to_log(f"Клиент {client_id} ошибка: {str(e)}")
