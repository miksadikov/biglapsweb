from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file
from flask_socketio import SocketIO, emit, join_room, leave_room
import os
import re
import ipaddress
import uuid
import json
import time
import logging
from flask import render_template
import threading
import base64
session_lock = threading.Lock()

app = Flask(__name__)

# Настройки приложения (раньше были в config.py)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['DEBUG'] = True

# УДАЛЕНО: terminal_sessions = {}

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

# Убираем спам access-логов от gevent (GeventWebSocketWorker)
for name in ("gevent.pywsgi", "geventwebsocket.handler"):
    logging.getLogger(name).setLevel(logging.WARNING)

socketio = SocketIO(app, cors_allowed_origins="*")

# Данные устройств
devices = {
    1: {"name": "Устройство 1", "connected": False, "address": None},
    2: {"name": "Устройство 2", "connected": False, "address": None},
    3: {"name": "Устройство 3", "connected": False, "address": None},
    4: {"name": "Устройство 4", "connected": False, "address": None},
    5: {"name": "Устройство 5", "connected": False, "address": None},
    6: {"name": "Устройство 6", "connected": False, "address": None},
    7: {"name": "Устройство 7", "connected": False, "address": None},
    8: {"name": "Устройство 8", "connected": False, "address": None},
    9: {"name": "Устройство 9", "connected": False, "address": None},
    10: {"name": "Устройство 10", "connected": False, "address": None},
    11: {"name": "Устройство 11", "connected": False, "address": None},
    12: {"name": "Устройство 12", "connected": False, "address": None},
    13: {"name": "Устройство 13", "connected": False, "address": None},
    14: {"name": "Устройство 14", "connected": False, "address": None},
    15: {"name": "Устройство 15", "connected": False, "address": None},
    16: {"name": "Устройство 16", "connected": False, "address": None},
    17: {"name": "Устройство 17", "connected": False, "address": None},
    18: {"name": "Устройство 18", "connected": False, "address": None},
    19: {"name": "Устройство 19", "connected": False, "address": None},
    20: {"name": "Устройство 20", "connected": False, "address": None},
    21: {"name": "Устройство 21", "connected": False, "address": None},
    22: {"name": "Устройство 22", "connected": False, "address": None},
    23: {"name": "Устройство 23", "connected": False, "address": None},
    24: {"name": "Устройство 24", "connected": False, "address": None},
    25: {"name": "Устройство 25", "connected": False, "address": None},
}

def empty_device_params():
    return {
        "Время съемки": "",
        "Интервал съемки": "",
        "Время подключения": "",
        "Период подключения": "",
        "Папка на сервере": "",
        "Удалить все фото с флешки": "",
        "Последние 5 фото": "",
        "Диапазон температур нагревателя": "",
        "Состояние нагревателя": "",
        "Температура и влажность в кофре": ""
    }

# Данные устройств (временное хранилище, можно заменить на БД)
device_params = {i: empty_device_params() for i in range(1, 26)}

logs = {
    1: ["Лог 1: Устройство 1 - Запись настроек", "Лог 1: Устройство 1 - Чтение настроек"],
    2: ["Лог 2: Устройство 1 - Подключение", "Лог 2: Устройство 1 - Отключение"],
}

# Разрешённые команды
ALLOWED_COMMANDS = ["cp", "mv", "rm", "mkdir", "cat", "cd", "ls", "pwd", "crontab"]

# Функция валидации параметров
def validate_param(param_name, value):
    if param_name == "Время съемки":
        if re.match(r"^\d{1,2}-\d{2}$", value):
            return None
        return "Введенные данные не соответствуют формату хх-хх, где х - это цифры от 0 до 9 (например, 01-23)"
    elif param_name == "Интервал съемки":
        try:
            num = int(value)
            if 1 <= num <= 60:
                return None
            else:
                return "Интервал съемки должен быть числом от 1 до 60."
        except ValueError:
            return "Интервал съемки должен быть числом от 1 до 60."
    elif param_name == "Время подключения":
        if re.match(r"^\d{1,2}-\d{2}$", value):
            return None
        return "Введенные данные не соответствуют формату хх-хх, где х - это цифры от 0 до 9 (например, 01-23)"
    elif param_name == "Период подключения":
        try:
            num = int(value)
            if 1 <= num <= 60:
                return None
            else:
                return "Период подключения должен быть числом от 1 до 60."
        except ValueError:
            return "Период подключения должен быть числом от 1 до 60."
    elif param_name == "Папка на сервере":
        if not re.match(r"^/[a-zA-Z0-9_/]{1,28}/$", value):
            return ("Введенные данные не соответствуют формату: путь должен начинаться и заканчиваться на '/', содержать только латинские буквы, цифры, '_', '/' и иметь длину не более 30 символов.")
    elif param_name == "Диапазон температур нагревателя":
        if not re.match(r"^\d{2}-\d{2}$", value):
            return "Введенные данные не соответствуют формату хх-хх, где х - это цифры от 0 до 9."
    return None

# WebSocket-события
@socketio.on('connect', namespace='/')
def handle_connect():
    logging.info(f"Клиент подключился: {request.sid}")

