from flask import Blueprint, render_template, request, redirect, url_for, session
import pandas as pd
from database.database import *
import json
from Model import execModel, finalModel, nutritional_calories

dashboard_blueprint = Blueprint('dashboard', __name__)


@dashboard_blueprint.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    if request.method == 'POST':
        calories = int(request.form['calories'])
        gender = request.form['gender']
        selected_days = request.form.getlist('days')
        weight = int(request.form['weight'])
        height = int(request.form['height'])

        height_m = height / 100

        # Calculate BMI
        bmi = weight / (height_m ** 2)

        print(selected_days)
        diet = finalModel(weight, calories)

        output = execModel(diet, selected_days)
        session['result'] = output
        return redirect(url_for('dashboard.result', bmi=bmi, height=height, weight=weight, gender=gender, calories = calories))

    return render_template('dashboard.html', days_of_week=days_of_week)

@dashboard_blueprint.route('/bmicalcultor', methods=['GET', 'POST'])
def bmicalculate():
    if request.method == 'POST':
        gender = request.form['gender']
        weight = int(request.form['weight'])
        height = int(request.form['height'])

        height_m = height / 100

        # Calculate BMI
        bmi = round((weight / (height_m ** 2)), 2)
        

    return render_template('bmiresult.html', bmi = bmi, height=height, weight=weight, gender = gender)

@dashboard_blueprint.route('/result')
def result():
    height = request.args.get('height')
    weight = float(request.args.get('weight'))
    gender = request.args.get('gender')
    calories = float(request.args.get('calories'))
    print(f'calories : {calories}')
    bmi = round(float(request.args.get('bmi')), 2)
    result_of_values = session.get('result', [])

    daily_carbs = nutritional_calories(weight, calories)
    print(daily_carbs)

    return render_template('result.html', output=result_of_values, height=height, weight=weight, gender=gender, bmi=bmi, daily_carbs = daily_carbs)
