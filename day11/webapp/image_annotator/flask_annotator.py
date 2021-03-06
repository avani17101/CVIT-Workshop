__author__ = 'Avani'
import io
from contextlib import closing
import pickle
import cv2
from flask import Flask, render_template, jsonify, make_response, flash
import sqlite3
from flask import request, g, redirect,url_for
import numpy 
import hashlib
import os
from werkzeug import secure_filename
import click

# from flask_images import resized_img_src
app = Flask(__name__)
app.config.from_object(__name__)
app.config.from_pyfile('config.cfg')
app.secret_key = 'super secret key'
app.config['UPLOAD_FOLDER'] = 'static/img/'




# def connect_db():
#     return sqlite3.connect(app.config['DATABASE'])


# def init_db():
#     with closing(connect_db()) as db:
#         with app.open_resource('schema.sql', mode='r') as f:
#             db.cursor().executescript(f.read())
#         db.commit()


import sqlite3

import click
from flask import current_app, g
from flask.cli import with_appcontext

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row

    return g.db


def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()

def init_db():
    db = get_db()

    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))


@click.command('init-db')
@with_appcontext
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo('Initialized the database.')

def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)

# init_app(app)
# conn = sqlite3.connect('database.db')
# print("Opened database successfully");

# conn.execute('CREATE TABLE Users (id integer primary key autoincrement,username text not null,email text ,password text)')
# print("Table created successfully");
# conn.close()

def check_password(hashed_password, user_password):
    return hashed_password == hashlib.md5(user_password.encode()).hexdigest()

def validate(username, password):
    con = sqlite3.connect('annotations.db')
    completion = False
    with con:
                cur = con.cursor()
                cur.execute("SELECT * FROM users")
                rows = cur.fetchall()
                for row in rows:
                    dbUser = row[0]
                    dbPass = row[1]
                    if dbUser==username:
                        completion=check_password(dbPass, password)
    return completion

@app.route('/register')
def register():
   return render_template('register.html')

@app.route('/addrec',methods = ['POST', 'GET'])
def addrec():
   if request.method == 'POST':
        try:
            username = request.form['username']
            email = request.form['email']
            password = request.form['password']
            
            with sqlite3.connect("annotations.db") as con:
                cur = con.cursor()
                cur.execute("INSERT INTO users(username,email,password) VALUES (?,?,?)",(username,email,password) )
                con.commit()
                msg = "Record successfully added"
        except:
            con.rollback()
            msg = "error in insert operation"
      
        finally:
            return msg
        #  return render_template("login.html",msg = msg)
        con.close()

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        completion = validate(username, password)
        if completion ==False:
            error = 'Invalid Credentials. Please try again.'
        else:
            return redirect(url_for('/'))
    return render_template('login.html', error=error)

@app.route('/')
@app.route("/<int:id>")
def index(id=0):
    return render_template('images.html', i=id)

@app.route('/gallery')
def image_gall():
    hists = os.listdir('static/img')
    hists = ['img/' + file for file in hists]
    return render_template('gallery.html', hists = hists)

@app.route('/uploader', methods = ['GET', 'POST'])
def upload_file():
   if request.method == 'POST':
      f = request.files['file']
      path, dirs, files = next(app.config['UPLOAD_FOLDER'])
      file_count = len(files)
      file_count = file_count+1
    #   _, ext = os.path.splitext(f.filename)
    #   f.filename = str(file_count)+'.jpg'
      filename = secure_filename(f.filename)
      f.save(os.path.join(app.config['UPLOAD_FOLDER'],filename))
      
      hists = os.listdir('static/img')
      hists = ['img/' + file for file in hists]
      flash('Image uploaded successfully')
      return render_template('images.html', hists = hists)

@app.route('/add', methods=['POST'])
def add_blob():
    g.db.execute('INSERT INTO annotations (image, x, y, width, height, label) VALUES (?, ?, ?,?,?,?)',
                 [request.form['image'], request.form['x'], request.form['y'], request.form['width'],
                  request.form['height'], request.form['label']])
    g.db.commit()
    return jsonify(success=True)

@app.route('/')
@app.route('/query_blob/<int:id>', methods=['POST'])
def query_blob(id):
    blob = numpy.ndarray("static\\img\\%d.jpg" % id).crop(int(request.form['x']), int(request.form['y']),
                                                  int(request.form['width']), int(request.form['height']))

    return jsonify(prediction='')


@app.route('/line_blobs/<int:id>', methods=['GET'])
def line_blobs(id):
    cur = g.db.execute('SELECT id, x, y, width, height FROM blobs WHERE image=?', [id])
    blobs = cur.fetchall()
    entries = []
    img = numpy.ndaaray("static\\img\\%d.jpg" % id)
    for i, entry in enumerate(blobs):
        blob = img.crop(entry[1], entry[2], entry[3], entry[4])
        entries.append(dict(x=entry[1], y=entry[2], width=entry[3], height=entry[4]))
    return jsonify(blobs=entries)


@app.route('/blob/<int:id>', methods=['GET'])
def blob(id):
    cur = g.db.execute('SELECT id, image, x, y, width, height FROM annotations WHERE annotations.id=?', [id])
    line = cur.fetchone()

    img = numpy.ndaaray("static\\img\\%d.jpg" % int(line[1]))
    blob = img.crop(line[2], line[3], line[4], line[5])
    io = io.StringIO()
    blob.save(io)
    data = io.getvalue()
    resp = make_response(data)
    resp.content_type = "image/jpeg"
    return resp

@app.route('/blob/<int:id>', methods=['POST'])
def change_blob(id):
    g.db.execute('UPDATE annotations SET label = ? WHERE id = ?', [request.form['label'], id])
    g.db.commit()
    return jsonify(success=True)

@app.route('/blob/<int:id>', methods=['DELETE'])
def delete_blob(id):
    g.db.execute('DELETE FROM annotations WHERE id = ?', [id])
    g.db.commit()
    return jsonify(success=True)

@app.route('/admin')
@app.route('/admin/<int:page>')
def admin(page=0):
    cur = g.db.execute('SELECT annotations.id, annotations.label FROM annotations LIMIT ?, 100', [page*100])
    blobs = cur.fetchall()
    return render_template('admin.html', annotations=blobs, page=page)

if __name__ == "__main__":
    app.run(host='0.0.0.0',debug = True)