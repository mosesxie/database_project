
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

@app.route('/password')
def password():
	return render_template('password.html')

@app.route('/login')
def login():
	return render_template("login.html")


@app.route('/loginAuth', methods = ['GET', 'POST'])
def loginAuth():
	pw = request.form['password']
	user = request.form['username']
	cursor = conn.cursor()

	query1 = 'SELECT * FROM Person WHERE username = %s AND password = %s'
	cursor.execute(query1, (user, sha1(pw).hexdigest()))

	output = cursor.fetchone()

	cursor.close()
	error = None
	if(output):
		session['username'] = user
		return render_template('index.html',message= not None)
	else:
		error = 'Not the correct login info'
		return render_template('login.html', error=error)

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

	error = None
	message=not None

	if(output):

		error = 'There is already a user with that info'
		return render_template('register.html', error = error)
	else:
		ins = 'INSERT INTO Person VALUES(%s, %s, %s, %s)'
		cursor.execute(ins, (user, sha1(pw).hexdigest(), first_name, last_name))
		conn.commit()
		cursor.close()
		return render_template('index.html', message=message)


@app.route('/home')
def home():
	username = session['username']
	cursor = conn.cursor();
	query1 = 'SELECT id, username, content_name, file_path, timest\
	FROM content WHERE username = %s || public = %s || id in \
	(SELECT id FROM Share, Member WHERE Share.group_name = Member.group_name  && Member.username = %s) ORDER BY timest DESC'
	cursor.execute(query1, (username, True, username))

	query2 = 'SELECT timest, content_name, file_path, likes FROM Content WHERE username = %s && public = 1 ORDER BY timest DESC'
	cursor.execute(query2, (username))
	data = cursor.fetchall()
	cursor.close()
	return render_template('home.html', username=username, posts=data)

@app.route('/post', methods=['GET', 'POST'])
def post():
	username = session['username']
	cursor = conn.cursor();
	file_path = request.form['image_path']
	content_name = request.form['content_name']
	public=request.form['optradio']
	likes=0
	query = 'INSERT INTO Content(username, file_path, content_name, public,likes) VALUES(%s, %s, %s, %s,%s)'
	cursor.execute(query, (username, file_path, content_name, public,likes))
	conn.commit()
	cursor.close()
	return redirect(url_for('home'))


@app.route('/likes')
def likes(content_name):
	username = session['username']
	cursor = conn.cursor();
	query = 'SELECT likes FROM content WHERE username = %s'
	cursor.execute(query, (username))
	data = cursor.fetchall()
	query2 = 'UPDATE content SET likes = likes+1 WHERE username = %s'
	cursor.execute(query2, (data,username))
	cursor.close()
	return redirect(url_for('home'))

@app.route('/friends')
def friends():
	username = session['username']
	cursor = conn.cursor();
	query = 'SELECT DISTINCT group_name, username_creator FROM member WHERE username = %s OR username_creator = %s'
	cursor.execute(query, (username,username))
	data = cursor.fetchall()
	cursor.close()
	return render_template('friends.html', username=username, groups=data)


@app.route('/tagandshare')
def tagandshare():
	username=session['username']
	cursor = conn.cursor();
	query2 = 'SELECT timest, content_name, file_path FROM Content WHERE username = %s ORDER BY timest DESC'
	cursor.execute(query2, (username))
	data1 = cursor.fetchall()
	query = 'SELECT group_name FROM member WHERE username = %s'
	cursor.execute(query, (username))
	data2 = cursor.fetchall()
	cursor.close()
	return render_template('tagandshare.html', username=username, posts=data1, groups=data2,sel=1)



@app.route('/addFriendGroup', methods=['GET','POST'])
def addFriendGroup():
	username = session['username']
	cursor = conn.cursor();
	friendGroupName = request.form['groupName']
	mFirstName = request.form['memfname']
	mLastName = request.form['memlname']
	
	queryFindMemUsername = "SELECT username FROM Person	WHERE first_name = %s AND last_name = %s"
	cursor.execute(queryFindMemUsername, (mFirstName, mLastName))
	memUsername = cursor.fetchone().get('username')
	 
	#create freind group only after we have ensured that 
	#person we want to create the group with exists 
	queryFG = "INSERT INTO FriendGroup (group_name, username) VALUES(%s, %s)"
	cursor.execute(queryFG, (friendGroupName, username))
	#add yourself as member

	queryMeAsMem = "INSERT INTO Member (username, group_name, username_creator) VALUES(%s, %s, %s)"
	cursor.execute(queryMeAsMem, (username, friendGroupName, username))
	#add other person as member
	queryAddMember = "INSERT INTO Member (username, group_name, username_creator) VALUES(%s, %s, %s)"
	cursor.execute(queryAddMember, (memUsername, friendGroupName, username))
	conn.commit()
	cursor.close()
	return redirect(url_for('friends'))

@app.route('/profile')
def backProfile():
	return render_template('index.html', message=not None)

@app.route('/logout')
def logout():
	session['username'] = ''
	return render_template('index.html')

@app.route('/forgotPassword', methods=['GET','POST'])
def forgotPassword():
	#grab infor from the reset password form
	username = request.form['username']
	newpass = request.form['password1']
	confirmpass = request.form['password2']

	cursor = conn.cursor()

	query = 'SELECT * FROM Person WHERE username=%s'
	cursor.execute(query, (username))
	data = cursor.fetchone()
	cursor.close()

	error = None
	message = not None

	if newpass != confirmpass:
		error = 'The passwords do not match'
		return render_template('password.html', error=error)
	else:
		newpass_hex = sha1(newpass).hexdigest()
		confirmpass_hex = sha1(confirmpass).hexdigest()

		cursor = conn.cursor()
		update = 'UPDATE Person SET password = %s WHERE username = %s'
		cursor.execute(update, (newpass_hex, username))
		conn.commit()

		query = 'SELECT * FROM person WHERE username = %s AND password = %s'
		cursor.execute(query, (username, newpass))

		new_data = cursor.fetchone()
		print(new_data)
		message = "Password successfully changed, you are logged back in!"
		cursor.close()
		return render_template('index.html')

app.static_folder = 'static'
app.secret_key = 'secret key 123'
#Run the app on local host port 5000
if __name__=='__main__':
	app.run('127.0.0.1',5000,debug=True)

