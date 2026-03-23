from flask import Flask, request, render_template, make_response
import re

app = Flask(__name__)
app.secret_key = 'super_secret_key'  # Нужен для работы с сессиями/куки, если потребуется


# --- 1. Отображение данных запроса ---
@app.route('/')
def index():
    return render_template('base.html')


@app.route('/url-params')
def show_url_params():
    # request.args возвращает ImmutableMultiDict, преобразуем в dict для удобства
    params = request.args.to_dict()
    return render_template('url_params.html', params=params)


@app.route('/headers')
def show_headers():
    # request.headers возвращает EnvironHeaders
    headers = dict(request.headers)
    return render_template('headers.html', headers=headers)


@app.route('/cookies')
def handle_cookies():
    cookie_name = 'test_flask_cookie'
    current_value = request.cookies.get(cookie_name)

    response = make_response(render_template('cookies.html', current_value=current_value))

    if current_value:
        # Если кука есть - удаляем
        response.delete_cookie(cookie_name)
    else:
        # Если куки нет - устанавливаем
        response.set_cookie(cookie_name, 'cookie_value_123')

    return response


@app.route('/form-params', methods=['GET', 'POST'])
def show_form_params():
    data = {}
    if request.method == 'POST':
        # request.form содержит данные формы
        data = request.form.to_dict()
    return render_template('form_params.html', data=data, method=request.method)


# --- 2. Форма с обработкой ошибок (Телефон) ---

@app.route('/phone', methods=['GET', 'POST'])
def phone_validation():
    error_message = None
    formatted_phone = None
    is_invalid = False

    if request.method == 'POST':
        phone = request.form.get('phone', '')

        # 1. Сначала проверяем пустой ввод
        if not phone.strip():
            error_message = 'Недопустимый ввод. Неверное количество цифр.'
            is_invalid = True
        else:
            # 2. Проверка на недопустимые символы
            # Разрешены: цифры, пробелы, (), -, ., +
            allowed_pattern = r'^[\d\s\(\)\-\.\+]+$'
            if not re.match(allowed_pattern, phone):
                error_message = 'Недопустимый ввод. В номере телефона встречаются недопустимые символы.'
                is_invalid = True
            else:
                # 3. Извлекаем только цифры
                digits = re.sub(r'\D', '', phone)
                digit_count = len(digits)

                # 4. Проверка количества цифр
                # Логика: если начинается с +7 или 8 (в исходной строке или в цифрах), то должно быть 11
                # Иначе 10.
                # Примечание: в очищенных цифрах +7 превращается в 7.
                # Проверяем исходную строку на наличие +7 или 8 в начале, либо просто длину цифр.
                # ТЗ: "номер должен содержать 11 цифр если он начинается с «+7» или «8»"

                starts_with_7_or_8 = phone.strip().startswith('+7') or phone.strip().startswith('8') or digits.startswith(
                    '7') or digits.startswith('8')

                expected_length = 11 if starts_with_7_or_8 else 10

                if digit_count != expected_length:
                    error_message = "Недопустимый ввод. Неверное количество цифр."
                    is_invalid = True
                else:
                    # 5. Форматирование 8-***-***-**-**
                    # Нормализуем к 8 (если началось с 7, меняем на 8)
                    if digits.startswith('7'):
                        digits = '8' + digits[1:]
                    elif not digits.startswith('8') and len(digits) == 10:
                        # Если ввели локальный номер (10 цифр), добавляем 8 спереди для формата
                        digits = '8' + digits

                    # Собираем формат 8-XXX-XXX-XX-XX
                    # digits сейчас должен быть 11 цифр, начинающихся с 8
                    if len(digits) == 11:
                        formatted_phone = f"{digits[0]}-{digits[1:4]}-{digits[4:7]}-{digits[7:9]}-{digits[9:11]}"
                    else:
                        # fallback на случай 10 цифр без 8 (хотя логика выше должна была добавить 8)
                        formatted_phone = f"8-{digits[0:3]}-{digits[3:6]}-{digits[6:8]}-{digits[8:10]}"

    return render_template('phone_form.html',
                           error_message=error_message,
                           formatted_phone=formatted_phone,
                           is_invalid=is_invalid)


if __name__ == '__main__':
    app.run(debug=True)