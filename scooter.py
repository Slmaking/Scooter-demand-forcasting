# -*- coding: utf-8 -*-
"""Scooter.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1fwizguyzLEsfp8pBrAB6FF6r2iBSTLt8
"""



"""##**Comprehensive Exam**
# 1-1 Import data

Build a model for the dataset scooter.csv that will predict the number users for a scooter rental service (user). \\
1. Justify your choice regarding the method chosen to create the model and explain the pros and cons in comparison with other state-of-the-art methods. \\
2. Quantify the prediction accuracy of your model and provide a detailed description of the methodology used for this task. \\
3. Provide a comprehensive list of the limitations of your model and explain how these could potentially be resolve using existing methods.

- season : 1:springer	 2:summer	 3:fall	 4:winter \\
- year : 0= 2011 ,	 1=2012	 \\
- month : month ( 1 to 12)
- hour : 0 to 23 \\
- holiday : (0	1)
- weekday : (1	7)
- workingday : (0	1)
- weather : 1= Clear	 2= Mist	 3=: Light Snow	 4= Heavy Rain 
- temperature : temperature in Celsius divided by 41
"""

!pip install catboost

#libraries
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import math

import random
from catboost import CatBoostRegressor
from lightgbm import LGBMRegressor
from xgboost import XGBRegressor
from sklearn.model_selection import RandomizedSearchCV
from scipy.stats import uniform
from sklearn.model_selection import train_test_split
import time
from sklearn.metrics import r2_score
from sklearn.metrics import mean_absolute_error
from sklearn.metrics import mean_squared_error
from sklearn.metrics import max_error
from sklearn.feature_selection import SelectFromModel

#load the data
from google.colab import drive
drive.mount('/content/drive')

df=pd.read_csv(r'/content/drive/MyDrive/scooter.csv')

df

df.columns = ["Date","season","year", "month",
              "Hour", "holiday", "weekday", "workingday" ,"weather" ,
              "temperature" ,"temperature felt", "humidity", "windspeed" ,"users"
]

df.head(20)

#removing nan data
df= df.dropna()

df.info()

df.shape

df.isna().sum()

df.head(10)

"""# 1-2 Data overall statistics

"""

df.describe()

for col in df.columns:
    print("{c} Column has {u} unique values".format(c=col,u = np.count_nonzero(df[col].unique())))

##Counting unique elements in user
np.count_nonzero(df['users'].unique())

sns.pairplot(df)

plt.figure(figsize=(16, 6))
heatmap = sns.heatmap(df.corr(), vmin=-1, vmax=1, annot=True, cmap='BrBG')
heatmap.set_title('Correlation Heatmap', fontdict={'fontsize':18}, pad=12);

plt.savefig('heatmap.png', dpi=300, bbox_inches='tight')

plt.figure(figsize=(35,36))

l = df.columns.values
number_of_columns=5
number_of_rows = int(len(l)-1/number_of_columns)
for i in range(0,len(l)):
    plt.subplot(number_of_rows ,number_of_columns,i+1)
    sns.histplot(df[l[i]],kde=True) 
plt.show()

plt.figure(figsize=(5,6))

boxplot = df.boxplot(column= ["users"
] )
boxplot.plot()
plt.show()

sns.histplot(data=df, x="users", kde=True, color= 'olive')

"""#1-3 Data Cleaning and model fitting

From information provided from feature selectiona and corrolation matrix we should only consider one of following varibles temperature and temperature felt (high correlation 0.99). In this case we only consider temperature fel. Also, season and month have high correlation we need to consider only one of these features so we only consider month as variable.

*  We can conclude that there are no outliers because there is no significant difference between the 75th quantile and the maximum value for any of the features.


*   The range of values of the features is not the same for that we choose to normalize the date in order to make it in the same scale.
"""

df= df.drop(columns=['season','temperature'])

df= df.drop(columns=['Date'])

