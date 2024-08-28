import pandas as pd
import numpy as np
# Generate multivariate time series data for VAR example

np.random.seed(0)

num_samples = 100

def generate_csv():
    data = pd.DataFrame({
        'path1bandwidth': np.random.randint(100, size=num_samples),
        'path1latency': np.random.randint(40, size=num_samples),
        'path2bandwidth': np.random.randint(100, size=num_samples),
        'path2latency': np.random.randint(40, size=num_samples),
    })
    # Save generated data to a CSV file
    data.to_csv('multivariate_data.csv', index=False)
    #data

def generate_pathlist(num_paths):
    pathlist={}
    #print(num_paths)
    for j in range(10):
        temp=[]
        for i in range(num_paths):
        #pathlist[i]={}
            bw=np.random.randint(100)
            lat=np.random.randint(30)
            temp.append(bw)
            temp.append(lat)
        pathlist[j]={}
        pathlist[j]=temp
            





    return(pathlist)


generate_pathlist(2)