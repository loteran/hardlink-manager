#!/usr/bin/env python3
from flask import Flask, render_template, request, jsonify, redirect, url_for
import os, json
from pathlib import Path

app = Flask(__name__)
SETTINGS_FILE = Path(__file__).parent / 'settings.json'
DEFAULT_SETTINGS = {'base_paths': ['/mnt/Stockage', '/mnt/Stockage2'], 'default_dest': '/mnt/Stockage/Downloads'}

def load_settings():
    try:
        if SETTINGS_FILE.exists():
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return DEFAULT_SETTINGS
    except:
        return DEFAULT_SETTINGS

settings = load_settings()
BASE_PATHS = settings.get('base_paths', DEFAULT_SETTINGS['base_paths'])
DEFAULT_DESTINATION = settings.get('default_dest', DEFAULT_SETTINGS['default_dest'])

def get_directory_tree(path, max_depth=3, current_depth=0):
    if current_depth >= max_depth:
        return []
    try:
        items = []
        all_items = list(Path(path).iterdir())
        dirs = sorted([i for i in all_items if i.is_dir()], key=lambda x: x.name.lower())
        files = sorted([i for i in all_items if i.is_file()], key=lambda x: x.name.lower())
        for item in dirs:
            items.append({'name': item.name, 'path': str(item), 'type': 'directory', 'children': get_directory_tree(str(item), max_depth, current_depth + 1) if current_depth < max_depth - 1 else []})
        for item in files:
            items.append({'name': item.name, 'path': str(item), 'type': 'file', 'size': item.stat().st_size})
        return items
    except PermissionError:
        return []
    except Exception as e:
        print(f"Error: {e}")
        return []

@app.route('/')
def index():
    global settings, BASE_PATHS, DEFAULT_DESTINATION
    settings = load_settings()
    BASE_PATHS = settings.get('base_paths', DEFAULT_SETTINGS['base_paths'])
    DEFAULT_DESTINATION = settings.get('default_dest', DEFAULT_SETTINGS['default_dest'])
    return render_template('index.html', default_dest=DEFAULT_DESTINATION)

@app.route('/settings', methods=['GET'])
def settings_page():
    s = load_settings()
    return render_template('settings.html', base_paths=s.get('base_paths', []), default_dest=s.get('default_dest', ''))

@app.route('/settings', methods=['POST'])
def save_settings_route():
    bp = request.form.get('base_paths', '')
    dd = request.form.get('default_dest', '')
    base_paths = [l.strip() for l in bp.splitlines() if l.strip()]
    new_settings = {'base_paths': base_paths, 'default_dest': dd}
    try:
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(new_settings, f, indent=2, ensure_ascii=False)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/browse')
def browse():
    path = request.args.get('path', '/')
    if path == '/':
        items = [{'name': p, 'path': p, 'type': 'directory'} for p in settings.get('base_paths', BASE_PATHS)]
        return jsonify(items)
    return jsonify(get_directory_tree(path, max_depth=1))

@app.route('/api/browse_all')
def browse_all():
    """Parcourir tout le système de fichiers (pour la page settings)"""
    path = request.args.get('path', '/')
    try:
        items = []
        p = Path(path)
        if not p.exists():
            return jsonify([])
        all_items = list(p.iterdir())
        dirs = sorted([i for i in all_items if i.is_dir()], key=lambda x: x.name.lower())
        for d in dirs:
            items.append({'name': d.name, 'path': str(d), 'type': 'directory'})
        return jsonify(items)
    except PermissionError:
        return jsonify([])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/create_hardlink', methods=['POST'])
def create_hardlink():
    data = request.json
    src, dst = data.get('source'), data.get('destination')
    if not src or not dst:
        return jsonify({'success': False, 'error': 'Required'}), 400
    sp, dp = Path(src), Path(dst)
    if not sp.exists() or not sp.is_file():
        return jsonify({'success': False, 'error': 'Source invalid'}), 400
    if not dp.parent.exists():
        return jsonify({'success': False, 'error': 'Dest dir missing'}), 400
    try:
        os.link(src, dst)
        si = sp.stat().st_ino
        di = dp.stat().st_ino
        if si == di:
            return jsonify({'success': True, 'inode': si, 'link_count': sp.stat().st_nlink})
        return jsonify({'success': False, 'error': 'Inode mismatch'}), 500
    except FileExistsError:
        return jsonify({'success': False, 'error': 'Dest exists'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/check_file')
def check_file():
    path = request.args.get('path')
    if not path:
        return jsonify({'error': 'Path required'}), 400
    fp = Path(path)
    if not fp.exists():
        return jsonify({'error': 'Not found'}), 404
    st = fp.stat()
    return jsonify({'exists': True, 'size': st.st_size, 'inode': st.st_ino, 'link_count': st.st_nlink, 'is_hardlink': st.st_nlink > 1})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