@socketio.on('connect_error', namespace='/')
def handle_connect_error(error):
    logging.error(f"Ошибка подключения клиента: {error}")

@socketio.on('register', namespace='/')
def handle_register(data):
    client_id = int(data['client_id'])
    devices[client_id]["connected"] = True
    device_params[client_id] = empty_device_params()
    # Логируем только client_id
    logging.info(f"Клиент зарегистрирован: client_id={client_id}")

@socketio.on('disconnect', namespace='/')
def handle_disconnect():
    for device_id, device in list(devices.items()):
        if device.get("connected"):
            device["connected"] = False
            logging.info(f"Устройство {device_id} отключено")
            break

@socketio.on('response', namespace='/')
def handle_response(data):
    client_id = data.get('client_id')
    response = (data.get('response') or "").strip()
    command = data.get('command')

    logging.info(f"Получен ответ от устройства {client_id}: {response} для команды {command}")

    # ЧТЕНИЕ ПАРАМЕТРОВ
    if command == 'read_param':
        param_name = data.get('param_name')
        if not param_name:
            logging.warning("read_param без param_name")
            return

        value = response

        try:
            if param_name == "Время съемки" and response.startswith("timetable="):
                # timetable=1-23 -> 1-23
                value = response.split("=", 1)[1]
            elif param_name == "Интервал съемки" and response.startswith("period="):
                # period=*/10 -> 10
                value = response.split("/", 1)[1]
            elif param_name == "Время подключения" and response.startswith("timetable2="):
                # timetable=1-23 -> 1-23
                value = response.split("=", 1)[1]
            elif param_name == "Период подключения" and response.startswith("period2="):
                # period=*/10 -> 10
                value = response.split("/", 1)[1]
            elif param_name == "Телефон админа 1" and response.startswith("admin="):
                # admin=7XXXXXXXXXX -> 7XXXXXXXXXX
                value = response.split("=", 1)[1]
            elif param_name == "Папка на сервере" and response.startswith("dir="):
                # dir=folder1 -> folder1
                value = response.split("=", 1)[1]
            elif param_name == "Диапазон температур нагревателя" and "=" in response:
                # heater_range=20-30 -> 20-30 (если вдруг так придёт)
                value = response.split("=", 1)[1]
            elif param_name == "Температура и влажность в кофре" and response.startswith("ht="):
                # ht=20°C, 50% -> 20°C, 50%
                value = response.split("=", 1)[1]
        except Exception as e:
            logging.error(f"Ошибка парсинга ответа '{response}' для параметра '{param_name}': {e}")
            value = response

        device_params[client_id][param_name] = value
        logging.info(f"Обновлен параметр {param_name} для устройства {client_id}: {value}")

    # ТЕСТОВОЕ ФОТО (если используешь)
    elif command == 'test_photo' and response.startswith('PHOTO_OK'):
        photo_path = response.split(':', 1)[1] if ':' in response else "test_photo.jpg"
        device_params[client_id]["Тестовое фото"] = photo_path
        logging.info(f"Тестовое фото для устройства {client_id}: {photo_path}")


@socketio.on('exec_command', namespace='/')
def handle_exec_command(data):
    client_id = data.get('client_id')
    command = data.get('command')
    args = data.get('args', [])
    if not client_id or not command:
        emit('command_result', {'error': 'Не указан client_id или команда'})
        return
    if command not in ALLOWED_COMMANDS:
        emit('command_result', {'error': f'Команда {command} не разрешена'})
        return
    if client_id in devices and devices[client_id]["connected"]:
        # Broadcast всем клиентам, клиент сам проверит свой client_id
        socketio.emit('exec_command', {'command': command, 'args': args, 'client_id': client_id})
    else:
        emit('command_result', {'error': 'Устройство не подключено'})

@socketio.on('command_result', namespace='/')
def handle_command_result(data):
    result = data.get('result')
    error = data.get('error')
    client_id = data.get('client_id')
    emit('command_result', {'result': result, 'error': error, 'client_id': client_id})

def send_command(client_id, command, data=None):
    if client_id in devices and devices[client_id]["connected"]:
        # Broadcast всем клиентам, клиент сам проверит свой client_id
        socketio.emit('command', {'command': command, 'data': data, 'client_id': client_id})
        logging.info(f"Отправлена команда устройству {client_id}: {command}")

# Функции для работы с устройствами
def read_device_params(device_id, param_name):
    send_command(device_id, 'read_param', {'param_name': param_name})

def write_device_params(device_id, params):
    param_name, value = next(iter(params.items()))
    send_command(device_id, 'write_param', {'param_name': param_name, 'value': value})

def delete_all_photos(device_id):
    """
    Отправляет на устройство команду удаления всех фото.
    По аналогии с write_device_params, но значение всегда 'all'
    и не берётся из формы.
    """
    send_command(
        device_id,
        'write_param',
        {
            'param_name': 'Удалить все фото с флешки',
            'value': 'all'
        }
    )


def control_heater(device_id, action):
    send_command(device_id, 'heater', {'action': action})

