# Stdlib imports
import os
import csv
# Third-Party imports
import pandas as pd
import numpy as np
# Local imports
from .basic_tools import user_input, filt_gt, filt_3sigma, filt_edge_percent

def trimToFreq(target, targ_param, df, flatLocation, rate_func):
    """ToDo
     Args:
        target (int, float): ToDO
    """
    # remove 0 or negative values from target parameter
    df = filt_gt(df, [targ_param])
    
    # get x and y in mm
    x = df['DieX']/1000
    y = df['DieY']/1000
    if int(flatLocation)==180:
        x = -df['DieY']/1000
        y = df['DieX']/1000
    # create shift column
    shift = target - df[targ_param]
    # apply rate function to shift to get [nm] from [Hz]
    shift = shift.apply(rate_func)
    
    # create dataframe from arrays
    ibe = pd.DataFrame(np.array([x, y, shift]).T, columns = ['x', 'y', 'shift'])
    
    # get values for filtering
    av = ibe['shift'].values.mean()
    sd = ibe['shift'].values.std()
    print(av, sd)
    # Filter ibe
    # clip sets value to bound (lower or upper) per column
    # clip outside 3 sd --> lower = av - 3*sd; upper = av + 3*sd
    print(av + 3*sd)
    lower_bounds = pd.Series({'x': -np.inf, 'y': -np.inf, 'shift': max([0, av - 3*sd])})
    upper_bounds = pd.Series({'x': np.inf, 'y': np.inf, 'shift': av + 3*sd})                      
    ibe_filt = ibe.clip(lower=lower_bounds, upper=upper_bounds, axis=1)
    return ibe_filt

def trimToThickness(target, df):
    x = df['Die x (mm)']
    y = df['Die y (mm)']
    shift = (df['Site 1 Layer 1 Thickness (A)'] - target)/10 # A -> nm
    shift = shift.rename('Shift')

    ibe = pd.DataFrame(np.array([x,y,shift]).T, columns = ['x', 'y', 'shift'])

    av = shift.mean()
    sd = shift.std()
    
    # clip sets value to bound (lower or upper) per column
    # clip outside 3 sd --> lower = av - 3*sd; upper = av + 3*sd
    lower_bounds = pd.Series({'x': -np.inf, 'y': -np.inf, 'shift': max([0, av - 3*sd])})
    upper_bounds = pd.Series({'x': -np.inf, 'y': -np.inf, 'shift': av + 3*sd})                      
    ibe_filt = ibe.clip(lower=lower_bounds, upper=upper_bounds, axis=1)
    return ibe_filt
