import numpy as np

def user_input(msg, typ=['y', 'n', 'a', 'q']):
    """Handlt terminal user input"""
    
    inpt = input('%s %s' % (msg, str(typ)))
    if inpt in ['y', 'Y', 'yes', 'Yes', 'YES'] and 'y' in typ:
        out = True
    elif inpt in ['n', 'N', 'no', 'No', 'NO'] and 'n' in typ:
        out = False
    elif inpt in ['a', 'A', 'all', 'All', 'ALL'] and 'a' in typ:
        out = 'all'
    elif inpt in ['q', 'Q', 'quit', 'Quit', 'QUIT'] and 'q' in typ:
        out = 'quit'
    else:
        out = user_input('Please try again!\n%s' % msg)

    return out

def get_precision(self, number):
    """Returns (value, position) of first non zero digit after the decimal point"""
    str_num = str(number)
    dec_pos = str_num.index('.')
    for ii, val in enumerate(str_num[dec_pos+1:]):
        if val != '0':
            return (int(val), ii)
            
def round_tol(self, val, tol):
    """round to match tolarance"""
    return round(val, self.get_precision(tol)[1] + 1)

def filter_data(df, filt, columns):
    """Return df subseted by function filt(x) on x = columns.
     Args:
        df (pd.dataframe): pandas dataframe of one to many columns.
        filter (func): f(x)-->bool array of good values (values to keep); where x is list or np.array.
        columns (list): list of column namse (str) or indicies(ints)
    """
    dfn = df.copy(deep=True)
    #dfn.sort_index(inplace=True) # make sure it is sorted by its index (data frames can be weird) - not needed now bc using 
    for item in columns:
        # accept both index or column name
        column = item
        if isinstance(item, int):  # could also have used df.iloc[rows, cols]
            column = dfn.columns[item]
        # get where(bool array) --> indicies of bad values   # old way
        #ind = np.where(~filt(dfn[column].values))[0]   # old way
        # get bool aray of good values
        tf_df = filt(dfn[column])
        
        #dfn = dfn.drop(ind.tolist(), axis=0, inplace=False)   # old way
        dfn = dfn[tf_df]  #wahaha giving it a boolean array selects from rows rather than columns, WTF?
        
        # reset the indicies so they start at 0 and are continuous
        dfn = dfn.reset_index(drop=True)
    return dfn
    
def filt_3sigma(df, columns=[1], sig=3):
    """Retruns df with values greater than sig(3) sigma removed based on columns"""
    def filt(data):
        """Returns list of sig sigma filtered indices"""
        av = data.mean()
        sd = data.std()
        return np.abs(data-av) <= sig*sd
    return filter_data(df, filt, columns)

def filt_gt(df, columns=[0, 1], val=0):
    """Retrun df with nonpositive (those greater than val) values removed based on columns"""
    def filt(data):
        """Returns list of filtered indices"""
        return data > val
    return filter_data(df, filt, columns)

def filt_lt(df, columns=[0, 1], val=0):
    """Retrun df with nonpositive (those greater than val) values removed based on columns"""
    def filt(data):
        """Returns list of filtered indices"""
        return data < val
    return filter_data(df, filt, columns)

def filt_edge_percent(df, columns=[1], per=0.05):
    """Retruns df with values greater than per removed based on columns"""
    def filt(data):
        """Returns list of filtered indices removing outside %"""
        av = data.mean()
        return np.abs((data-av)/av) <= per
    return filter_data(df, filt, columns)