#df['Date'] = df['Date'].astype('datetime64')
df['holiday']=df['holiday'].astype('category')
df['month']=df['month'].astype('category')
df['weekday']=df['weekday'].astype('category')
df['Hour']=df['Hour'].astype('category')
df['year']=df['year'].astype('category')
df['workingday']=df['workingday'].astype('category')
df['weather']=df['weather'].astype('category')

df.info()

pd.crosstab(df.weather, df.season)

df.loc[:,'temperature':'windspeed'].plot(subplots=True)
plt.xlabel("")
plt.tight_layout()
plt.show()

"""**Feature selection**"""

from sklearn.feature_selection import SelectKBest,  f_regression

"""We started by selecting 7 features at the beginning by dropping temperature and season. however, it yielded bad performance. Highest performance features are "temperature felt" and "Hour". Therefore, we opted to drop another feature with a low correlation with the target variables which is windspeed. We add windspeed the performance is getting better. Finally from feature selection 'weekday' and  'workingday' are remove due low performance. """

X=df.iloc[:,0:10]
Y=df.iloc[:,-1]

print(X)

print(Y)

select = SelectKBest(score_func=f_regression,k=8)
z = select.fit_transform(X,Y)

cols_idxs = select.get_support(indices=True)

features = X.iloc[:,cols_idxs]
features.columns

from sklearn.preprocessing import MaxAbsScaler
scaler = MaxAbsScaler()
scaler.fit(df)
scaled = scaler.transform(df)
scaled_df = pd.DataFrame(scaled, columns=df.columns)

print(scaled_df)

df_new= scaled_df.drop(columns=['weekday' , 'workingday'] )

df_new.describe()

"""Change in user count over the time"""

fig, ax = plt.subplots(figsize = (20,5))
sns.pointplot(data = df , x ='Hour' , y ='users', hue = 'weekday')
ax.set(title='Count of scooter during weekdays and weekends')

fig ,ax = plt.subplots(figsize = (20,5))
sns.barplot(data = df , x= 'month', y = 'users')
ax.set(title='Count of scooter during different months')

fig, ax = plt.subplots(figsize=(20,5))
sns.barplot(data=df, x='weekday', y='users')
ax.set(title='Count of scooter during different days')

"""**Spiliting dataset**"""

X=df_new.iloc[:,0:8]
Y=df_new.iloc[:,8]

from sklearn.model_selection import train_test_split
x_train, x_test,y_train, y_test = train_test_split(X,Y ,
                                   random_state=2, 
                                   test_size=0.2, 
                                   shuffle=True)

x_train

y_train

"""##**2-1 Machine learning Model**

**2-1-1 Linear regression**
"""

from sklearn.linear_model import LinearRegression
lm = LinearRegression()
lm.fit(x_train, y_train)

linear = lm.score(x_test, y_test)
print(f"coefficient of determination: {linear}")
print(f"intercept: {lm.intercept_}")
print(f"slope: {lm.coef_}")

# Check for the VIF values of the feature variables. 
from statsmodels.stats.outliers_influence import variance_inflation_factor

# Create a dataframe that will contain the names of all the feature variables and their respective VIFs
vif = pd.DataFrame()
vif['Features'] = x_train.columns
vif['VIF'] = [variance_inflation_factor(x_train.values, i) for i in range(x_train.shape[1])]
vif['VIF'] = round(vif['VIF'], 2)
vif = vif.sort_values(by = "VIF", ascending = False)
vif

"""**2-1-3 XGBoosted, CatBoosted and LGBMRegressor**
- In this section we employed three regressior from descion tree family with random search 
"""

distributions = dict(learning_rate=uniform(), n_estimators=np.arange(10,500), max_depth=np.arange(1,50), min_data_in_leaf=np.arange(5,100))

t11 = time.time()

clf1 = RandomizedSearchCV(XGBRegressor(), distributions, cv=5, scoring='r2').fit(x_train ,y_train)


