#!/usr/bin/env python3
"""
HardLink Manager - Web interface for creating hard links
"""

from flask import Flask, render_template, request, jsonify
import os
import subprocess
from pathlib import Path

app = Flask(__name__)

# Configuration
BASE_PATHS = [
    '/mnt/Stockage',
    '/mnt/Stockage2'
]

DEFAULT_DESTINATION = '/mnt/Stockage/Downloads'

def get_directory_tree(path, max_depth=3, current_depth=0):
    """Get directory tree structure"""
    if current_depth >= max_depth:
        return []

    try:
        items = []
        # Get all items and sort them properly
        all_items = list(Path(path).iterdir())

        # Sort: directories first, then files, alphabetically
        dirs = sorted([item for item in all_items if item.is_dir()], key=lambda x: x.name.lower())
        files = sorted([item for item in all_items if item.is_file()], key=lambda x: x.name.lower())

        # Add directories
        for item in dirs:
            items.append({
                'name': item.name,
                'path': str(item),
                'type': 'directory',
                'children': get_directory_tree(str(item), max_depth, current_depth + 1) if current_depth < max_depth - 1 else []
            })

        # Add files
        for item in files:
            items.append({
                'name': item.name,
                'path': str(item),
                'type': 'file',
                'size': item.stat().st_size
            })

        return items
    except PermissionError:
        return []
    except Exception as e:
        print(f"Error reading {path}: {e}")
        return []

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html', default_dest=DEFAULT_DESTINATION)

@app.route('/api/browse')
def browse():
    """Browse directories"""
    path = request.args.get('path', '/')

    if path == '/':
        # Return base paths
        items = [{'name': p, 'path': p, 'type': 'directory'} for p in BASE_PATHS]
        return jsonify(items)

    items = get_directory_tree(path, max_depth=1)
    return jsonify(items)

@app.route('/api/create_hardlink', methods=['POST'])
def create_hardlink():
    """Create a hard link"""
    data = request.json
    source = data.get('source')
    destination = data.get('destination')

    if not source or not destination:
        return jsonify({'success': False, 'error': 'Source and destination required'}), 400

    # Validate paths
    source_path = Path(source)
    dest_path = Path(destination)

    if not source_path.exists():
        return jsonify({'success': False, 'error': 'Source file does not exist'}), 400

    if not source_path.is_file():
        return jsonify({'success': False, 'error': 'Source must be a file'}), 400

    # Check if on same filesystem
    source_stat = source_path.stat()
    dest_parent = dest_path.parent

    if not dest_parent.exists():
        return jsonify({'success': False, 'error': 'Destination directory does not exist'}), 400

    dest_stat = dest_parent.stat()

    if source_stat.st_dev != dest_stat.st_dev:
        return jsonify({'success': False, 'error': 'Source and destination must be on the same filesystem'}), 400

    # Create hard link
    try:
        os.link(source, destination)

        # Verify it's a hard link
        source_inode = source_path.stat().st_ino
        dest_inode = dest_path.stat().st_ino

        if source_inode == dest_inode:
            return jsonify({
                'success': True,
                'message': f'Hard link created successfully',
                'inode': source_inode,
                'link_count': source_path.stat().st_nlink
            })
        else:
            return jsonify({'success': False, 'error': 'Link created but inodes do not match'}), 500

    except FileExistsError:
        return jsonify({'success': False, 'error': 'Destination file already exists'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/check_file')
def check_file():
    """Check file information"""
    path = request.args.get('path')

    if not path:
        return jsonify({'error': 'Path required'}), 400

    file_path = Path(path)

    if not file_path.exists():
        return jsonify({'error': 'File does not exist'}), 404

    stat = file_path.stat()

    return jsonify({
        'exists': True,
        'size': stat.st_size,
        'inode': stat.st_ino,
        'link_count': stat.st_nlink,
        'is_hardlink': stat.st_nlink > 1
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
