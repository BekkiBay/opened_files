import os
import sys
import threading
import subprocess
import datetime
import requests
from flask import Flask, request, jsonify, render_template_string, redirect, session
import webview

# === Конфигурация приложения ===
__VERSION__ = "v1"
VERSION_URL = "https://raw.githubusercontent.com/Xenox681/opened_files/refs/heads/main/version.txt"
SECRET_KEY = "j4f8Jd9sK!mP0qR#vZx7L"

# Локальные учётные записи (логин:пароль)
USERS = {
    "builova":     "pass123",
    "abdusalomov": "pass123",
    "botirov":     "pass123",
    "ergashev":    "pass123",
}

# Telegram Bot
TELEGRAM_TOKEN = "7829442090:AAGiNwSyWL-atfdmicOMXwL-ESLdVjMVfUM"
ADMIN_CHAT_ID = "-1002604524764"


# Меню: два уровня «Регионы» и «Ташкент»
MENU = {
    "Регионы": {
        "Андижан": {
            "Дефолт":    {"Андижан - дефолт": "x.rtf"},
            "Сценарии": {"Андижан - сценарий": "andijan_only_auto_prolong_v2.exe"}
        },
        "Фергана": {
            "Дефолт":    {"Фергана - дефолт": "fergana_default_prolong_v2.exe"},
            "Сценарии": {"Фергана - сценарий": "fergana_only_auto_prolong_v2.exe"}
        },
        "Самарканд": {
            "Дефолт":    {"Самарканд - дефолт": "samarkand_default_prolong_v2.exe"},
            "Сценарии": {"Самарканд - сценарий": "samarkand_only_auto_prolong_v2.exe"}
        },
        "Бухара": {
            "Дефолт":    {"Бухара - дефолт": "bukhara_default_prolong_v2.exe"},
            "Сценарии": {"Бухара - сценарий": "bukhara_only_auto_prolong_v2.exe"}
        },
        "Навои": {
            "Дефолт":    {"Навои - дефолт": "navoi_default_prolong_v2.exe"},
            "Сценарии": {"Навои - сценарий": "navoi_only_auto_prolong_v2.exe"}
        },
        "Наманган": {
            "Дефолт":    {"Наманган - дефолт": "namangan_default_prolong_v2.exe"},
            "Сценарии": {"Наманган - сценарий": "namangan_only_auto_prolong_v2.exe"}
        },
        "Коканд": {
            "Дефолт":    {"Коканд - дефолт": "kokand_default_prolong_v2.exe"},
            "Сценарии": {"Коканд - сценарий": "kokand_only_auto_prolong_v2.exe"}
        },
        "Карши": {
            "Дефолт":    {"Карши - дефолт": "karshi_default_prolong_v2.exe"},
            "Сценарии": {"Карши - сценарий": "karshi_only_auto_prolong_v2.exe"}
        },
        "Ургенч": {
            "Дефолт":    {"Ургенч - дефолт": "urgench_default_prolong_v2.exe"},
            "Сценарии": {"Ургенч - сценарий": "urgench_only_auto_prolong_v2.exe"}
        },
        "Чирчик": {
            "Дефолт":    {"Чирчик - дефолт": "chirchik_default_prolong_v2.exe"},
            "Сценарии": {"Чирчик - сценарий": "chirchik_only_auto_prolong_v2.exe"}
        },
        "Нукус": {
            "Дефолт":    {"Нукус - дефолт": "nukus_default_prolong_v2.exe"},
            "Сценарии": {"Нукус - сценарий": "nukus_only_auto_prolong_v2.exe"}
        }
    },
    "Ташкент": {
        "Дефолт":    {"Ташкент - дефолт": "tashkent_default_prolong_v2.exe"},
        "Сценарии": {"Ташкент - сценарий": "tashkent_only_auto_prolong_v2.exe"}
    }
}

# Инициализация Flask-приложения
# Инициализация Flask-приложения
app = Flask(__name__)
app.secret_key = SECRET_KEY

# ==================== Шаблоны ====================

# 1) Страница входа
LOGIN_HTML = '''
<!doctype html>
<html lang="ru">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Авторизация</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
<style>body{background: linear-gradient(135deg, #89F7FE, #66A6FF);height:100vh;display:flex;justify-content:center;align-items:center;} .card{border-radius:1rem;box-shadow:0 4px 20px rgba(0,0,0,0.1);width:100%;max-width:400px;} .btn-primary{background:linear-gradient(135deg,#4A00E0,#8E2DE2);border:none;color:#fff;box-shadow:0 4px 15px rgba(0,0,0,0.1);transition:background .3s;width:100%;} .btn-primary:hover{background:linear-gradient(135deg,#3E00B5,#7A1EC1);} </style>
</head><body>
  <div class="card"><div class="card-body">
    <h4 class="text-center mb-4">Вход в систему</h4>
    <form method="post" action="/login">
      <div class="mb-3"><label>Логин</label><input type="text" name="login" class="form-control" required></div>
      <div class="mb-3"><label>Пароль</label><input type="password" name="password" class="form-control" required></div>
      {% if error %}<div class="alert alert-danger">{{ error }}</div>{% endif %}
      <button type="submit" class="btn btn-primary">Войти</button>
    </form>
  </div></div>
</body></html>'''

