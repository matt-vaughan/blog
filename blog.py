#!/bin/usr/python
from flask import Flask, render_template, session, request, Response
#from flask_cors import CORS
from blogdb import BlogDB
import json

app = Flask(__name__)
#CORS(app)
blogdb = BlogDB()

@app.route("/.blog", methods=['GET', 'POST'])
def home():
    return render_template('blog.html', content="landed")

@app.route("/register.blog", methods=['GET', 'POST'])
def register():
    return render_template('register.html')

@app.route("/login.blog", methods=['GET', 'POST'])
def login():
    return render_template('login.html')

@app.route("/post.blog", methods=['GET', 'POST'])
def post():
    return render_template('post.html')

@app.route("/view-posts.blog", methods=['GET', 'POST'])
def view_posts():
    return render_template('blog.html', content="Posts", posts=blogdb.posts())

"""
Form targets
"""
@app.route("/register-action.blog", methods=['POST'])
def register_action():    
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    phone = request.form.get('phone')
    email = request.form.get('email')
    print(f"Ok here is {first_name} {last_name}")

    password = request.form.get('password')
    if password != request.form.get('confirm_password'):
        return render_template('blog.html', content="password must match confirm password")
    
    blogdb.create_user(first_name, last_name, email, phone, password)
    return render_template('blog.html', content=f"created user with phone {phone}")

@app.route("/post-action.blog", methods=['POST'])
def post_action():
    if not session['token']:
        return render_template('blog.html', content="You are not logged in and, therefor, cannot post")
    else:
        post = request.form.get('post')
        # TODO validate post
        blogdb.create_post(session['phone'], session['token'], post)
        return render_template('blog.html', content="Post made")

@app.route("/login-action.blog", methods=['POST'])
def login_action():
    # TODO validate phone and password
    phone = request.form.get('phone')
    password = request.form.get('password')
    
    token = blogdb.login_with_phone(phone, password)
    if token == None:
        return render_template('blog.html', content="Couldn't login")
    else:
        session['token'] = token
        session['phone'] = phone

    return render_template('blog.html', content=f"logged in as {session['phone']}")

if __name__ == "__main__":
    app.run()