def create_test_photo(device_id):
    send_command(device_id, 'test_photo')
    return "test_photo.jpg"

# Маршруты Flask
@app.route('/')
def index():
    return render_template('index.html', devices=devices)

@app.route('/get_devices')
def get_devices():
    return jsonify(devices)

@app.route('/disconnect/<int:device_id>')
def disconnect(device_id):
    if device_id in devices and devices[device_id]["connected"]:
        send_command(device_id, 'disconnect')
        devices[device_id]["connected"] = False
        devices[device_id]["sid"] = None
        logging.info(f"Устройство {device_id} отключено")
    return redirect(url_for('index'))

@app.route('/device/<int:device_id>', methods=['GET', 'POST'])
def device_page(device_id):
    if device_id not in devices or not devices[device_id]["connected"]:
        logging.info(f"Устройство {device_id} не подключено, перенаправляем на главную")
        return redirect(url_for('index'))

    params = device_params[device_id]
    error_message = None

    if request.method == 'POST':
        logging.info(f"Получен POST-запрос: {request.form}")

        # Работа с параметрами (чтение/запись)
        if 'action' in request.form:
            param_name = request.form.get('param_name')
            action = request.form.get('action')
            logging.info(f"Действие: {action}, Параметр: {param_name}")

            if action == 'read':
                # старое значение, чтобы понять, что оно изменилось
                old_value = params.get(param_name)

                # отправляем команду устройству
                read_device_params(device_id, param_name)

                # ждём, пока клиент ответит и handle_response обновит device_params
                timeout = 2.0
                step = 0.1
                start = time.time()

                while time.time() - start < timeout:
                    new_value = device_params[device_id].get(param_name)
                    if new_value != old_value and new_value is not None:
                        break
                    time.sleep(step)

                # после ожидания – стандартный redirect
                return redirect(url_for('device_page', device_id=device_id))

            elif action == 'write':
                new_value = request.form.get('value')
                logging.info(f"Попытка записи: {param_name} = {new_value}")
                error_message = validate_param(param_name, new_value)
                if error_message is None:
                    # Сохраняем локально и отправляем на устройство
                    params[param_name] = new_value
                    write_device_params(device_id, {param_name: new_value})
                    return redirect(url_for('device_page', device_id=device_id))

            elif action == 'delete_photos':
                # здесь логика удаления всех фото на устройстве
                logging.info(f"Запрос на удаление всех фото с флешки для устройства {device_id}")
                delete_all_photos(device_id)
                params["Удалить все фото с флешки"] = "Команда отправлена"
                return redirect(url_for('device_page', device_id=device_id))

        # Управление нагревателем
        elif 'heater_action' in request.form:
            heater_action = request.form.get('heater_action')
            state = "Включен" if heater_action == "turn_on" else "Выключен"
            control_heater(device_id, heater_action)
            params["Состояние нагревателя"] = state
            return redirect(url_for('device_page', device_id=device_id))

        # Тестовое фото
        elif 'test_photo' in request.form:
            photo_path = create_test_photo(device_id)
            if os.path.exists(photo_path):
                return send_file(photo_path, as_attachment=True)
            else:
                error_message = "Тестовое фото не найдено"

    return render_template(
        'device.html',
        device_id=device_id,
        device_name=devices[device_id]["name"],
        params=params,
        error_message=error_message
    )


@app.route('/log/<int:log_id>')
def log_page(log_id):
    log_content = logs.get(log_id, ["Лог не найден"])
    return render_template('log.html', log_id=log_id, log_content=log_content)

@app.route('/upload_file', methods=['POST'])
def upload_file():
    client_id = int(request.form.get('client_id'))
    dest_path = request.form.get('dest_path')
    file = request.files.get('file')
    if not file or not dest_path or client_id not in devices or not devices[client_id]["connected"]:
        return jsonify({'status': 'error', 'message': 'Некорректные данные или устройство не подключено'}), 400
    file_data = base64.b64encode(file.read()).decode('utf-8')
    # Broadcast всем клиентам, клиент сам проверит свой client_id
    socketio.emit('upload_file', {'file_data': file_data, 'filename': file.filename, 'dest_path': dest_path, 'client_id': client_id})
    return jsonify({'status': 'ok'})

# WebSocket-обработка результата загрузки файла
@socketio.on('upload_file_result', namespace='/')
def handle_upload_file_result(data):
    # Можно доработать: отправлять статус пользователю по sid
    print('Результат загрузки файла:', data)

@app.route('/terminal/<int:device_id>')
def terminal_page(device_id):
    if device_id not in devices or not devices[device_id]["connected"]:
        return "Device not connected", 404
    return render_template('terminal.html', device_id=device_id)

# УДАЛЕНО: @socketio.on('terminal_connect', namespace='/terminal')
# УДАЛЕНО: @socketio.on('shell_input', namespace='/terminal')
# УДАЛЕНО: @socketio.on('shell_output', namespace='/')
# УДАЛЕНО: @socketio.on('stop_shell', namespace='/terminal')
# УДАЛЕНО: @socketio.on('disconnect', namespace='/terminal')

@app.route('/favicon.ico')
def favicon():
    return '', 204

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
