from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file
from flask_socketio import SocketIO, emit
import os
import re
import ipaddress

app = Flask(__name__)

# Настройки приложения (раньше были в config.py)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['DEBUG'] = True

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
}

# Данные устройств (временное хранилище, можно заменить на БД)
device_params = {
    1: {
        "Время съемки": "",
        "Интервал съемки": "",
        "Папка на сервере": "",
        "IP адрес сервера": "",
        "Телефон админа 1": "",
        "Телефон админа 2": "",
        "Диапазон температур нагревателя": "",
        "Состояние нагревателя": "",
        "Температура и влажность в кофре": ""
    },
    2: {
        "Время съемки": "",
        "Интервал съемки": "",
        "Папка на сервере": "",
        "IP адрес сервера": "",
        "Телефон админа 1": "",
        "Телефон админа 2": "",
        "Диапазон температур нагревателя": "",
        "Состояние нагревателя": "",
        "Температура и влажность в кофре": ""
    },
    3: {
        "Время съемки": "",
        "Интервал съемки": "",
        "Папка на сервере": "",
        "IP адрес сервера": "",
        "Телефон админа 1": "",
        "Телефон админа 2": "",
        "Диапазон температур нагревателя": "",
        "Состояние нагревателя": "",
        "Температура и влажность в кофре": ""
    },
    4: {
        "Время съемки": "",
        "Интервал съемки": "",
        "Папка на сервере": "",
        "IP адрес сервера": "",
        "Телефон админа 1": "",
        "Телефон админа 2": "",
        "Диапазон температур нагревателя": "",
        "Состояние нагревателя": "",
        "Температура и влажность в кофре": ""
    },
    5: {
        "Время съемки": "",
        "Интервал съемки": "",
        "Папка на сервере": "",
        "IP адрес сервера": "",
        "Телефон админа 1": "",
        "Телефон админа 2": "",
        "Диапазон температур нагревателя": "",
        "Состояние нагревателя": "",
        "Температура и влажность в кофре": ""
    },
    6: {
        "Время съемки": "",
        "Интервал съемки": "",
        "Папка на сервере": "",
        "IP адрес сервера": "",
        "Телефон админа 1": "",
        "Телефон админа 2": "",
        "Диапазон температур нагревателя": "",
        "Состояние нагревателя": "",
        "Температура и влажность в кофре": ""
    },
    7: {
        "Время съемки": "",
        "Интервал съемки": "",
        "Папка на сервере": "",
        "IP адрес сервера": "",
        "Телефон админа 1": "",
        "Телефон админа 2": "",
        "Диапазон температур нагревателя": "",
        "Состояние нагревателя": "",
        "Температура и влажность в кофре": ""
    },
    8: {
        "Время съемки": "",
        "Интервал съемки": "",
        "Папка на сервере": "",
        "IP адрес сервера": "",
        "Телефон админа 1": "",
        "Телефон админа 2": "",
        "Диапазон температур нагревателя": "",
        "Состояние нагревателя": "",
        "Температура и влажность в кофре": ""
    },
    9: {
        "Время съемки": "",
        "Интервал съемки": "",
        "Папка на сервере": "",
        "IP адрес сервера": "",
        "Телефон админа 1": "",
        "Телефон админа 2": "",
        "Диапазон температур нагревателя": "",
        "Состояние нагревателя": "",
        "Температура и влажность в кофре": ""
    },
    10: {
        "Время съемки": "",
        "Интервал съемки": "",
        "Папка на сервере": "",
        "IP адрес сервера": "",
        "Телефон админа 1": "",
        "Телефон админа 2": "",
        "Диапазон температур нагревателя": "",
        "Состояние нагревателя": "",
        "Температура и влажность в кофре": ""
    },
    11: {
        "Время съемки": "",
        "Интервал съемки": "",
        "Папка на сервере": "",
        "IP адрес сервера": "",
        "Телефон админа 1": "",
        "Телефон админа 2": "",
        "Диапазон температур нагревателя": "",
        "Состояние нагревателя": "",
        "Температура и влажность в кофре": ""
    }
}

logs = {
    1: ["Лог 1: Устройство 1 - Запись настроек", "Лог 1: Устройство 1 - Чтение настроек"],
    2: ["Лог 2: Устройство 1 - Подключение", "Лог 2: Устройство 1 - Отключение"],
}

# Функция валидации параметров
def validate_param(param_name, value):
    if param_name == "Время съемки":
        if not re.match(r"^timetable=\d{2}-\d{2}$", value) and not re.match(r"^timetable=\d{1}-\d{2}$", value):
            return "Введенные данные не соответствуют формату timetable=хх-хх, где х - это цифры от 0 до 9."
    elif param_name == "Интервал съемки":
        if not re.match(r"^period=\*/\d{1,2}$", value):
            try:
                num = int(value.split('=')[-1])
                if not (1 <= num <= 60):
                    return "Введенные данные не соответствуют формату period=*/х, где х - это число от 1 до 60."
            except ValueError:
                return "Введенные данные не соответствуют формату period=*/х, где х - это число от 1 до 60."
    elif param_name == "Папка на сервере":
        if not re.match(r"^[a-zA-Z0-9_/]{0,30}$", value):
            return "Введенные данные не соответствуют формату х, где х - это любая строка длиной до 30 символов, допустимые символы: цифры, латинские буквы, знак подчеркивания _ и наклонная черта /."
    elif param_name == "IP адрес сервера":
        try:
            ipaddress.ip_address(value)
        except ValueError:
            return "Введенные данные не соответствуют формату корректного IP адреса."
    elif param_name == "Телефон админа 1":
        if not re.match(r"^admin=7\d{9}$", value):
            return "Введенные данные не соответствуют формату: admin=7хххххххххх."
    elif param_name == "Телефон админа 2":
        if not re.match(r"^root=7\d{9}$", value):
            return "Введенные данные не соответствуют формату: root=7хххххххххх."
    elif param_name == "Диапазон температур нагревателя":
        if not re.match(r"^\d{2}-\d{2}$", value):
            return "Введенные данные не соответствуют формату хх-хх, где х - это цифры от 0 до 9."
    return None

