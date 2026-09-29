#A more barebones version of my PreMatch-CS-AI script

from sklearn.tree import DecisionTreeClassifier, plot_tree, export_text
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.ensemble import HistGradientBoostingClassifier, AdaBoostClassifier
from sklearn.dummy import DummyClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import requests
import io
import json

#Shut up about the 1,000 data conversion warnings
import warnings
from sklearn.exceptions import DataConversionWarning
warnings.filterwarnings(action='ignore', category=DataConversionWarning)

########################
### READ IN THE DATA ###
########################

#I could just... read from local files.

WEBSITE_URL = "https://hard-ware-website.vercel.app/datasets/xlsx/"

df = pd.read_excel(
                   io.BytesIO(
                    requests.get(WEBSITE_URL + "CSPreMatchStatistics.xlsx").content
                   ),
                   engine='openpyxl')

#load in the results of each match, and drop any NA results (for some reason.)
results = pd.read_excel(
                   io.BytesIO(
                    requests.get(WEBSITE_URL + "CounterStrike2.xlsx").content
                   ),
                   engine='openpyxl')[["ID", "Map", "StartSide", "Result"]].dropna(subset="Result")

#drop NaN rows
df = df.dropna(subset=["ID"])

#construct the averages
df["FriendlyAverageElo"] = df[["Friendly1Elo", "Friendly2Elo", "Friendly3Elo", "Friendly4Elo", "Friendly5Elo"]].mean(axis=1)
df["EnemyAverageElo"] = df[["Enemy1Elo", "Enemy2Elo", "Enemy3Elo", "Enemy4Elo", "Enemy5Elo"]].mean(axis=1)
df["AverageEloDiff"] = df["FriendlyAverageElo"] - df["EnemyAverageElo"]

df = df.dropna(subset=["AverageEloDiff"]) #just in case there is NA elo diffs
                                  #if one team has no average, then it comes up NA

df["FriendlyEloStdDev"] = df[["Friendly1Elo", "Friendly2Elo", "Friendly3Elo", "Friendly4Elo", "Friendly5Elo"]].std(axis=1)
df["EnemyEloStdDev"] = df[["Enemy1Elo", "Enemy2Elo", "Enemy3Elo", "Enemy4Elo", "Enemy5Elo"]].std(axis=1)

df = df.dropna(subset = ["FriendlyEloStdDev"]).dropna(subset = ["EnemyEloStdDev"]) #doing it piecewise just in case

#too lazy, here is a workaround for when we create PlayingMapDiff and Dust II has a space in it
df["Dust IIDiff"] = df["DustIIDiff"]

merge_df = pd.merge(df, results, how='left', on='ID')
merge_df["PlayingMapDiff"] = merge_df.apply(lambda row: row[f"{row['Map']}Diff"], axis=1)

almost_final_df = pd.get_dummies(merge_df, columns=["FriendlyStacks", "EnemyStacks", "Map", "StartSide"], dtype=int)

#encode "map active"
for map_col in ['InfernoDiff', 'MirageDiff', 'TrainDiff', 'DustIIDiff', 'NukeDiff', 'AncientDiff', 'OverpassDiff', 'AnubisDiff']:
  trimmedMap = map_col[:-4] #remove the "Diff" from the end

  almost_final_df[f"{trimmedMap}Active"] = almost_final_df[map_col].notna().astype(int)
  almost_final_df[map_col] = almost_final_df[map_col].fillna(-999)

data = almost_final_df[['AverageEloDiff', "FriendlyEloStdDev", "EnemyEloStdDev", 'PlayingMapDiff', 'FriendlyStacks_5',
    'FriendlyStacks_32',    'FriendlyStacks_41',   'FriendlyStacks_221',
   'FriendlyStacks_311',  'FriendlyStacks_2111', 'FriendlyStacks_11111',
        'EnemyStacks_5',       'EnemyStacks_32',       'EnemyStacks_41',
      'EnemyStacks_221',      'EnemyStacks_311',     'EnemyStacks_2111',
    'EnemyStacks_11111',            'Map_Ancient',             'Map_Anubis',
            'Map_Dust II',            'Map_Inferno',             'Map_Mirage',
               'Map_Nuke',           'Map_Overpass',              'Map_Train', 'StartSide_CT', 'StartSide_T',
               'DustIIDiff', 'InfernoDiff', 'MirageDiff', 'TrainDiff', 'NukeDiff', 'AncientDiff', 'OverpassDiff', 'AnubisDiff',
               'DustIIActive', 'InfernoActive', 'MirageActive', 'TrainActive', 'NukeActive', 'AncientActive', 'OverpassActive', 'AnubisActive' ]]
