from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'masjid-Sumorame-Sidoarjo'

# Database inisiasi
def init_db():
    conn = sqlite3.connect('masjid.db')
    c = conn.cursor()
    
    # tabel admin
    c.execute('''CREATE TABLE IF NOT EXISTS admin (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 username TEXT UNIQUE NOT NULL,
                 password TEXT NOT NULL)''')
    
    # kajian tabel
    c.execute('''CREATE TABLE IF NOT EXISTS kajian (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 nama_ustaz TEXT NOT NULL,
                 tema_kajian TEXT NOT NULL,
                 hari TEXT NOT NULL,
                 tanggal TEXT NOT NULL,
                 waktu TEXT NOT NULL,
                 lokasi TEXT NOT NULL,
                 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # default admin jika tidak ada
    c.execute("SELECT * FROM admin WHERE username = ?", ('admin',))
    if not c.fetchone():
        hashed_password = generate_password_hash('admin123')
        c.execute("INSERT INTO admin (username, password) VALUES (?, ?)", ('admin', hashed_password))
    
    # isi kajian
    c.execute("SELECT COUNT(*) FROM kajian")
    if c.fetchone()[0] == 0:
        sample_kajian = [
            ('Ustaz Ahmad Hidayat', 'Tafsir Al-Quran Surah Al-Baqarah', 'Senin', '2024-01-15', '19:30', 'Ruang Utama'),
            ('Ustaz Muhammad Yusuf', 'Hadits Shahih Bukhari', 'Rabu', '2024-01-17', '20:00', 'Ruang Kajian'),
            ('Ustaz Abdullah Rahman', 'Fiqih Shalat dan Wudu', 'Jumat', '2024-01-19', '19:45', 'Ruang Utama'),
            ('Ustaz Ismail Hakim', 'Sirah Nabawiyah', 'Minggu', '2024-01-21', '20:15', 'Ruang Kajian')
        ]
        c.executemany("INSERT INTO kajian (nama_ustaz, tema_kajian, hari, tanggal, waktu, lokasi) VALUES (?, ?, ?, ?, ?, ?)", sample_kajian)
    
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = sqlite3.connect('masjid.db')
        c = conn.cursor()
        c.execute("SELECT * FROM admin WHERE username = ?", (username,))
        admin = c.fetchone()
        conn.close()
        
        if admin and check_password_hash(admin[2], password):
            session['admin_logged_in'] = True
            session['admin_username'] = username
            flash('Login berhasil!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Username atau password salah!', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    session.pop('admin_username', None)
    flash('Logout berhasil!', 'success')
    return redirect(url_for('index'))

@app.route('/admin')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        flash('Silakan login terlebih dahulu!', 'error')
        return redirect(url_for('login'))
    
    search_query = request.args.get('search', '')
    
    conn = sqlite3.connect('masjid.db')
    c = conn.cursor()
    
    if search_query:
        c.execute("SELECT * FROM kajian WHERE nama_ustaz LIKE ? OR hari LIKE ? ORDER BY tanggal DESC", 
                 (f'%{search_query}%', f'%{search_query}%'))
    else:
        c.execute("SELECT * FROM kajian ORDER BY tanggal DESC")
    
    kajian_list = c.fetchall()
    conn.close()
    
    return render_template('admin_dashboard.html', kajian_list=kajian_list, search_query=search_query)

@app.route('/admin/kajian/add', methods=['GET', 'POST'])
def add_kajian():
    if not session.get('admin_logged_in'):
        flash('Silakan login terlebih dahulu!', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        nama_ustaz = request.form['nama_ustaz']
        tema_kajian = request.form['tema_kajian']
        hari = request.form['hari']
        tanggal = request.form['tanggal']
        waktu = request.form['waktu']
        lokasi = request.form['lokasi']
        
        conn = sqlite3.connect('masjid.db')
        c = conn.cursor()
        c.execute("INSERT INTO kajian (nama_ustaz, tema_kajian, hari, tanggal, waktu, lokasi) VALUES (?, ?, ?, ?, ?, ?)",
                 (nama_ustaz, tema_kajian, hari, tanggal, waktu, lokasi))
        conn.commit()
        conn.close()
        
        flash('Kajian berhasil ditambahkan!', 'success')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('add_kajian.html')

@app.route('/admin/kajian/edit/<int:id>', methods=['GET', 'POST'])
def edit_kajian(id):
    if not session.get('admin_logged_in'):
        flash('Silakan login terlebih dahulu!', 'error')
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('masjid.db')
    c = conn.cursor()
    
    if request.method == 'POST':
        nama_ustaz = request.form['nama_ustaz']
        tema_kajian = request.form['tema_kajian']
        hari = request.form['hari']
        tanggal = request.form['tanggal']
        waktu = request.form['waktu']
        lokasi = request.form['lokasi']
        
        c.execute("UPDATE kajian SET nama_ustaz=?, tema_kajian=?, hari=?, tanggal=?, waktu=?, lokasi=? WHERE id=?",
                 (nama_ustaz, tema_kajian, hari, tanggal, waktu, lokasi, id))
        conn.commit()
        conn.close()
        
        flash('Kajian berhasil diperbarui!', 'success')
        return redirect(url_for('admin_dashboard'))
    
    c.execute("SELECT * FROM kajian WHERE id = ?", (id,))
    kajian = c.fetchone()
    conn.close()
    
    if not kajian:
        flash('Kajian tidak ditemukan!', 'error')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('edit_kajian.html', kajian=kajian)

@app.route('/admin/kajian/delete/<int:id>')
def delete_kajian(id):
    if not session.get('admin_logged_in'):
        flash('Silakan login terlebih dahulu!', 'error')
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('masjid.db')
    c = conn.cursor()
    c.execute("DELETE FROM kajian WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    
    flash('Kajian berhasil dihapus!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/kajian')
def kajian_public():
    search_query = request.args.get('search', '')
    
    conn = sqlite3.connect('masjid.db')
    c = conn.cursor()
    
    if search_query:
        c.execute("SELECT * FROM kajian WHERE nama_ustaz LIKE ? OR hari LIKE ? ORDER BY tanggal DESC", 
                 (f'%{search_query}%', f'%{search_query}%'))
    else:
        c.execute("SELECT * FROM kajian ORDER BY tanggal DESC")
    
    kajian_list = c.fetchall()
    conn.close()
    
    return render_template('kajian_public.html', kajian_list=kajian_list, search_query=search_query)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)