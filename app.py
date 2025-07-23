from flask import Flask, request, render_template, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
import sqlite3
import os
import numpy as np
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

from utils import load_malaria_model, predict_image

app = Flask(__name__)
app.secret_key = 'your-secret-key'
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# Mail config
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = 'confidenceehiemere1@gmail.com'
app.config['MAIL_PASSWORD'] = 'sxngmsliistiwoyt'  # App password

mail = Mail(app)
serializer = URLSafeTimedSerializer(app.secret_key)

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Load model and metrics once
model, metrics = load_malaria_model()


# ================= AUTH ROUTES =================

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = generate_password_hash(request.form['password'])

        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, email TEXT UNIQUE, password TEXT)')
        try:
            cursor.execute('INSERT INTO users (email, password) VALUES (?, ?)', (email, password))
            conn.commit()
        except sqlite3.IntegrityError:
            flash("Email already exists.", "danger")
            return redirect(url_for('signup'))
        conn.close()
        flash("Signup successful. Please log in.", "success")
        return redirect(url_for('login'))
    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user[2], password):
            session['user'] = user[1]
            return redirect(url_for('index'))
        else:
            flash("Invalid credentials", "danger")
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']

        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        conn.close()

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
            return "Email not found."
    return render_template('forgot_password.html')


@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = serializer.loads(token, salt='reset-password', max_age=3600)
    except:
        return "Invalid or expired token."

    if request.method == 'POST':
        new_password = generate_password_hash(request.form['password'])

        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET password = ? WHERE email = ?', (new_password, email))
        conn.commit()
        conn.close()
        flash("Password updated successfully. Please login.", "success")
        return redirect(url_for('login'))

    return render_template('reset_password.html')


# ================ MALARIA PREDICTION ROUTES ================

@app.route('/')
def index():
    if 'user' not in session:
        return redirect(url_for('login'))

    prediction = session.pop('prediction', None)
    image_url = session.pop('image_url', None)
    confidence = session.pop('confidence', None)
    accuracy = session.pop('accuracy', None)
    precision = session.pop('precision', None)
    recall = session.pop('recall', None)
    f1 = session.pop('f1', None)

    return render_template('index.html',
                           prediction=prediction,
                           image_url=image_url,
                           confidence=confidence,
                           metrics=metrics,
                           accuracy=accuracy,
                           precision=precision,
                           recall=recall,
                           f1=f1)


@app.route('/predict', methods=['POST'])
def predict():
    if 'user' not in session:
        return redirect(url_for('login'))

    if 'image' not in request.files:
        flash("No image uploaded.", "danger")
        return redirect(url_for('index'))

    file = request.files['image']
    if file.filename == '':
        flash("No file selected.", "danger")
        return redirect(url_for('index'))

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    try:
        prediction = predict_image(filepath, model)
        confidence = "High" if prediction == "Parasitized" else "Low"

        # Simulate true label from filename (optional and basic)
        true_label = "Parasitized" if "Parasitized" in filename else "Uninfected"
        y_true = [1 if true_label == "Parasitized" else 0]
        y_pred = [1 if prediction == "Parasitized" else 0]

        accuracy = round(accuracy_score(y_true, y_pred) * 100, 2)
        precision = round(precision_score(y_true, y_pred, zero_division=0) * 100, 2)
        recall = round(recall_score(y_true, y_pred, zero_division=0) * 100, 2)
        f1 = round(f1_score(y_true, y_pred, zero_division=0) * 100, 2)

        session['prediction'] = prediction
        session['image_url'] = filepath
        session['confidence'] = confidence
        session['accuracy'] = accuracy
        session['precision'] = precision
        session['recall'] = recall
        session['f1'] = f1

        return redirect(url_for('index'))

    except Exception as e:
        flash(f"Prediction failed: {str(e)}", "danger")
        return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)