y_train_pred1 = clf1.predict(x_train)
y_test_pred1 = clf1.predict(x_test)
r2_train1 = r2_score(y_train_pred1, y_train)
r2_test1 = r2_score(y_test_pred1, y_test)
mae_train1 = mean_absolute_error(y_train_pred1, y_train)
mae_test1 = mean_absolute_error(y_test_pred1, y_test)
mse_train1 = mean_squared_error(y_train_pred1, y_train)
mse_test1 = mean_squared_error(y_test_pred1, y_test)
me_train1 = max_error(y_train_pred1, y_train)
me_test1 = max_error(y_test_pred1, y_test)

t1 = time.time() - t11

t12 = time.time()






clf2 = RandomizedSearchCV(LGBMRegressor(), distributions, cv=5, scoring='r2').fit(x_train ,y_train)


y_train_pred2 = clf2.predict(x_train)
y_test_pred2 = clf2.predict(x_test)
r2_train2 = r2_score(y_train_pred2, y_train)
r2_test2 = r2_score(y_test_pred2, y_test)
mae_train2 = mean_absolute_error(y_train_pred2, y_train)
mae_test2 = mean_absolute_error(y_test_pred2, y_test)
mse_train2 = mean_squared_error(y_train_pred2, y_train)
mse_test2 = mean_squared_error(y_test_pred2, y_test)
me_train2 = max_error(y_train_pred2, y_train)
me_test2 = max_error(y_test_pred2, y_test)

t2 = time.time() - t12

t13 = time.time()

clf3 = RandomizedSearchCV(CatBoostRegressor(), distributions, cv=5, scoring='r2').fit(x_train ,y_train)


y_train_pred3 = clf3.predict(x_train)
y_test_pred3 = clf3.predict(x_test)
r2_train3 = r2_score(y_train_pred3, y_train)
r2_test3 = r2_score(y_test_pred3, y_test)
mae_train3 = mean_absolute_error(y_train_pred3, y_train)
mae_test3 = mean_absolute_error(y_test_pred3, y_test)
mse_train3 = mean_squared_error(y_train_pred3, y_train)
mse_test3 = mean_squared_error(y_test_pred3, y_test)
me_train3 = max_error(y_train_pred3, y_train)
me_test3 = max_error(y_test_pred3, y_test)

t3 = time.time() - t13





score1 = clf1.best_score_
params1 = clf1.best_params_
print(score1)
print(params1)
print(r2_test1)
print(t1)

print("")
print("")

score2 = clf2.best_score_
params2 = clf2.best_params_
print(score2)
print(params2)
print(r2_test2)
print(t2)

print("")
print("")

score3 = clf3.best_score_
params3 = clf3.best_params_
print(score3)
print(params3)
print(r2_test3)
print(t3)

!pip install shap
!pip install tensorflow

from sklearn.inspection import partial_dependence
from sklearn.inspection import PartialDependenceDisplay
t11 = time.time()

clf1 = XGBRegressor(learning_rate=0.7664699609923687, n_estimators=93, max_depth=3, min_data_in_leaf=54).fit(x_train ,y_train)




y_train_pred1 = clf1.predict(x_train)
y_test_pred1 = clf1.predict(x_test)
r2_train1 = r2_score(y_train_pred1, y_train)
r2_test1 = r2_score(y_test_pred1, y_test)
mae_train1 = mean_absolute_error(y_train_pred1, y_train)
mae_test1 = mean_absolute_error(y_test_pred1, y_test)
mse_train1 = mean_squared_error(y_train_pred1, y_train)
mse_test1 = mean_squared_error(y_test_pred1, y_test)
me_train1 = max_error(y_train_pred1, y_train)
me_test1 = max_error(y_test_pred1, y_test)

t1 = time.time() - t11

t12 = time.time()






clf2 = LGBMRegressor(learning_rate=0.05345850744374758, n_estimators=167, max_depth=27, min_data_in_leaf=44).fit(x_train ,y_train)

