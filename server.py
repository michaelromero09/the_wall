from flask import Flask, request, redirect, render_template, session, flash
from mysqlconnection import MySQLConnector
import md5, re
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')

app = Flask(__name__)
app.secret_key = 'pepperBreath'
mysql = MySQLConnector(app, 'wall_db')

@app.route('/')
def index():
  return render_template('index.html')

@app.route('/register', methods=['POST'])
def submit():
  if len(request.form['first_name']) < 2:
    flash("Please enter first name.")
    return redirect('/')
  if len(request.form['last_name']) <2:
    flash("Please enter last name.")
    return redirect('/')
  if len(request.form['email']) <1:
    flash("Please enter email.")
  elif not EMAIL_REGEX.match(request.form['email']):
    flash("I said please enter valid email!")
    return redirect('/')
  if len(request.form['password']) < 8:
    flash("Password must be at least 8 characters.")
    return redirect('/')
  if (request.form['confirm_password']) != (request.form['password']):
    flash("Password and confirmed password do not match up, please try again.")
    return redirect('/')
  else:
    hashed_password = md5.new(request.form['password']).hexdigest()
    query = 'INSERT INTO users (first_name, last_name, email, password, created_at, updated_at) VALUES (:first_name, :last_name, :email, :password, NOW(), NOW())'
    data = {
      'first_name': request.form['first_name'],
      'last_name': request.form['last_name'],
      'email': request.form['email'],
      'password': hashed_password
    }
    mysql.query_db(query, data)
    db_id = mysql.query_db('SELECT id FROM users WHERE email = "' + request.form['email'] + '"')
    session['user_id'] = db_id[0].get('id')
    return redirect('/wall')

@app.route('/login', methods=['post'])
def login():
  form_email = request.form['email']
  db_email = mysql.query_db('SELECT email FROM users WHERE email = "' + form_email + '"')
  hashed_form_password = md5.new(request.form['password']).hexdigest()
  db_password = mysql.query_db('SELECT password FROM users WHERE email = "' + form_email + '"')
  db_id = mysql.query_db('SELECT id FROM users WHERE email = "' + form_email + '"')
  if db_email == []:
    flash('Email does not exist in our system')
    return redirect('/')
  if hashed_form_password != db_password[0].get('password'):
    flash('Invalid password')
    return redirect('/')
  if hashed_form_password == db_password[0].get('password'):
    session['user_id'] = db_id[0].get('id')
    return redirect('/wall')

@app.route('/wall')
def mainWall():
  def getRawComments(id):
    query = "SELECT content, first_name, last_name, comments.updated_at FROM comments JOIN users ON comments.user_id = users.id WHERE comments.post_id = " + str(id)
    print 'query:' + query + ' id:' + str(id)
    return mysql.query_db(query)

  def getName(first, last):
    return first + ' ' + last

  def getRawPosts():
    query = "SELECT content, first_name, last_name, posts.updated_at, posts.id AS id, users.id as user_id FROM posts JOIN users ON posts.users_id = users.id"
    return mysql.query_db(query)

  def getCleanPost(rawPost):
    return {
      'post': rawPost['content'],
      'name': getName(rawPost['first_name'], rawPost['last_name']),
      'date': rawPost['updated_at'],
      'post_id': rawPost['id'],
      'user_id': rawPost['user_id']
    }

  def getPosts():
    rawPosts = getRawPosts()
    posts = []

    for rawPost in rawPosts:
      post = getCleanPost(rawPost)
      post['comments'] = getRawComments(post['post_id'])
      posts.append(post)

    return posts

  return render_template('wall.html', posts = getPosts())

@app.route('/post_message', methods=['post'])
def post():
  request.form['post_content']
  query = 'INSERT INTO posts (users_id, content, created_at, updated_at) VALUES (:user_id, :content, NOW(), NOW())'
  data = {
    'user_id': session['user_id'],
    'content': request.form['post_content']
  }
  mysql.query_db(query, data)
  return redirect('/wall')

@app.route('/post_comment', methods=['post'])
def post_comment():
  request.form['comment_content']
  query = 'INSERT INTO comments (user_id, post_id, content, created_at, updated_at) VALUES (:user_id, :post_id, :com_content, NOW(), NOW())'
  data = {
    'user_id': session['user_id'],
    'post_id': request.form['post_id'],
    'com_content': request.form['comment_content']
  }
  mysql.query_db(query, data)
  return redirect('/wall')

@app.route('/logout', methods=['post'])
def logout():
  session.clear()
  return redirect('/')

@app.route('/delete_post', methods=['post'])
def delete_post():
  query = 'DELETE * FROM posts WHERE post_id = ' #+ str(post['post_id'])
  print 'CHUBSYWUBSY' + request.form['post_id'] 
  return redirect('/wall')

app.run(debug = True)

