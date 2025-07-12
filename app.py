from flask import Flask, request, render_template, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
import sqlite3
import os

from utils import load_malaria_model, predict_image

app = Flask(__name__)
app.secret_key = 'your-secret-key'
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# Mail config
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = 'confidenceehiemere1@gmail.com'
app.config['MAIL_PASSWORD'] = 'sxngmsliistiwoyt'

mail = Mail(app)
serializer = URLSafeTimedSerializer(app.secret_key)

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Load model once
model = load_malaria_model()

# ================= AUTH ROUTES =================

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = generate_password_hash(request.form['password'])

        with sqlite3.connect('users.db') as conn:
            cursor = conn.cursor()
            cursor.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, email TEXT UNIQUE, password TEXT)')
            try:
                cursor.execute('INSERT INTO users (email, password) VALUES (?, ?)', (email, password))
                conn.commit()
            except sqlite3.IntegrityError:
                flash("Email already exists.")
                return render_template('signup.html')
        return redirect(url_for('login'))
    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        with sqlite3.connect('users.db') as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
            user = cursor.fetchone()

        if user and check_password_hash(user[2], password):
            session['user'] = user[1]
            return redirect(url_for('index'))
        else:
            flash("Invalid credentials")
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']

        with sqlite3.connect('users.db') as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
            user = cursor.fetchone()

        if user:
            token = serializer.dumps(email, salt='reset-password')
            reset_url = url_for('reset_password', token=token, _external=True)
            msg = Message('Reset Your Password',
                          sender=app.config['MAIL_USERNAME'],
                          recipients=[email])
            msg.body = f"Click here to reset your password: {reset_url}"
            mail.send(msg)
            return "Check your email for a password reset link."
        else:
            flash("Email not found.")
    return render_template('forgot_password.html')


@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = serializer.loads(token, salt='reset-password', max_age=3600)
    except:
        return "Invalid or expired token."

    if request.method == 'POST':
        new_password = generate_password_hash(request.form['password'])

        with sqlite3.connect('users.db') as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE users SET password = ? WHERE email = ?', (new_password, email))
            conn.commit()
        return redirect(url_for('login'))

    return render_template('reset_password.html')


# ================ MALARIA PREDICTION ROUTES ================

@app.route('/')
def index():
    if 'user' not in session:
        return redirect(url_for('login'))

    prediction = session.pop('prediction', None)
    image_url = session.pop('image_url', None)
    return render_template('index.html', prediction=prediction, image_url=image_url)


@app.route('/predict', methods=['POST'])
def predict():
    if 'user' not in session:
        return redirect(url_for('login'))

    if 'image' not in request.files:
        flash("No image uploaded.")
        return redirect(url_for('index'))

    file = request.files['image']
    if file.filename == '':
        flash("No file selected.")
        return redirect(url_for('index'))

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    result = predict_image(filepath, model)

    session['prediction'] = result
    session['image_url'] = filepath

    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
