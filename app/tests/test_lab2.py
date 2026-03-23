import pytest
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

# --- Тесты части 1: Отображение данных ---

def test_url_params_display(client):
    """Проверка отображения параметров URL"""
    response = client.get('/url-params?key1=value1&key2=value2')
    assert response.status_code == 200
    assert b'key1' in response.data
    assert b'value1' in response.data
    assert b'key2' in response.data
    assert b'value2' in response.data

def test_headers_display(client):
    """Проверка отображения заголовков"""
    response = client.get('/headers')
    assert response.status_code == 200
    # Проверяем наличие стандартного заголовка Host или User-Agent
    assert b'Host' in response.data or b'host' in response.data

def test_cookie_set_logic(client):
    """Проверка установки куки, если её нет"""
    # Первый запрос (куки нет)
    response = client.get('/cookies')
    assert response.status_code == 200
    # Проверяем, что в ответе установлен Set-Cookie
    assert 'Set-Cookie' in response.headers
    assert 'test_flask_cookie' in response.headers['Set-Cookie']

def test_cookie_delete_logic(client):
    """Проверка удаления куки, если она есть"""
    # Сначала устанавливаем
    client.get('/cookies')
    # Второй запрос (кука есть)
    response = client.get('/cookies')
    # Проверяем, что кука удаляется (Max-Age=0 или Expires в прошлом)
    assert 'Set-Cookie' in response.headers
    # В заголовке удаления обычно есть Max-Age=0
    assert 'Max-Age=0' in response.headers['Set-Cookie'] or 'Expires' in response.headers['Set-Cookie']

def test_form_params_post(client):
    """Проверка отображения данных формы после POST"""
    data = {'username': 'Ivan', 'email': 'ivan@test.com'}
    response = client.post('/form-params', data=data)
    assert response.status_code == 200
    assert b'Ivan' in response.data
    assert b'ivan@test.com' in response.data

# --- Тесты части 2: Валидация телефона ---

def test_phone_valid_plus7(client):
    """Валидный номер +7 (11 цифр)"""
    response = client.post('/phone', data={'phone': '+7 (999) 123-45-67'})
    assert response.status_code == 200
    assert '8-999-123-45-67' in response.text
    assert 'is-invalid' not in response.text

def test_phone_valid_8(client):
    """Валидный номер 8 (11 цифр)"""
    response = client.post('/phone', data={'phone': '89991234567'})
    assert response.status_code == 200
    assert '8-999-123-45-67' in response.text

def test_phone_valid_local_10_digits(client):
    """Валидный локальный номер (10 цифр)"""
    response = client.post('/phone', data={'phone': '123.456.75.90'})
    assert response.status_code == 200
    # Ожидаем форматирование с добавленной 8-кой спереди
    assert '8-123-456-75-90' in response.text

def test_phone_invalid_symbols(client):
    """Невалидный номер: недопустимые символы (буквы)"""
    response = client.post('/phone', data={'phone': '+7 (999) ABC-45-67'})
    assert response.status_code == 200
    assert 'Недопустимый ввод. В номере телефона встречаются недопустимые символы.' in response.text
    assert 'is-invalid' in response.text
    assert 'invalid-feedback' in response.text

def test_phone_invalid_length_plus7(client):
    """Невалидный номер +7: неверное количество цифр (9 цифр вместо 11)"""
    response = client.post('/phone', data={'phone': '+7 999 123 45'})
    assert response.status_code == 200
    assert 'Недопустимый ввод. Неверное количество цифр.' in response.text
    assert 'is-invalid' in response.text

def test_phone_invalid_length_local(client):
    """Невалидный локальный номер: 11 цифр без +7/8"""
    # Ввод 11 цифр, но не начинается с 8 или +7. Ожидается 10 цифр.
    response = client.post('/phone', data={'phone': '99912345678'})
    assert response.status_code == 200
    assert 'Недопустимый ввод. Неверное количество цифр.' in response.text

def test_phone_bootstrap_classes_on_error(client):
    """Проверка наличия классов Bootstrap при ошибке"""
    response = client.post('/phone', data={'phone': 'invalid'})
    html = response.data.decode('utf-8')
    assert 'is-invalid' in html
    assert 'invalid-feedback' in html

def test_phone_bootstrap_classes_on_success(client):
    """Проверка отсутствия классов ошибки при успехе"""
    response = client.post('/phone', data={'phone': '89991234567'})
    html = response.data.decode('utf-8')
    assert 'is-invalid' not in html

def test_phone_formatting_complex(client):
    """Проверка форматирования со сложными разделителями"""
    response = client.post('/phone', data={'phone': '+7(123)456-75-90'})
    assert '8-123-456-75-90' in response.text

def test_phone_empty_input(client):
    """Проверка пустого ввода (должна быть ошибка длины)"""
    response = client.post('/phone', data={'phone': ''})
    # Пустая строка -> 0 цифр. Ожидается 10 или 11. Ошибка длины.
    assert 'Неверное количество цифр' in response.text

def test_phone_special_chars_only(client):
    """Проверка ввода только спецсимволов"""
    response = client.post('/phone', data={'phone': '() - . +'})
    # 0 цифр -> ошибка длины
    assert 'Неверное количество цифр' in response.text
    # Символы допустимые, поэтому ошибка символов не должна вылезти
    assert 'недопустимые символы' not in response.text

def test_phone_forbidden_char(client):
    """Проверка символа, которого нет в списке разрешенных (например, @)"""
    response = client.post('/phone', data={'phone': '8999@123456'})
    assert 'недопустимые символы' in response.text

# Итого 15 тестов