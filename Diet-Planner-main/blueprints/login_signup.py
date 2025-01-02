from flask import Blueprint, render_template, request, redirect, url_for, session
from database.database import *

login_blueprint = Blueprint('login', __name__)

@login_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = get_user(email)

        if verify_password(user, password):
            # Store user in the session
            session['user'] = email
            return redirect(url_for('dashboard.dashboard'))
        else:
            return 'Invalid username or password.'
    return render_template('login.html')

@login_blueprint.route('/signup')
def signup():
    return render_template('signup.html')

def count_digits(number):
    # Convert the number to a string and calculate its length
    return len(str(abs(number)))

@login_blueprint.route('/signup-form', methods=['GET', 'POST'])
def signup_form():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm-password']
        username = request.form['name']
        phone = int(request.form['mobile'])

        if count_digits(phone) <10:
            return "please enter correct phone number"
        if password != confirm_password:
            return 'Password and Confirm Password do not match.'

        existing_user = get_user(email)
        if existing_user:
            return 'Email address is already registered.'

        # Create a new user
        insert_user(username = username, mobile=phone,email= email, password= password)

        # Redirect to login page after successful signup
        return redirect(url_for('login.login'))

    return render_template('signup-form.html')
