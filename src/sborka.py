#!/usr/bin/env python3
"""Сборка приложения «Сахалыы саҥар» из исходников.

Исходники (в одной папке со скриптом):
  app.html                — код приложения с метками /*DICT*/, /*AUDIO_FILES*/, <!--PWA--> и <!--PWA-HEAD-->
  dict.json               — словарь (массив ["слово","часть речи","перевод","англ. значение"])
  sw.js                   — заготовка service worker (метки /*VERSION*/, /*AUDIO_FILES*/)
  icon-192.png, icon-512.png, icon-maskable-512.png, apple-touch-icon.png — иконки
  emblem-dark.webp, emblem-light.webp — знак для тёмной и светлой темы (встраиваются в страницу)
  fonts/*.woff2           — шрифты Onest и PT Serif (SIL OFL 1.1), лицензии там же
  splash/launch-*.png     — картинки запуска для iPhone (только версия для сайта)
  ozvuchka/audio-*.json   — озвучка (MP3 в base64), в проект не кладётся, хранится отдельно

Файл manifest.webmanifest отдельно не хранится: он описан ниже в MANIFEST
и создаётся при сборке (телефон не даёт прикреплять такое расширение).

Запуск:
  python3 sborka.py site      → папка build/site/  (версия для сайта, PWA)
  python3 sborka.py offline   → build/sakhalyy-sanar-offline.html (один файл)
  python3 sborka.py both      → и то и другое (по умолчанию)
"""
import base64
import hashlib
import json
import os
import re
import shutil
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(BASE, 'build')
ASSETS = ['icon-192.png', 'icon-512.png', 'icon-maskable-512.png', 'apple-touch-icon.png']
EMBLEMS = ['emblem-dark.webp', 'emblem-light.webp']
FONTS_DIR = 'fonts'
SPLASH_DIR = 'splash'

# Манифест приложения: название, иконки, цвета. Нужен для установки на телефон.
MANIFEST = {
    "name": "Сахалыы саҥар — разговорный якутский",
    "short_name": "Сахалыы саҥар",
    "lang": "ru",
    "start_url": "./",
    "scope": "./",
    "display": "standalone",
    "background_color": "#050B1C",
    "theme_color": "#081128",
    "icons": [
        {"src": "icon-192.png", "sizes": "192x192", "type": "image/png"},
        {"src": "icon-512.png", "sizes": "512x512", "type": "image/png"},
        {"src": "icon-maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"},
    ],
}


def read(name):
    with open(os.path.join(BASE, name), encoding='utf-8') as f:
        return f.read()


def audio_files():
    """Файлы озвучки по порядку имён. Пустой список — сборка без звука."""
    d = os.path.join(BASE, 'ozvuchka')
    if not os.path.isdir(d):
        return []
    return sorted(f for f in os.listdir(d) if f.startswith('audio-') and f.endswith('.json'))


def data_uri(path, mime):
    with open(path, 'rb') as f:
        return f'data:{mime};base64,' + base64.b64encode(f.read()).decode()


def with_emblems(html):
    """Знаки встраиваются в страницу: заставка видна с первого кадра, без отдельной загрузки."""
    for name in EMBLEMS:
        assert html.count(name) == 1, f'в app.html должно быть ровно одно упоминание {name}'
        html = html.replace(name, data_uri(os.path.join(BASE, name), 'image/webp'))
    return html


def font_files():
    d = os.path.join(BASE, FONTS_DIR)
    return sorted(f for f in os.listdir(d) if f.endswith('.woff2'))


def with_dict(html):
    """Подставляет словарь вместо метки /*DICT*/[]."""
    assert '/*DICT*/[]' in html, 'в app.html нет метки /*DICT*/[]'
    data = json.loads(read('dict.json'))
    return html.replace('/*DICT*/[]', json.dumps(data, ensure_ascii=False, separators=(',', ':')), 1)