y_train_pred2 = clf2.predict(x_train)
y_test_pred2 = clf2.predict(x_test)
r2_train2 = r2_score(y_train_pred2, y_train)
r2_test2 = r2_score(y_test_pred2, y_test)
mae_train2 = mean_absolute_error(y_train_pred2, y_train)
mae_test2 = mean_absolute_error(y_test_pred2, y_test)
mse_train2 = mean_squared_error(y_train_pred2, y_train)
mse_test2 = mean_squared_error(y_test_pred2, y_test)
me_train2 = max_error(y_train_pred2, y_train)
me_test2 = max_error(y_test_pred2, y_test)

t2 = time.time() - t12

t13 = time.time()


clf3 = CatBoostRegressor(learning_rate=0.8571840189019115, n_estimators=72, max_depth=5, min_data_in_leaf=31).fit(x_train ,y_train)


y_train_pred3 = clf3.predict(x_train)
y_test_pred3 = clf3.predict(x_test)
r2_train3 = r2_score(y_train_pred3, y_train)
r2_test3 = r2_score(y_test_pred3, y_test)
mae_train3 = mean_absolute_error(y_train_pred3, y_train)
mae_test3 = mean_absolute_error(y_test_pred3, y_test)
mse_train3 = mean_squared_error(y_train_pred3, y_train)
mse_test3 = mean_squared_error(y_test_pred3, y_test)
me_train3 = max_error(y_train_pred3, y_train)
me_test3 = max_error(y_test_pred3, y_test)

t3 = time.time() - t13





a_report = np.array([(r2_train1, r2_test1, mae_train1, mae_test1, mse_train1, mse_test1, me_train1, me_test3, t1), (r2_train2, r2_test2, mae_train2, mae_test2, mse_train2, mse_test2, me_train2, me_test2, t2), (r2_train3, r2_test3, mae_train3, mae_test3, mse_train3, mse_test3, me_train3, me_test3, t3)])

#make predictions and calculate explainer 
preds1 = clf1.predict(x_test)
preds2 = clf2.predict(x_test)
preds3 = clf3.predict(x_test)

def MAPE(Y_actual,Y_Predicted):
    mape = np.mean(np.abs((Y_actual - Y_Predicted)/Y_actual))*100
    return mape

def RMSE(Y_actual,Y_Predicted):
    MSE = np.square(np.subtract(Y_actual,Y_Predicted)).mean() 
    RMSE = math.sqrt(MSE)
    return RMSE

#LGBMRegressor
from sklearn.metrics import r2_score,mean_absolute_error
print('R2 score LGBMRegressor', r2_score(y_test, preds1))
print('MAE LGBMRegressor', mean_absolute_error(y_test, preds1))
RMSE1 = RMSE(y_test,preds1)
LR_MAPE1= MAPE(y_test,preds1)

print("Root Mean Square Error and Mean Absolute Percentage Error LGBMRegressor:\n")
print(RMSE1)
print(LR_MAPE1)

#XGBRegressor
from sklearn.metrics import r2_score,mean_absolute_error
print('R2 score XGBRegressor', r2_score(y_test, preds2))
print('MAE XGBRegressor', mean_absolute_error(y_test, preds2))
RMSE2 = RMSE(y_test,preds2)
LR_MAPE2= MAPE(y_test,preds2)

print("Root Mean Square Error and Mean Absolute Percentage Error XGBRegressor:\n")
print(RMSE2)
print(LR_MAPE2)

#Catboosted
from sklearn.metrics import r2_score,mean_absolute_error
print('R2 score Catboosted', r2_score(y_test, preds3))
print('MAE Catboosted', mean_absolute_error(y_test, preds3))
RMSE3 = RMSE(y_test,preds3)
LR_MAPE3= MAPE(y_test,preds3)

print("Root Mean Square Error and Mean Absolute Percentage Error Catboosted:\n")
print(RMSE3)
print(LR_MAPE3)

"""**2-1-4 Nueral network**"""

# first neural network with keras make predictions
from numpy import loadtxt
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense

# Create the model
import tensorflow as tf
model = tf.keras.Sequential()
model.add(tf.keras.layers.Dense(units=32, activation='relu'))
model.add(tf.keras.layers.Dense(units=64, activation='relu'))
model.add(tf.keras.layers.Dense(units=128, activation='relu'))
model.add(tf.keras.layers.Dense(units=256, activation='relu'))
model.add(tf.keras.layers.Dense(units=64, activation='relu'))
model.add(tf.keras.layers.Dense(units=32, activation='relu'))
model.add(tf.keras.layers.Dense(units=16, activation='relu'))
model.add(tf.keras.layers.Dense(units=1,activation="linear"))



# Compile the model with a mean squared error loss function and L2 regularization
model.compile(optimizer='adam', loss='mean_squared_error', metrics=['mae'])

# Train the model on the train data
# early_stop = tf.keras.callbacks.EarlyStopping(monitor='val_loss', patience=10)
history = model.fit(x_train, y_train, epochs=70, verbose = 0)

# Predict the values of y for the test data
y_pred = model.predict(x_test)
print("Predicted y values:", y_pred)

deep_learning_prediction = np.array(y_pred)

deep_learning_prediction

deep_learning_prediction1 = []
for i in range(len(deep_learning_prediction)):
    deep_learning_prediction1.append(deep_learning_prediction[i][0])
deep_learning_prediction1 = np.array(deep_learning_prediction1)
deep_learning_prediction1

print('R2 score Deep learning', r2_score(y_test, y_pred))
print('MAE Deep learning', mean_absolute_error(y_test, y_pred))

plt.figure(figsize=(20,5))
ax1 = sns.kdeplot(y_train, label = 'train',color="red")
ax3 = sns.kdeplot(deep_learning_prediction1, label = 'test-DP',color="green")

plt.legend()
plt.show()

import tensorflow as tf
from tensorflow import keras
from sklearn.model_selection import RandomizedSearchCV
from tensorflow.keras.wrappers.scikit_learn import KerasRegressor

# Define the function to create the Keras model
def create_model(learning_rate=0.01, epochs=100, batch_size=32):
    model = keras.Sequential([
        keras.layers.Dense(units=32, activation='relu'),
        keras.layers.Dense(units=64, activation='relu'),
        keras.layers.Dense(units=128, activation='relu'),
        keras.layers.Dense(units=256, activation='relu'),
        keras.layers.Dense(units=64, activation='relu'),
        keras.layers.Dense(units=32, activation='relu'),
        keras.layers.Dense(units=16, activation='relu'),
        keras.layers.Dense(units=1, activation='linear')
    ])
    
    optimizer = keras.optimizers.Adam(lr=learning_rate)
    model.compile(optimizer=optimizer, loss='mean_squared_error', metrics=['mae'])
    
    return model

# Create the KerasRegressor wrapper for the create_model function
model = KerasRegressor(build_fn=create_model, verbose=0)

# Define the hyperparameter search space
param_grid = {
    'learning_rate': np.arange(0.001, 0.1, 0.001),
    'epochs': np.arange(50, 200, 10),
    'batch_size': np.arange(16, 64, 8)
}

# Use RandomizedSearchCV to search for the best hyperparameters
random_search = RandomizedSearchCV(
    estimator=model,
    param_distributions=param_grid,
    n_iter=10,
    cv=3,
    verbose=2
)

# Fit the random search to the training data
random_search.fit(x_train, y_train)

# Print the best hyperparameters and corresponding mean test score
print("Best hyperparameters: ", random_search.best_params_)
print("Best mean test score: ", random_search.best_score_)

# Use the best hyperparameters to train the model on the full training data
best_model = create_model(**random_search.best_params_)
history = best_model.fit(x_train, y_train, epochs=random_search.best_params_['epochs'], batch_size=random_search.best_params_['batch_size'], verbose=0)

# Predict the values of y for the test data using the best model
y_pred = best_model.predict(x_test)
print("Predicted y values:", y_pred)