# WebSocket-события
@socketio.on('connect')
def handle_connect():
    print(f"Клиент подключился: {request.sid}")

@socketio.on('register')
def handle_register(data):
    client_id = int(data['client_id'])
    if client_id in devices:
        devices[client_id]["connected"] = True
        devices[client_id]["sid"] = request.sid
        print(f"Устройство {client_id} подключено с SID {request.sid}")
        emit('registration_success', {'status': 'OK'})
    else:
        emit('error', {'message': f"Устройство {client_id} не найдено"})

@socketio.on('disconnect')
def handle_disconnect():
    for device_id, device in devices.items():
        if device["sid"] == request.sid:
            device["connected"] = False
            device["sid"] = None
            print(f"Устройство {device_id} отключено")
            break

@socketio.on('response')
def handle_response(data):
    client_id = data.get('client_id')
    response = data.get('response')
    command = data.get('command')
    print(f"Получен ответ от устройства {client_id}: {response} для команды {command}")
    if command == 'read_param':
        param_name = data.get('param_name')
        device_params[client_id][param_name] = response
    elif command == 'test_photo' and response.startswith('PHOTO_OK'):
        # Предполагается, что устройство отправляет путь к файлу
        photo_path = response.split(':')[1] if ':' in response else "test_photo.jpg"
        device_params[client_id]["Тестовое фото"] = photo_path

def send_command(client_id, command, data=None):
    if client_id in devices and devices[client_id]["connected"]:
        socketio.emit('command', {'command': command, 'data': data, 'client_id': client_id}, to=devices[client_id]["sid"])
        print(f"Отправлена команда устройству {client_id}: {command}")

# Функции для работы с устройствами
def read_device_params(device_id, param_name):
    send_command(device_id, 'read_param', {'param_name': param_name})

def write_device_params(device_id, params):
    param_name, value = next(iter(params.items()))
    send_command(device_id, 'write_param', {'param_name': param_name, 'value': value})

def control_heater(device_id, action):
    send_command(device_id, 'heater', {'action': action})

def create_test_photo(device_id):
    send_command(device_id, 'test_photo')
    return "test_photo.jpg"  # Заглушка, путь будет обновлен в handle_response

# Маршруты Flask
@app.route('/')
def index():
    return render_template('index.html', devices=devices)

@app.route('/get_devices')
def get_devices():
    return jsonify(devices)

@app.route('/disconnect/<int:device_id>')
def disconnect(device_id):
    if devices[device_id]["connected"]:
        send_command(device_id, 'disconnect')
        devices[device_id]["connected"] = False
        devices[device_id]["sid"] = None
        print(f"Устройство {device_id} отключено")
    return redirect(url_for('index'))

@app.route('/device/<int:device_id>', methods=['GET', 'POST'])
def device_page(device_id):
    if not devices[device_id]["connected"]:
        print(f"Устройство {device_id} не подключено, перенаправляем на главную")
        return redirect(url_for('index'))

    params = device_params[device_id]
    error_message = None

    if request.method == 'POST':
        print(f"Получен POST-запрос: {request.form}")

        if 'action' in request.form:
            param_name = request.form.get('param_name')
            action = request.form.get('action')
            print(f"Действие: {action}, Параметр: {param_name}")

            if action == 'read':
                read_device_params(device_id, param_name)
            elif action == 'write':
                new_value = request.form.get('value')
                print(f"Попытка записи: {param_name} = {new_value}")
                error_message = validate_param(param_name, new_value)
                if error_message is None:
                    params[param_name] = new_value
                    write_device_params(device_id, {param_name: new_value})

        elif 'heater_action' in request.form:
            heater_action = request.form.get('heater_action')
            state = "Включен" if heater_action == "turn_on" else "Выключен"
            control_heater(device_id, heater_action)
            params["Состояние нагревателя"] = state

        elif 'test_photo' in request.form:
            photo_path = create_test_photo(device_id)
            if os.path.exists(photo_path):
                return send_file(photo_path, as_attachment=True)
            else:
                error_message = "Тестовое фото не найдено"

    return render_template('device.html', device_id=device_id, device_name=devices[device_id]["name"], params=params, error_message=error_message)

@app.route('/log/<int:log_id>')
def log_page(log_id):
    log_content = logs.get(log_id, ["Лог не найден"])
    return render_template('log.html', log_id=log_id, log_content=log_content)

@app.route('/favicon.ico')
def favicon():
    return '', 204

if __name__ == '__main__':
    # Для локального тестирования
    socketio.run(app, host='0.0.0.0', port=int(os.getenv('PORT', 5000)))