def build_site():
    out = os.path.join(BUILD, 'site')
    shutil.rmtree(out, ignore_errors=True)
    os.makedirs(out)
    files = audio_files()
    html = with_emblems(with_dict(read('app.html'))).replace('/*AUDIO_FILES*/[]', json.dumps(files), 1)
    with open(os.path.join(out, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(html)
    for name in files:
        shutil.copy(os.path.join(BASE, 'ozvuchka', name), os.path.join(out, name))
    for name in ASSETS:
        shutil.copy(os.path.join(BASE, name), os.path.join(out, name))
    shutil.copytree(os.path.join(BASE, FONTS_DIR), os.path.join(out, FONTS_DIR))
    shutil.copytree(os.path.join(BASE, SPLASH_DIR), os.path.join(out, SPLASH_DIR))
    with open(os.path.join(out, 'manifest.webmanifest'), 'w', encoding='utf-8') as f:
        json.dump(MANIFEST, f, ensure_ascii=False, indent=1)
    # версия меняется при любой правке кода или списка озвучки — по ней обновляется кеш
    h = hashlib.md5((html + ''.join(files)).encode())
    for name in ASSETS + [os.path.join(FONTS_DIR, f) for f in font_files()]:
        with open(os.path.join(BASE, name), 'rb') as f:
            h.update(f.read())
    version = h.hexdigest()[:10]
    fonts = ['./' + FONTS_DIR + '/' + f for f in font_files()]
    sw = (read('sw.js').replace('/*VERSION*/', version, 1).replace('/*AUDIO_FILES*/[]', json.dumps(files), 1)
          .replace('/*FONT_FILES*/[]', json.dumps(fonts), 1))
    with open(os.path.join(out, 'sw.js'), 'w', encoding='utf-8') as f:
        f.write(sw)
    paths = [os.path.join(r, f) for r, _, fs in os.walk(out) for f in fs]
    total = sum(os.path.getsize(p) for p in paths)
    print(f'build/site/ — {len(paths)} файлов, {total / 1e6:.1f} МБ, версия {version}')


def build_offline():
    os.makedirs(BUILD, exist_ok=True)
    html = with_emblems(with_dict(read('app.html')))
    # шрифты внутрь файла — без сети они берутся отсюда
    for name in font_files():
        ref = f'url({FONTS_DIR}/{name})'
        assert html.count(ref) == 1, f'в app.html нет ссылки {ref}'
        html = html.replace(ref, 'url(' + data_uri(os.path.join(BASE, FONTS_DIR, name), 'font/woff2') + ')')
    # озвучка внутрь файла: ключи из всех частей сливаются в один объект
    audio = {}
    for name in audio_files():
        with open(os.path.join(BASE, 'ozvuchka', name), encoding='utf-8') as f:
            audio.update(json.load(f))
    html = html.replace('const BUILTIN_AUDIO={};',
                        'const BUILTIN_AUDIO=' + json.dumps(audio, ensure_ascii=False, separators=(',', ':')) + ';', 1)
    # блок PWA (загрузка озвучки по сети, service worker, плашка обновления) офлайн-файлу не нужен
    html = re.sub(r'<!--PWA-->.*?<!--/PWA-->\n?', '', html, flags=re.S)
    # ссылки на manifest и иконки в одиночном файле ведут в никуда — убираем
    html = re.sub(r'<!--PWA-HEAD-->.*?<!--/PWA-HEAD-->\n?', '', html, flags=re.S)
    assert '<!--PWA-' not in html
    path = os.path.join(BUILD, 'sakhalyy-sanar-offline.html')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f'build/sakhalyy-sanar-offline.html — {os.path.getsize(path) / 1e6:.1f} МБ, '
          f'записей озвучки: {len(audio)}')


if __name__ == '__main__':
    what = sys.argv[1] if len(sys.argv) > 1 else 'both'
    if not audio_files():
        print('Внимание: папка ozvuchka пуста — приложение соберётся без встроенной озвучки.')
    if what in ('site', 'both'):
        build_site()
    if what in ('offline', 'both'):
        build_offline()
    if what not in ('site', 'offline', 'both'):
        print(__doc__)