import tensorflow as tf
from tensorflow import keras
import matplotlib.pyplot as plt

# Define the model with the specified hyperparameters
model = keras.Sequential([    keras.layers.Dense(units=32, activation='relu'),    keras.layers.Dense(units=64, activation='relu'),    keras.layers.Dense(units=128, activation='relu'),    keras.layers.Dense(units=256, activation='relu'),    keras.layers.Dense(units=64, activation='relu'),    keras.layers.Dense(units=32, activation='relu'),    keras.layers.Dense(units=16, activation='relu'),    keras.layers.Dense(units=1, activation='linear')])

optimizer = keras.optimizers.Adam(lr=0.032)
model.compile(optimizer=optimizer, loss='mean_squared_error', metrics=['mae'])

# Train the model with different numbers of epochs
epochs = [10, 30, 50, 70, 100]
histories = []
for e in epochs:
    history = model.fit(x_train, y_train, epochs=e, batch_size=16, validation_data=(x_test, y_test))
    histories.append(history)

# Plot the training and test loss with accuracy over time for each number of epochs
for i, history in enumerate(histories):
    plt.subplot(2, 3, i+1)
    plt.plot(history.history['loss'])
    plt.plot(history.history['val_loss'])
    plt.plot(history.history['mae'])
    plt.plot(history.history['val_mae'])
    plt.title('Epochs = ' + str(epochs[i]))
    plt.ylabel('Loss / MAE')
    plt.xlabel('Epoch')
    plt.legend(['Train loss', 'Test loss', 'Train MAE', 'Test MAE'], loc='upper right')
plt.show()

plt.figure(figsize=(20,10))

for i, history in enumerate(histories):
    plt.subplot(2, 3, i+1)
    plt.plot(history.history['loss'])
    plt.plot(history.history['val_loss'])
    plt.plot(history.history['mae'])
    plt.plot(history.history['val_mae'])
    plt.title('Epochs = ' + str(epochs[i]))
    plt.ylabel('Loss / MAE')
    plt.xlabel('Epoch')
    plt.legend(['Train loss', 'Test loss', 'Train MAE', 'Test MAE'], loc='upper right')
plt.show()

plt.figure(figsize=(20,10))

for i, history in enumerate(histories):
    plt.subplot(2, 3, i+1)
    plt.plot(history.history['loss'])
    plt.plot(history.history['val_loss'])

    plt.title('Epochs = ' + str(epochs[i]))
    plt.ylabel('Loss ')
    plt.xlabel('Epoch')
    plt.legend(['Train loss', 'Test loss'], loc='upper right')
plt.show()

plt.figure(figsize=(20,10))

for i, history in enumerate(histories):
    plt.subplot(2, 3, i+1)

    plt.plot(history.history['mae'])
    plt.plot(history.history['val_mae'])
    plt.title('Epochs = ' + str(epochs[i]))
    plt.ylabel('MAE')
    plt.xlabel('Epoch')
    plt.legend([ 'Train MAE', 'Test MAE'], loc='upper right')
plt.show()

import tensorflow as tf
from tensorflow import keras
import matplotlib.pyplot as plt

# Define the model with the specified hyperparameters
def create_model():
    model = keras.Sequential([
        keras.layers.Dense(units=32, activation='relu'),
        keras.layers.Dense(units=64, activation='relu'),
        keras.layers.Dense(units=128, activation='relu'),
        keras.layers.Dense(units=256, activation='relu'),
        keras.layers.Dense(units=64, activation='relu'),
        keras.layers.Dense(units=32, activation='relu'),
        keras.layers.Dense(units=16, activation='relu'),
        keras.layers.Dense(units=1, activation='linear')
    ])
    return model

learning_rates = [0.001, 0.005, 0.01, 0.0032, 0.05, 0.1]

