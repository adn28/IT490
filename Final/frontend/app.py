from flask import Flask, render_template, request, session
from werkzeug.security import check_password_hash, generate_password_hash
import pika
import os

app = Flask(__name__)
app.secret_key = os.environ['FLASK_SECRET_KEY'] 

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        msg = messaging.Messaging()
        msg.send('GETHASH', { 'username': username })
        response = msg.receive()
        if response['success'] != True:
            return "Login failed."
        if check_password_hash(response['hash'], password):
            session['username'] = username
            return redirect('/')
        else:
            return "Login failed."
    return render_template('login.html')

@app.route('/register')
def register():
    if request.method =='POST':
       firstname = request.form['firstname']
       lastname = request.form['lastname']
       email = request.form['email']
       username = request.form['username']
       password = request.form['password']
       confirmpassword = request.form['confirmpassword']
       if password == confirmpassword:
          msg = messaging.Messaging()
          msg.send(
              'REGISTER',
              {
                   'firstname' : firstname,
                   'lastname' : lastname,
                   'email': email,
                   'username' : username,
                   'hash': generate_password_hash(password)
               }
            )
          response = msg.receive()
          if response['success']:
              session['username'] = username
              return redirect('/')
          else:
              return f"{response['message']}"

    return render_template('register.html')

@app.route('/logout')
def logout():
   session.pop('username', None)
   return redirect('/')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
