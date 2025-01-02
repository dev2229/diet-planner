import numpy as np
import pandas as pd
from pulp import *
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import pickle

sampleData = pd.read_csv('https://raw.githubusercontent.com/imperixxl/hackjmi-2024/main/nutritionalValues.csv').drop(
    columns='VegNovVeg', axis=1)

optcols = ['Food_items', 'Calories', 'Fats', 'Proteins', 'Carbohydrates']
opt = sampleData[optcols]
# converting fats, proteins and carbs columns to float-type
flt = ['Fats', 'Proteins', 'Carbohydrates']
opt[flt].astype(float)

days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

# now, we split the data randomly into 8 equal parts
splitValuesDays = np.linspace(0, len(opt), 8).astype(int)

# we divided the data into 8 equal parts, because the dataset may/may not be divisible by 7
# so the following will make sure any data point is not missed
splitValuesDays[-1] = splitValuesDays[-1] - 1


# Now we randomise the food into the days, lets define a function
def randomisedDays():
    fracValues = opt.sample(frac=1).reset_index().drop('index', axis=1)
    dayData = []  # an empty list to be appended with the data of a specific day
    for z in range(len(splitValuesDays) - 1):
        dayData.append(fracValues.loc[splitValuesDays[z]:splitValuesDays[
            z + 1]])  # this slices splitValuesDays, and loc is a function to access rows
    return dict(zip(days, dayData))


meals = ['Breakfast', 'Snack 1', 'Lunch', 'Snack 2', 'Dinner']
splitValuesMeal = np.linspace(0, splitValuesDays[1], len(meals) + 1).astype(int)
splitValuesMeal[-1] = splitValuesMeal[-1] - 1

import random


def randomisedMeals(dayData):
    mealsData = {}
    for meal in meals:
        fracValues = dayData.sample(frac=1).reset_index(drop=True)
        mealData = fracValues.sample(frac=random.uniform(0.5, 1.0)).reset_index(drop=True)
        mealsData[meal] = mealData
    return mealsData


def nutritional_calories(weight, cals):
    pr_cals = weight * 4  # it is assumed that 1 gram of protein gives approx 4 calories
    carb_cals = cals / 2
    fat_cals = cals - (pr_cals + carb_cals)
    finalcals = {"Protein calories": pr_cals, "Carbohydrate calories": carb_cals, "Fat calories": fat_cals}
    return finalcals


def nutritional_grams(calsdict):
    pr_grams = calsdict['Protein calories'] / 4  # approx 4 calories per gram of proteins
    carb_grams = calsdict['Carbohydrate calories'] / 4  # approx 4 calories per gram of carbohydrates
    fat_grams = calsdict['Fat calories'] / 9  # approx 9 calories per gram of fats
    finalgrams = {"Protein grams": pr_grams, "Carbohydrate grams": carb_grams, "Fat grams": fat_grams}
    return finalgrams


daysData = randomisedDays()


def dietModel(constr, day, weight, cals, food, data):
    gms = nutritional_grams(nutritional_calories(weight, cals))  # dictionary for grams required for intake
    P = gms['Protein grams']
    F = gms['Fat grams']
    B = gms['Carbohydrate grams']
    dayData = daysData[day]
    dayData = dayData[dayData.Calories != 0]  # removes any rows that have calories=0

    meal = dayData.Food_items.tolist()  # converts the food_items column to list
    c = dayData.Calories.tolist()  # converts the calories column to list
    np.random.shuffle(meal)

    x = pulp.LpVariable.dicts("x", indices=meal, lowBound=0, upBound=1.5, cat='Continuous', indexStart=[])

    p = dayData.Proteins.tolist()
    f = dayData.Fats.tolist()
    b = dayData.Carbohydrates.tolist()

    # using PuLP to optimize
    constr = pulp.LpProblem("DietCalculator", LpMinimize)  # creates a new Linear Programming Problem (LPP)
    # objective function:
    constr += pulp.lpSum([x[meal[i]] * c[i] for i in
                          range(len(meal))])  # lpSum adds everything (Σ) and for loop iterates over each food_item
    # constraints:
    splitMeal = {'Snack 1': 0.10, 'Snack 2': 0.10, 'Breakfast': 0.15, 'Lunch': 0.35, 'Dinner': 0.30}
    divMeal = splitMeal[food]
    constr += pulp.lpSum([x[meal[i]] * p[i] for i in range(len(x))]) >= P * divMeal  # constraint for proteins
    constr += pulp.lpSum([x[meal[i]] * f[i] for i in range(len(x))]) >= F * divMeal  # constraint for fats
    constr += pulp.lpSum([x[meal[i]] * b[i] for i in range(len(x))]) >= B * divMeal  # constraint for carbohydrates
    # solving the problem using pulp's solving function
    constr.solve()

    # formatting the solution into a dataframe:
    vars, values = [], []
    for l in constr.variables():
        var = l.name  # name of decision variable
        val = l.varValue
        vars.append(var)
        values.append(val)
    values = np.array(values).round(2).astype(
        float)  # array for decision variables, upto 2 decimal places with type float
    # solution into df
    solution = pd.DataFrame(np.array([meal, values]).T, columns=['Food Items', 'Quantity'])  # making df using pandas
    solution['Quantity'] = solution.Quantity.astype(float)
    solution = solution[solution['Quantity'] != 0]  # eliminating any items with quantity=0
    solution.Quantity *= 100  # converting into grams
    solution = solution.rename(columns={'Quantity': 'Quantity (grams)'})
    return solution


# For the final model implementation
def baseModel(weight, cals):
    result = []
    for day in days:
        constr = pulp.LpProblem("DietCalculator", LpMinimize)
        print(f'Building a model for {day}')
        result.append(dietModel(constr, day, weight, cals))
    return dict(zip(days, result))


# final model that runs dietModel and baseModel respectively
def finalModel(weight, cals):
    res_model = []
    for day in days:
        dayData = daysData[day]
        mealsData = randomisedMeals(dayData)
        mealModel = {}
        for meal in meals:
            constr = pulp.LpProblem("DietCalculator", LpMinimize)
            solModel = dietModel(constr, day, weight, cals, meal, mealsData)

            mealModel[meal] = solModel
        res_model.append(mealModel)
    return dict(zip(days, res_model))


def execModel(diet, selected_days):
    ufo = []
    for day in selected_days:
        ufo.append({"day": day})
        print(f"\033[1m{day}\033[0m")  # Bold day
        print("\n")  # Add two new lines after printing the day
        meal_labels = []
        for meal in meals:
            meal_data = diet[day][meal]
            if not meal_data.empty:
                ufo.append({"meal": meal})
                if meal not in meal_labels:
                    print(f"\033[4m\033[3m{meal}\033[0m")  # Underline and italicize meal name
                    meal_labels.append(meal)
                # Format the meal data as a dictionary
                meal_data_formatted = meal_data[['Food Items', 'Quantity (grams)']].copy()
                meal_data_dict = meal_data_formatted.set_index('Food Items').T.to_dict('list')

                # Print the meal data
                for food_item, quantity in meal_data_dict.items():
                    ufo.append({food_item: f"{round(quantity[0],1)} grams"})
                print("---------------------------------")
        print("________________________________________________________________________________________________________________")
    return ufo

