from flask import Flask, render_template, request, redirect, url_for, jsonify
import os
import sqlite3
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Folder to store uploaded images
UPLOAD_FOLDER = 'static/uploads/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload directory exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Allowed extensions for image files
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Database connection
def get_db_connection():
    conn = sqlite3.connect('db.sqlite3')
    conn.row_factory = sqlite3.Row
    return conn

# Create the table for storing image metadata
def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            filepath TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Initialize the database
init_db()

# Check if the file has a valid extension
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    conn = get_db_connection()
    images = conn.execute('SELECT * FROM images').fetchall()
    conn.close()
    return render_template('index.html', images=images)

@app.route('/upload', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return redirect(request.url)

    file = request.files['image']

    if file.filename == '':
        return redirect(request.url)

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        conn = get_db_connection()
        conn.execute('INSERT INTO images (filename, filepath) VALUES (?, ?)', (filename, filepath))
        conn.commit()
        conn.close()

        return redirect(url_for('index'))

    return redirect(request.url)

# Updated delete route to return a JSON response
@app.route('/delete/<int:image_id>', methods=['POST'])
def delete_image(image_id):
    conn = get_db_connection()
    image = conn.execute('SELECT * FROM images WHERE id = ?', (image_id,)).fetchone()

    if image:
        os.remove(image['filepath'])  # Remove the file from the server
        conn.execute('DELETE FROM images WHERE id = ?', (image_id,))
        conn.commit()
        conn.close()

        # Return a success response with the image ID
        return jsonify({'success': True, 'image_id': image_id})

    conn.close()
    return jsonify({'success': False}), 404

if __name__ == '__main__':
    app.run(debug=True)
