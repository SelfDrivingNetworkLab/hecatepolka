#Polka retuns (BW, latency) per path saved in database
"""
Notes: predicting for multi-variate (getting input of path n features) and predict these in the future
Example csv file:
path 1, path 2 
15, 3, 25, 3 
path 2
"""
# Importing necessary libraries
import pandas as pd

import numpy as np
from statsmodels.tsa.vector_ar.var_model import VAR
import matplotlib.pyplot as plt
# Load multivariate time series data
import generatetestdata


paths=3
"""
def test_path_predictor():
    #data = pd.read_csv('multivariate_data.csv')
    # Fit the VAR model
    pathdata=generatetestdata.generate_pathlist(paths)
    print(pathdata)
    pathcolumns=[]
    for i in range(paths):
        for j in range(10):
            #pathcolumns[i]=pathdata[i][j]['bandwidth'],pathdata[i][j]['latency']
            print("pathdata")
            print(pathdata[i][j]['bandwidth'], pathdata[i][j]['latency'])
    data=pd.DataFrame.from_dict(pathdata)
    print(pathcolumns)    
    print(data)
    model = VAR(data)
    model_fit = model.fit()
    # Forecast future values
    forecast = model_fit.forecast(model_fit.endog, steps=5)
    print(forecast)

    # Plot the forecasted values
    plt.figure(figsize=(10, 6))
    for i in range(len(data.columns)):
        plt.plot(data.index, data.iloc[:, i], label=data.columns[i])
        plt.plot(range(len(data), len(data) + 5), forecast[:, i], 'r--', label='Forecast '+data.columns[i])
    plt.legend()
    plt.title('Multivariate Forecast using VAR')
    plt.xlabel('Time')
    plt.ylabel('Values')
    plt.show()
"""

def test_path_predictor():
    #data = pd.read_csv('multivariate_data.csv')
    # Fit the VAR model
    pathdata=generatetestdata.generate_pathlist(paths)
    print(pathdata)
    pathcolumns=[]
    
    data=pd.DataFrame.from_dict(pathdata,orient='index')
    print("new")    
    print(data)
    model = VAR(data)
    model_fit = model.fit()
    # Forecast future values
    forecast = model_fit.forecast(model_fit.endog, steps=5)
    print(forecast)

    # Plot the forecasted values
    plt.figure(figsize=(10, 6))
    for i in range(len(data.columns)):
        plt.plot(data.index, data.iloc[:, i], label=data.columns[i])
        plt.plot(range(len(data), len(data) + 5), forecast[:, i], 'r--', label='Forecast '+str(data.columns[i]))
    plt.legend()
    plt.title('Multivariate Forecast using VAR')
    plt.xlabel('Time')
    plt.ylabel('Values')
    plt.show()

test_path_predictor()