target = almost_final_df["Result"]

train_data, train_test, target_data, target_test = train_test_split(data, target, test_size=0.20, random_state=8)

#############################
### MACHINE LEARNING TIME ###
#############################

#Class to store the information of each model
class Model:
  def __init__(self, name: str, accuracy: float, parameters: dict[str, any]):
    self.name = name
    self.accuracy = accuracy
    self.parameters = parameters
    
  def to_dict(self):
    return{"model": self.name,
           "accuracy": self.accuracy,
           "parameters": self.parameters
           }

models=[]

#Dummies
if(True):
  MostFreqModel = DummyClassifier(strategy="most_frequent").fit(train_data, target_data)

  models.append(
    Model(name="Most Frequent", 
          accuracy=MostFreqModel.score(train_test, target_test), 
          parameters={"strategy": "most_frequent"})
          )

  UniformModel = DummyClassifier(strategy="uniform", random_state=8).fit(train_data, target_data)

  models.append(
    Model(name="Uniform", 
          accuracy=UniformModel.score(train_test, target_test), 
          parameters={"strategy": "uniform"})  
  )

#Decision Tree
if(True):
  params = {
    "max_depth" : range(1, 11, 1)
  }

  grid = GridSearchCV(
    estimator = DecisionTreeClassifier(random_state=8),
    param_grid = params,
    scoring = "accuracy"
  )

  grid.fit(train_data, target_data)

  models.append(
    Model(name="Decision Tree", 
          accuracy=grid.best_score_, 
          parameters=grid.best_params_)
  )

#HistGradientBoostingClassifier
if(True):
  params = {
    "learning_rate" : np.linspace(0.01, 1, 20)
  }

  grid = GridSearchCV(
    estimator = HistGradientBoostingClassifier(random_state=8),
    param_grid = params,
    scoring = "accuracy"
  )

  grid.fit(train_data, target_data)

  models.append(
    Model(name="Histogram Gradient Boosting",
          accuracy=grid.best_score_,
          parameters=grid.best_params_)
  )

#K Nearest Neighbors
if(True):
  params = {
    "n_neighbors" : range(1, 12, 1),
    "weights" : ["uniform", "distance"]
  }

  grid = GridSearchCV(
    estimator = KNeighborsClassifier(),
    param_grid = params,
    scoring = "accuracy"
  )

  grid.fit(train_data, target_data)

  models.append(
    Model(name="K Nearest Neighbors",
          accuracy=grid.best_score_,
          parameters=grid.best_params_)
  )

#AdaBoost with DecisionTreeClassifier
if(True):
  params = {
    "learning_rate" : np.linspace(0.01, 1, 20),
    "n_estimators" : range(10, 101, 10)
  }

  grid = GridSearchCV(
    estimator = AdaBoostClassifier(estimator=DecisionTreeClassifier(max_depth=2),
                                   random_state=8),
    param_grid = params,
    scoring = "accuracy"
  )

  grid.fit(train_data, target_data)

  models.append(
    Model(name="AdaBoost with DecisionTree",
          accuracy=grid.best_score_,
          parameters=grid.best_params_)
  )

#Random Forest Classifier
if(True):

  params = {
   "n_estimators" : range(10, 101, 10),
   "max_depth" : range(1, 11, 1)
  }

  grid = GridSearchCV(
    estimator = RandomForestClassifier(random_state=8),
    param_grid = params,
    scoring = "accuracy"
  )

  grid.fit(train_data, target_data)

  models.append(
    Model(name="Random Forest Classifier",
          accuracy=grid.best_score_,
          parameters=grid.best_params_)
  )

#Logistic Regression
if(True):
  params = {
    "l1_ratio": np.linspace(0, 1, 20),
    "C" : np.linspace(0.01, 1, 20)
  }

  grid = GridSearchCV(
    estimator = LogisticRegression(random_state=8, tol=0.005, max_iter=5000, solver="saga"),
    param_grid = params,
    scoring = "accuracy"
  )

  grid.fit(train_data, target_data)

  models.append(
    Model(name="Logistic Regression",
          accuracy=grid.best_score_,
          parameters=grid.best_params_)
  )

#Show highest accuracy models
models.sort(key=lambda x: x.accuracy, reverse=True)
result = [m.to_dict() for m in models]

with open("./datasets/json/preMatchModels.json", "w") as f:
  json.dump(result, f, indent=2)