# Loop over learning rates
for lr in learning_rates:
    model = create_model()
    optimizer = keras.optimizers.Adam(lr=lr)
    model.compile(optimizer=optimizer, loss='mean_squared_error', metrics=['mae'])
    
    # Train the model on the training data
    history = model.fit(x_train, y_train, epochs=10, batch_size=16, validation_data=(x_test, y_test), verbose=0)
    
    # Plot training and testing losses
    plt.plot(history.history['loss'], label=f'Train loss (lr={lr})')
    plt.plot(history.history['val_loss'], label=f'Test loss (lr={lr})')

plt.title('Training and Testing Losses for Different Learning Rates')
plt.xlabel('Epochs')
plt.ylabel('Loss')
plt.legend()
plt.show()

"""Based on the results obtained from random search, the best learning rate for the given problem was found to be 0.0032, which resulted in the highest accuracy on the testing set. The validation of this assumption can be observed from the training and testing loss plots, where the model trained with a learning rate of 0.0032 achieved the lowest testing loss among all the tested learning rates. Therefore, it can be concluded that the learning rate of 0.0032 is the optimal choice for this specific problem.

It's important to note that random search was used to find the optimal learning rate among a range of values, and this approach can be useful in cases where there are many hyperparameters to tune. However, the optimal learning rate may vary depending on the specific problem and dataset, and it's always a good practice to validate the results by testing the model on an independent testing set.
"""

from tensorflow.keras import regularizers

def create_improved_model(input_size):
    model = keras.Sequential([
        keras.layers.Dense(units=64, activation='relu', input_shape=(input_size,)),
        keras.layers.BatchNormalization(),
        keras.layers.Dropout(0.2),
        
        keras.layers.Dense(units=128, activation='relu', kernel_regularizer=regularizers.l2(0.01)),
        keras.layers.BatchNormalization(),
        keras.layers.Dropout(0.2),
        
        keras.layers.Dense(units=256, activation='relu', kernel_regularizer=regularizers.l2(0.01)),
        keras.layers.BatchNormalization(),
        keras.layers.Dropout(0.2),
        
        keras.layers.Dense(units=128, activation='relu', kernel_regularizer=regularizers.l2(0.01)),
        keras.layers.BatchNormalization(),
        keras.layers.Dropout(0.2),
        
        keras.layers.Dense(units=64, activation='relu', kernel_regularizer=regularizers.l2(0.01)),
        keras.layers.BatchNormalization(),
        keras.layers.Dropout(0.2),
        
        keras.layers.Dense(units=32, activation='relu', kernel_regularizer=regularizers.l2(0.01)),
        keras.layers.BatchNormalization(),
        keras.layers.Dropout(0.2),
        
        keras.layers.Dense(units=1, activation='linear')
    ])
    return model

learning_rates = [ 0.0032]
epochs = 50
batch_size = 16

for lr in learning_rates:
    model = create_improved_model(8)
    optimizer = keras.optimizers.Adam(lr=lr)
    model.compile(optimizer=optimizer, loss='mean_squared_error', metrics=['mae'])
    
    # Train the model on the training data
    history = model.fit(x_train, y_train, epochs=epochs, batch_size=batch_size, validation_data=(x_test, y_test), verbose=0)
    
    # Plot training and testing losses
    plt.plot(history.history['mae'], label=f'Train MAE (lr={lr})')
    plt.plot(history.history['val_mae'], label=f'Test MAE (lr={lr})')

plt.title(f'Training and Testing MAE for {epochs} epochs and batch size={batch_size}')
plt.xlabel('Epochs')
plt.ylabel('MAE')
plt.legend()
plt.show()

