#!/bin/usr/python
from flask import Flask, render_template, session, request, Response
#from flask_cors import CORS
from blogdb import BlogDB
import json

app = Flask(__name__)
app.secret_key = "TODO: Get this from a file outside what's available on the server"
#CORS(app)
blogdb = BlogDB()

@app.route("/", methods=['GET', 'POST'])
def home():
    if not session['token'] or not session['phone']:
        return render_template('login.html')
    else:
        return render_template('blog.html', content="Posts", posts=blogdb.posts())
        
@app.route("/register", methods=['GET', 'POST'])
def register():
    return render_template('register.html')

"""
Form targets
"""
@app.route("/register-action", methods=['POST'])
def register_action():    
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    phone = request.form.get('phone')
    email = request.form.get('email')

    password = request.form.get('password')
    if password != request.form.get('confirm_password'):
        return render_template('blog.html', content="password must match confirm password")
    
    blogdb.create_user(first_name, last_name, email, phone, password)
    return render_template('blog.html', content=f"created user with phone {phone}")

@app.route("/post-action", methods=['POST'])
def post_action():
    if not session['token'] or not session['phone']:
        return render_template('blog.html', content="You are not logged in and, therefor, cannot post")
    else:
        post = request.form.get('post')
        blogdb.create_post(session['phone'], session['token'], post)
        return render_template('blog.html', content="Post made")

@app.route("/login-action", methods=['POST'])
def login_action():
    phone = request.form.get('phone')
    password = request.form.get('password')

    if not phone or not password:
        return render_template('blog.html', content="Phone number or password invalid")

    token = blogdb.login_with_phone(phone, password)
    if not token:
        return render_template('blog.html', content="Couldn't login")
    else:
        session['token'] = token
        session['phone'] = phone

    return render_template('blog.html', content=f"logged in as {session['phone']}")

if __name__ == "__main__":
    app.run()
