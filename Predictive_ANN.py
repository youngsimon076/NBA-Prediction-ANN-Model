# -*- coding: utf-8 -*-
"""Final Culminating Product

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1UkIVNmgosguv4AKvgsk0KWMdhvO14rkW
"""

pip install sklearn.externals

import requests
from bs4 import BeautifulSoup
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, GridSearchCV
from imblearn.over_sampling import SMOTE

# scrapes team data from the br url
def scrape_team_data(url):
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    table = soup.find('table', {'id': 'ratings'})
    team_data = pd.read_html(str(table))[0]
    team_data.columns = team_data.columns.droplevel()
    team_data = team_data[['Team', 'W', 'L', 'ORtg', 'DRtg']]
    team_data.set_index('Team', inplace=True)
    return team_data

# scrapes game data from the br url
def scrape_game_data(url):
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    table = soup.find('table', {'id': 'schedule'})
    game_data = pd.read_html(str(table))[0]
    return game_data

# preprocesses the game data
def preprocess_game_data(game_data, team_data):
    game_data = game_data[['Visitor/Neutral', 'Home/Neutral', 'PTS', 'PTS.1']]
    game_data.columns = ['Visitor', 'Home', 'Visitor_PTS', 'Home_PTS']

    # combine data types
    game_data = game_data.merge(team_data, how='left', left_on='Visitor', right_index=True)
    game_data = game_data.merge(team_data, how='left', left_on='Home', right_index=True, suffixes=('_visitor', '_home'))

    # bonus features
    game_data['Win_Streak_visitor'] = game_data['W_visitor'].rolling(window=5, min_periods=1).sum()
    game_data['Win_Streak_home'] = game_data['W_home'].rolling(window=5, min_periods=1).sum()
    game_data['Home_Win_Ratio'] = game_data['W_home'] / (game_data['W_home'] + game_data['L_home'])
    game_data['Visitor_Win_Ratio'] = game_data['W_visitor'] / (game_data['W_visitor'] + game_data['L_visitor'])

    return game_data

# call function to scrape team data
team_url = "https://www.basketball-reference.com/leagues/NBA_2024_ratings.html"
team_data = scrape_team_data(team_url)

# call function to scrape game data
january_url = "https://www.basketball-reference.com/leagues/NBA_2024_games-january.html"
february_url = "https://www.basketball-reference.com/leagues/NBA_2024_games-february.html"
march_url = "https://www.basketball-reference.com/leagues/NBA_2024_games-march.html"
april_url = "https://www.basketball-reference.com/leagues/NBA_2024_games-april.html"

january_games = scrape_game_data(january_url)
february_games = scrape_game_data(february_url)
march_games = scrape_game_data(march_url)
april_games = scrape_game_data(april_url)

# call function to preprocess game data
january_data = preprocess_game_data(january_games, team_data)
february_data = preprocess_game_data(february_games, team_data)
march_data = preprocess_game_data(march_games, team_data)
april_data = preprocess_game_data(april_games, team_data)

# combine jan/feb data
training_data = pd.concat([january_data, february_data])

# define features(what the model uses to predict) and target(what model predicts)
X_train = training_data[['W_visitor', 'L_visitor', 'ORtg_visitor', 'DRtg_visitor', 'W_home', 'L_home', 'ORtg_home', 'DRtg_home',
                         'Win_Streak_visitor', 'Win_Streak_home', 'Home_Win_Ratio', 'Visitor_Win_Ratio']]
y_train = (training_data['Visitor_PTS'] < training_data['Home_PTS']).astype(int)

# oversample using smote(makes data more balanced)
smote = SMOTE(random_state=42)
X_train_resampled, y_train_resampled = smote.fit_resample(X_train, y_train)

# rcf(creates/trains model)
rf_classifier = RandomForestClassifier(random_state=42)

# makes grid for hyperparameter tuning
param_grid = {
    'n_estimators': [100, 200, 300],
    'max_depth': [10, 20, 30],
    'min_samples_split': [2, 5, 10],
    'min_samples_leaf': [1, 2, 4]
}

# uses the grid to hyperparameter tune, helps accuracy by finding the optimal parameters
grid_search = GridSearchCV(rf_classifier, param_grid, cv=5, scoring='accuracy')
grid_search.fit(X_train_resampled, y_train_resampled)

# takes the model with the best accuracy from hyperparameter tuning
best_rf_classifier = grid_search.best_estimator_

# displays the accuracy of said model
best_rf_accuracy = grid_search.best_score_

print("Best Random Forest Model Accuracy:", best_rf_accuracy)

# predict upcoming games
predictions = best_rf_classifier.predict(X_predictions)

# function to print new predictions
def print_predictions(game_data, predictions, start_idx, end_idx):
    print(f"Predictions for rows {start_idx} to {end_idx}:")
    for i in range(start_idx, end_idx):
        row = game_data.iloc[i]
        print(f"{row['Visitor/Neutral']} at {row['Home/Neutral']}: {'Visitor' if predictions[i] == 1 else 'Home'} wins")

# lets you input the rows from https://www.basketball-reference.com/leagues/NBA_2024_games-march.html to print, so input start and end rows
def get_input_range(max_rows):
    start_idx = int(input(f"Enter the start index (0 to {max_rows - 1}): "))
    end_idx = int(input(f"Enter the end index ({start_idx} to {max_rows - 1}): "))
    return start_idx, end_idx

# prints selected rows for march
march_start, march_end = get_input_range(len(march_games))
print_predictions(march_games, predictions[:len(march_games)], march_start, march_end)

# prints selected rows for april
april_start, april_end = get_input_range(len(april_games))
print_predictions(april_games, predictions[len(march_games):], april_start, april_end)