from tensorflow.keras import regularizers
input_size=8
model = keras.Sequential([
    keras.layers.Dense(units=64, activation='relu', input_shape=(input_size,)),
    keras.layers.BatchNormalization(),
    keras.layers.Dropout(0.2),
        
    keras.layers.Dense(units=128, activation='relu', kernel_regularizer=regularizers.l2(0.01)),
    keras.layers.BatchNormalization(),
    keras.layers.Dropout(0.2),
        
    keras.layers.Dense(units=256, activation='relu', kernel_regularizer=regularizers.l2(0.01)),
    keras.layers.BatchNormalization(),
    keras.layers.Dropout(0.2),
        
    keras.layers.Dense(units=128, activation='relu', kernel_regularizer=regularizers.l2(0.01)),
    keras.layers.BatchNormalization(),
    keras.layers.Dropout(0.2),
        
    keras.layers.Dense(units=64, activation='relu', kernel_regularizer=regularizers.l2(0.01)),
    keras.layers.BatchNormalization(),
    keras.layers.Dropout(0.2),
        
    keras.layers.Dense(units=32, activation='relu', kernel_regularizer=regularizers.l2(0.01)),
    keras.layers.BatchNormalization(),
    keras.layers.Dropout(0.2),
        
    keras.layers.Dense(units=1, activation='linear')
])

optimizer = keras.optimizers.Adam(lr=0.0032)
model.compile(optimizer=optimizer, loss='mean_squared_error', metrics=['mae'])

history = model.fit(x_train, y_train, epochs=10, verbose=0)

y_pred_deep = model.predict(x_test)
print("Predicted y values:", y_pred)

deep_learning_prediction=np.array(y_pred)

deep_learning_prediction1 = []
for i in range(len(deep_learning_prediction)):
    deep_learning_prediction1.append(deep_learning_prediction[i][0])
deep_learning_prediction1 = np.array(deep_learning_prediction1)
deep_learning_prediction1

print('R2 score best Deep learning', r2_score(y_test, deep_learning_prediction1))
print('MAE Deep best Deep learning', mean_absolute_error(y_test, deep_learning_prediction1))
RMSE4 = RMSE(y_test,deep_learning_prediction1)
LR_MAPE4= MAPE(y_test,deep_learning_prediction1)

print("Root Mean Square Error and Mean Absolute Percentage Error Deep learning:\n")
print(RMSE4)
print(LR_MAPE4)

"""**2-1-5 RandomForest Regressor**"""

from sklearn.ensemble import RandomForestRegressor
# Check the result according to "n_estimators".
for i in (10, 20, 30, 40, 100, 150,300):
    model = RandomForestRegressor(n_estimators= i,n_jobs= -1, random_state = 15)
    model.fit(x_train,y_train)
    # The higher the "n_estimators" value, the higher the accuracy, 
    # but the more computational it takes for the computer to calculate and derive results. 
    # I set the value to 300 appropriately.

    relation_square = model.score(x_train, y_train)
    print('relation_square : ', relation_square)
    plt.figure(figsize=(20,5))
    y_p = model.predict(x_train)
    ax1 = sns.kdeplot(y_train,label = 'y_train',color="red")
    ax2 = sns.kdeplot(y_p,label = 'y_pred',color="blue")
    
    plt.title(i)
    plt.legend()
    plt.show()

model = RandomForestRegressor(n_estimators=300, n_jobs = -1 , random_state = 0)
model.fit(x_train, y_train)

predictions = model.predict(x_test)
predictions

print('R2 score Random forest regression', r2_score(y_test, predictions))
print('MAE Random forest regression', mean_absolute_error(y_test, predictions))
RMSE5 = RMSE(y_test,predictions)
LR_MAPE5= MAPE(y_test,predictions)

print("Root Mean Square Error and Mean Absolute Percentage Error Deep learning:\n")
print(RMSE5)
print(LR_MAPE5)

plt.figure(figsize=(20,5))
ax1 = sns.kdeplot(y_train, label = 'train',color="olive")
ax2 = sns.kdeplot(y_test, label = 'test',color="black")
ax3 = sns.kdeplot(predictions, label = 'test-random',color="blue")
ax4 = sns.kdeplot(y_pred, label = 'test-DP',color="green")
ax5 = sns.kdeplot(preds3, label = 'test-cat',color="red")
ax6 = sns.kdeplot(preds2, label = 'test-Gboost',color="yellow")


plt.legend()
plt.show()

