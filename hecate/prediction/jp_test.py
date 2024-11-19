
#Polka retuns (BW, latency) per path saved in database

import os
import sys
import time
import pandas as pd
import numpy as np
from pprint import pprint
import collections

from matplotlib import pyplot as plt
from matplotlib.lines import Line2D
from mpl_toolkits.mplot3d import axes3d
from matplotlib.transforms import Bbox
from matplotlib import cm 
from matplotlib.ticker import MaxNLocator
from sklearn.base import clone



import warnings
warnings.filterwarnings("ignore")
from sklearn.model_selection import cross_val_score, KFold,cross_val_predict,cross_validate
from sklearn.metrics import precision_score, recall_score, f1_score,accuracy_score,roc_curve,\
classification_report,confusion_matrix, ConfusionMatrixDisplay,mean_squared_error,r2_score,roc_auc_score,auc
from sklearn.tree import DecisionTreeRegressor
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import label_binarize


from sklearn.naive_bayes import GaussianNB
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier
from sklearn import svm, tree
from sklearn.neighbors import KNeighborsClassifier
from sklearn.model_selection import cross_val_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline


from scipy import stats


pd.set_option('max_colwidth', 800)


def simple_predictor(routes_df, label_df,new_df):

    #routes_qos=np.loadtxt(f"{data_path}\\routes_bw.txt", comments='#',dtype=float)
    # Train-test Split

    X_train, X_test, y_train, y_test = train_test_split(routes_df,label_df, test_size = 0.2,
                                                    random_state=1234,
                                                    shuffle = True, stratify = None)
    print(X_train)
    print("testing...")
    print(y_train)
    model = LogisticRegression()
    model.fit=(X_train,y_train)
    print("Predicting...")
    yhat=model.predict(y_test)#uncomment for extension
    #yhat=new_df
    print(yhat)
    


def test_ML_fn():
    #load the data
    route_data_df=pd.read_csv("/Users/9mk/softwares/GitHub/hecatepolka/datasets/networkdatasets/linkdata/routes_bw.txt", sep=" ", header= None)
    
    routes_label_df=pd.read_csv("/Users/9mk/softwares/GitHub/hecatepolka/datasets/networkdatasets/linkdata/bw_routes_label.txt", sep=" ", header= None)


    print(route_data_df )
    route_data_df.columns=["#Time(m)","WiFi","4G"]
    newdf=[20.2,27.5,20.2,27]


    simple_predictor(route_data_df,routes_label_df,newdf)

test_ML_fn()
