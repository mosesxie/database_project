
from hashlib import sha1
from flask import Flask, render_template, request, session, url_for, redirect
import time
import pymysql.cursors

# start flask stuff
app = Flask(__name__)

conn = pymysql.connect(host='localhost',
					   port=3306,
                       user='root',
                       passwd='',
                       db='pricosha',
                       charset='utf8mb4',
                       cursorclass=pymysql.cursors.DictCursor)
	

@app.route('/')
def hello():
	return render_template('index.html')


#password

@app.route('/password')
def password():
	return render_template('password.html')

@app.route('/login')
def login():
	return render_template("login.html")

@app.route('/profile')
def backProfile():
	return render_template('index.html', message=not None)

@app.route('/logout')
def logout():
	session['username'] = ''
	return render_template('index.html')


@app.route('/loginAuth', methods = ['GET', 'POST'])
def loginAuth():
	pw = request.form['password']
	user = request.form['username']
	cursor = conn.cursor()

	query1 = 'SELECT * FROM Person WHERE username = %s AND password = %s'
	cursor.execute(query1, (user, sha1(pw).hexdigest()))

	output = cursor.fetchone()

	cursor.close()
	error_message = None
	if(output):
		session['username'] = user
		return render_template('index.html',message= not None)
	else:
		error = 'Not the correct login info'
		return render_template('login.html', error=error_message)

@app.route('/register')
def register():
	return render_template('register.html')



@app.route('/registerAuth', methods=['GET', 'POST'])
def registerAuth():

	user = request.form['new_username']
	pw = request.form['new_password']
	first_name = request.form['fname']
	last_name = request.form['lname']


	cursor = conn.cursor()

	query1 = 'SELECT * FROM Person WHERE username = %s'
	cursor.execute(query1, (user))

	output = cursor.fetchone()

	error_message = None
	message=not None

	if(output):

		error_message = 'There is already a user with that info'
		return render_template('register.html', error = error_message)



	else:
		ins = 'INSERT INTO Person VALUES(%s, %s, %s, %s)'
		cursor.execute(ins, (user, sha1(pw).hexdigest(), first_name, last_name))
		conn.commit()
		cursor.close()
		return render_template('index.html', message=message)


@app.route('/home')
def home():
	user = session['username']
	cursor = conn.cursor();
	query1 = 'SELECT id, username, content_name, file_path, timest\
	FROM content WHERE username = %s || public = %s || id in \
	(SELECT id FROM Share, Member WHERE Share.group_name = Member.group_name  && Member.username = %s) ORDER BY timest DESC'
	cursor.execute(query1, (user, True, user))

	query2 = 'SELECT timest, content_name, file_path, likes FROM Content WHERE username = %s && public = 1 ORDER BY timest DESC'


	cursor.execute(query2, (user))
	output = cursor.fetchall()


	cursor.close()
	return render_template('home.html', username=user, posts=output)

@app.route('/post', methods=['GET', 'POST'])
def post():


	user = session['username']
	cursor = conn.cursor();
	path = request.form['image_path']
	content_name = request.form['content_name']
	is_public=request.form['optradio']
	likes=0
	query = 'INSERT INTO Content(username, file_path, content_name, public,likes) VALUES(%s, %s, %s, %s,%s)'
	cursor.execute(query, (user, path, content_name, is_public,likes))
	conn.commit()
	cursor.close()
	return redirect(url_for('home'))


@app.route('/likes')
def likes(content_name):
	user = session['username']
	cursor = conn.cursor();
	query1 = 'SELECT likes FROM content WHERE username = %s'
	cursor.execute(query1, (user))
	output = cursor.fetchall()
	query2 = 'UPDATE content SET likes = likes+1 WHERE username = %s'
	cursor.execute(query2, (output,user))
	cursor.close()
	return redirect(url_for('home'))

@app.route('/friends')
def friends():
	user = session['username']
	cursor = conn.cursor();
	query1 = 'SELECT DISTINCT group_name, username_creator FROM member WHERE username = %s OR username_creator = %s'
	cursor.execute(query1, (user,user))
	output = cursor.fetchall()
	cursor.close()
	return render_template('friends.html', username=user, groups=output)


@app.route('/tagandshare')
def tagandshare():
	user=session['username']
	cursor = conn.cursor();
	query2 = 'SELECT timest, content_name, file_path FROM Content WHERE username = %s ORDER BY timest DESC'
	cursor.execute(query2, (user))
	output1 = cursor.fetchall()
	query = 'SELECT group_name FROM member WHERE username = %s'
	cursor.execute(query, (user))
	output2 = cursor.fetchall()
	cursor.close()
	return render_template('tagandshare.html', username=user, posts=output1, groups=output2,sel=1)







@app.route('/addFriendGroup', methods=['GET','POST'])
def addFriendGroup():
	user = session['username']
	cursor = conn.cursor();
	friend_group_name = request.form['groupName']
	m_first_name = request.form['memfname']
	m_last_name = request.form['memlname']
	
	queryFindMemUsername = "SELECT username FROM Person	WHERE first_name = %s AND last_name = %s"
	cursor.execute(queryFindMemUsername, (m_first_name, m_last_name))
	memUsername = cursor.fetchone().get('username')

	queryFG = "INSERT INTO FriendGroup (group_name, username) VALUES(%s, %s)"
	cursor.execute(queryFG, (friend_group_name, user))




	queryMeAsMem = "INSERT INTO Member (username, group_name, username_creator) VALUES(%s, %s, %s)"
	cursor.execute(queryMeAsMem, (user, friend_group_name, user))




	queryAddMember = "INSERT INTO Member (username, group_name, username_creator) VALUES(%s, %s, %s)"
	cursor.execute(queryAddMember, (memUsername, friend_group_name, user))
	conn.commit()
	cursor.close()
	return redirect(url_for('friends'))


@app.route('/forgotPassword', methods=['GET','POST'])
def forgotPassword():

	user = request.form['username']
	new_password = request.form['password1']
	confirm_password = request.form['password2']

	cursor = conn.cursor()

	query1 = 'SELECT * FROM Person WHERE username=%s'
	cursor.execute(query1, (user))
	data = cursor.fetchone()
	cursor.close()

	error_message = None
	message = not None

	if new_password != confirm_password:
		error_message = 'Thoses entries dont match'
		return render_template('password.html', error=error_message)
	else:
		newpass_hex = sha1(new_password).hexdigest()
		confirmpass_hex = sha1(confirm_password).hexdigest()

		cursor = conn.cursor()
		update = 'UPDATE Person SET password = %s WHERE username = %s'
		cursor.execute(update, (newpass_hex, user))
		conn.commit()

		query = 'SELECT * FROM person WHERE username = %s AND password = %s'
		cursor.execute(query, (user, new_password))

		new_data = cursor.fetchone()
		print(new_data)
		message = "its been changed"
		cursor.close()
		return render_template('index.html')

app.static_folder = 'static'
app.secret_key = 'this is the key'
#Run the app on local host port 5000
if __name__=='__main__':
	app.run('127.0.0.1',5000,debug=True)

