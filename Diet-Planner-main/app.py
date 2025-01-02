from flask import Flask, render_template

from blueprints.dashboard import dashboard_blueprint
from blueprints.login_signup import login_blueprint

app = Flask(__name__)

app.config['SECRET_KEY'] = 'your_secret_key'

app.register_blueprint(login_blueprint)
app.register_blueprint(dashboard_blueprint)


@app.route('/')
def hello():
    return render_template('index.html')


@app.route('/bmicalculator')
def dashboard():
    return render_template('bmicalculator.html')

@app.route('/resources')
def resources():
    return render_template('resources.html')

@app.route('/balanceddiet')
def balancedDiet():
    return render_template('result.html')

if __name__ == '__main__':
    app.run(debug=True)