# 2) Основной интерфейс
INDEX_HTML = '''
<!doctype html>
<html lang="ru">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Launcher v{{ version }}</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
<style>
  /* Градиентный фон */
  body { background: linear-gradient(135deg, #FF9A9E 0%, #FAD0C4 100%); min-height:100vh; }
  /* Карточка меню */
  .card-menu { cursor:pointer; transition: transform .2s; border:none; border-radius:.75rem; box-shadow:0 4px 15px rgba(0,0,0,0.1); background:#fff; }
  .card-menu:hover { transform:scale(1.03); }
  .nav-info a { text-decoration:none; color:#333; }
  .nav-info a:hover { text-decoration:underline; }
  .card-menu .card-body { padding: 2rem; text-align: center; }
</style>
</head>
<body>
<nav class="navbar bg-white shadow-sm"><div class="container-fluid">
  {% if parent_path %}<a href="?path={{ parent_path }}" class="btn btn-outline-secondary btn-sm">← Назад</a>{% endif %}
  <span class="nav-info">Пользователь: {{ user }} | <a href="/logout">Выйти</a></span>
</div></nav>
<div class="container py-5"><div class="row g-4">
  {% for label, submenu in menu.items() %}
    <div class="col-12 col-md-6 col-lg-4">
      {% if submenu is mapping %}
        <div class="card-menu h-100 card" onclick="location.href='?path={{ path + '/' + label if path else label }}'">
          <div class="card-body"><h5>{{ label }}</h5><p class="text-muted">Перейти</p></div>
        </div>
      {% else %}
        <div class="card-menu h-100 card" onclick="activate('{{ submenu }}','{{ label }}','{{ path }}')">
          <div class="card-body"><h5>{{ label }}</h5><p class="text-muted">Запустить конфиг</p></div>
        </div>
      {% endif %}
    </div>
  {% endfor %}
</div></div>
<script>
  // Получаем текущее имя пользователя из шаблона
  const currentUser = "{{ user }}";
  /**
   * Запускает EXE/файл, отправляет уведомление и перенаправляет на дашборд
   */
  function activate(exe, label, path) {
    if (!confirm(`Вы уверены, что хотите запустить «${label}»?`)) return;
    // Шаг 1: вызвать серверный маршрут активации
    fetch('/activate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({exe, label, path})
    })
    .then(res => res.json())
    .then(data => {
      if (!data.success) {
        throw new Error(data.error || 'Не удалось запустить файл');
      }
      // Шаг 2: отправить уведомление через бота
      const notifyUrl = `/notify?user=${encodeURIComponent(currentUser)}&label=${encodeURIComponent(label)}`;
      return fetch(notifyUrl);
    })
    .then(() => {
      // Шаг 3: перенаправление на дашборд после всех операций
      window.location.href = 'https://superset.internal.uzumtezkor.uz/superset/dashboard/641/';
    })
    .catch(err => {
      alert('Ошибка: ' + err.message);
    });
  }
</script>
</body>
</html>'''

# ==================== Логика приложения ====================

def check_version():
    try:
        r = requests.get(VERSION_URL, timeout=5)
        r.raise_for_status()
        remote = r.text.strip()
    except Exception as e:
        sys.exit(f"Не удалось проверить версию: {e}")
    if remote != __VERSION__:
        sys.exit(f"Неактуальная версия: ожидалось {__VERSION__}, на сервере {remote}.")

def send_telegram_message(user, label):
    """Отправка уведомления боту о запуске конфигурации"""
    ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    text = f"User {user} запустил '{label}' в {ts}"
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": ADMIN_CHAT_ID, "text": text}
    try:
        requests.post(url, data=payload)
    except:
        pass

from functools import wraps
from flask import redirect

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user' not in session:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated

@app.route('/login', methods=['GET','POST'])
def login():
    error=None
    if request.method=='POST':
        u=request.form['login'].lower(); p=request.form['password']
        if USERS.get(u)==p:
            session['user']=u
            return redirect('/')
        else:
            error='Неверный логин или пароль'
    return render_template_string(LOGIN_HTML, error=error)

@app.route('/logout')
def logout(): session.clear(); return redirect('/login')

@app.route('/')
@login_required
def index():
    raw=request.args.get('path','')
    parts=raw.split('/') if raw else []
    node=MENU
    for part in parts: node=node.get(part,{})
    parent='/'.join(parts[:-1])
    return render_template_string(INDEX_HTML, version=__VERSION__, user=session['user'], menu=node, path=raw, parent_path=parent)

@app.route('/activate', methods=['POST'])
@login_required
def activate():
    # Получаем данные из запроса
    data = request.get_json()
    exe = data.get('exe')
    label = data.get('label')  # получаем метку для уведомления
    # Полный путь к файлу
    file_path = os.path.join(os.getcwd(), exe)
    try:
        # Шаг 1: запуск файла
        if exe.lower().endswith('.exe'):
            subprocess.Popen([file_path])
        else:
            if sys.platform.startswith('win'):
                os.startfile(file_path)
            elif sys.platform == 'darwin':
                subprocess.Popen(['open', file_path])
            else:
                subprocess.Popen(['xdg-open', file_path])
        # Шаг 2: отправка уведомления в Telegram
        send_telegram_message(session['user'], label)
        # Шаг 3: открываем дашборд в браузере
        import webbrowser
        webbrowser.open('https://superset.internal.uzumtezkor.uz/superset/dashboard/641/')
        return jsonify(success=True)
    except Exception as e:
        return jsonify(success=False, error=str(e))
    except Exception as e:
        return jsonify(success=False, error=str(e))

@app.route('/notify')
def notify():
    user=request.args.get('user')
    label=request.args.get('label')
    send_telegram_message(user, label)
    return ('', 204)

if __name__=='__main__':
    check_version()
    threading.Thread(target=lambda: app.run('127.0.0.1', 8164, debug=False, use_reloader=False), daemon=True).start()
    webview.create_window('Launcher', 'http://127.0.0.1:8164')
    webview.start()