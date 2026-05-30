import d6tflow
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

import tasks
from flow import flow

def plot_data():

    df_data = flow.outputLoad(tasks.GetData)
    # plot the data

plot_data()