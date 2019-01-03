import os
import csv
import platform
from .either import Either
import re
import collections
import pandas as pd
import numpy as np
from .basic_tools import user_input, filt_gt, filt_lt, filt_3sigma, filt_edge_percent


def find_base_path():
    """
    function find_base_path() -> os.path
    
    returns:
        system dependant base path
    """
    if platform.system() == 'windows':
        base_path = os.path.join('K:', 'ptestbend')
    else:
        base_path = os.path.join('/mnt','K', 'ptestbend')
    return base_path
        
def find_spec_path(freq, device_num):
    """
    function find_specs_path: (string, string) -> os.path

    parameters:
        freq: string representation of frequency, 4 characters long. Zero padding on left to 
                    match format in K:/ptestbend
        part_number: the 88 part number of the spec to load
    """    
    base_path = find_base_path()
    spec_path = os.path.join(base_path, str(freq), 'Specs', str(device_num) + '.txt')
    #path_name =  os.path.join(base_path, str(freq), str(wafer), 'FinalAcceptance', str(device_num))
    return spec_path


def find_test_path(base_path, freq, wafer, test_step, d8_num, test_spec):
    """get path of a wafertest test file"""
    full_path = os.path.join(base_path, str(freq), str(wafer), test_step)
    # get test spec # # # # # # # # # # # # # # # # # # # # # # # # # # #
    if not test_spec:
        files_list = os.listdir(full_path)
        p = re.compile('.*' + re.escape(str(d8_num)))
        files = list(filter(p.match, files_list))
        if not files:
            raise ValueError('No test spec with "%s"\nFiles available: %s' % (str(d8_num), str(files_list)))
        elif len(files) > 1:
            raise ValueError('More than one test spec has been used for "%s"' % str(d8_num))
            
        full_path = os.path.join(full_path, files[0])    
    else:
        full_path = os.path.join(full_path, test_spec + str(d8_num))
    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
    return full_path


def get_filename(full_path, file_num):
    """get file name"""
    files_list = os.listdir(full_path)
    if int(file_num) < 1:
        p = re.compile('\d{4,5}-p\d-\d\d')

    else:
        p = re.compile('\d{4,5}-p\d-' + str(file_num))
        file_num = 0
        
    fname = list(filter(p.match, files_list))
    if len(fname) >= abs(int(file_num)):
        fname.sort(key = lambda x: x[-3:-1])
        fname = fname[int(file_num)]
        fname = fname[0:-4]  # remove extension from fname
    else:
        fname = None
    return fname
    
def get_target_param(summary, test_step=None, target_param=None):
    """Return the target parameter based on the test step or string given"""
    if not target_param:
        if test_step == "ResonatorMap":
            p = re.compile('ResFreq' + '.*', flags=re.IGNORECASE)
            columns = list(filter(p.match, list(summary.dataframe)))
        elif test_step == "WaferMap":
            p = re.compile('CF' + '.*', flags=re.IGNORECASE)
            columns = list(filter(p.match, list(summary.dataframe)))
        else:
            raise ValueError('test_step inproperly set.\nMust be "ResonatorMap", "WaferMap"')
    else:
        p = re.compile(re.escape(target_param) + '.*', flags=re.IGNORECASE)
        columns = list(filter(p.match, list(summary.dataframe)))
        
    if columns:
        target_param = columns[0]
        print('Using:', target_param)
    else:
         raise ValueError('no matching comumn: "%s" ??' % target_param)
    return target_param

def read_filmetrics(fileName):
    FilmetricsSummary = collections.namedtuple('Filmetrics_File', ['header', 'dataframe'])
    with open(fileName + '.txt') as f:
        header = {}
        for l in f:
            if l.strip('\n')[0:4] == "\"Die":
                # if starts with "Die
                # "column", "column2", "column3", ...
                header['columns'] = l.strip('\n').replace('"', "").split(",")
                break
            else:
                # name, value \n
                attribute =  l.strip('\n').split(',')
                if len(attribute) == 2:
                    header[attribute[0]] = attribute[1]
        # get data into dataframe
        df = pd.read_csv(f, header=None, names=header['columns'], skipfooter=4, engine='python', quotechar='\"')
    # remove outliers from thickness    
    df_filt = filt_edge_percent(filt_3sigma(df,['Site 1 Layer 1 Thickness (A)']), ['Site 1 Layer 1 Thickness (A)'])
    return WaferViewSummary(header, df_filt)

def read_CDE(filename):
    CDESummary = collections.namedtuple('CDE_File', ['header', 'dataframe'])
    with open(filename + '.RsM') as f:
        header = {'FileName': filename,} # should be capture in files header but justincase
        lines = [a for a in f]
    for il, line in enumerate(lines):
        while '  ' in line:
            line = line.replace('  ', '\t')
        sline = re.split(r'\t+', line)
        if '<' in line:
            cols = line[line.find('<') + 1:line.find('>')].split(',')
            if 'Data,' in line:
                header['columns'] = [col.strip() for col in cols]
                lines[il] = lines[il][:lines[il].find('\t')]
                data = [list(map(float, s)) for s in [re.split(r'\s+', dat.strip()) for dat in lines[il:]]]
                df = pd.DataFrame.from_records(data, columns=header['columns'])
                break
            else:
                for ic, col in enumerate(cols):
                    header[col.strip()] = sline[ic].strip()
        else:
            raise ValueError('This should not be.\nAll lines in header should include "<"')
    # remove outliers from thickness    
    #df_filt = filt_edge_percent(filt_3sigma(df,['Site 1 Layer 1 Thickness (A)']), ['Site 1 Layer 1 Thickness (A)'])
    return CDESummary(header, df)

def read_waferview(fileName, rm_param=None, rm_gt=None, rm_lt=None):
    """return named tuple with header and dataframe from WaferView test file"""
    WaferViewSummary = collections.namedtuple('WaferView_File', ['header', 'dataframe'])
    with open(fileName + '.txt') as f:
        header = {}
        for l in f:
            if l.strip('\n') == "!begin_data":
                # data \n
                header['columns'] = f.readline().strip('! ').strip('\n').split()
                break
            else:
                # ! name: value \n
                attribute =  l.strip('! ').strip('\n').split(': ')
                if len(attribute) == 2:
                    header[attribute[0]] = attribute[1]
        # get data into dataframe
        df = pd.read_csv(f, header=None, names=header['columns'], delim_whitespace=True, comment='!')
        df = df.sort_values('DieNum')
        summary = WaferViewSummary(header, df)
      
        orr = df.shape[0]
        if rm_param:
            rm_param = [get_target_param(summary, target_param=rm_param)]
            if rm_gt:
                df = filt_lt(df, columns=rm_param, val=rm_gt)
                print('removed %s rows where %s > %s' % (orr - df.shape[0], rm_param, rm_gt))
            if rm_lt:
                df = filt_gt(df, columns=rm_param, val=rm_lt)
                print('removed %s rows where %s < %s' % (orr - df.shape[0], rm_param, rm_gt))
            if not rm_gt or rm_lt:
                raise ValueError("With rm_param sepcified at least  one of rm_gt or rm_lt must be specified")
            summary = WaferViewSummary(header, df)       
    return summary

def read_ibe(file):
    """return named tuple with header and dataframe from ibe trim file"""
    ibeSummary = collections.namedtuple('ibe_File', ['header', 'dataframe'])
    if not os.path.exists(file + '.ibe'):
        return ibeSummary(None, None)
    with open(file + '.ibe','rb') as f:
        header = {}
        for l in f:
            #print(l)
            l = l.decode('ascii')
            #print(l)
            if l.strip('\n')[0:2] == "%m":
                header['units'] = l.strip('%').strip('\r\n').split()
                break
            elif l.strip('\n')[0:2] == "%x":
                header['columns'] = l.strip('%').strip('\r\n').split()
            elif l.strip('\n')[0:4] == "%ibe":
                vals = l.strip('%').strip('\r\n').split('\t')
                # get data
                for ii, val in enumerate(vals):
                    if ii < 1:
                        continue
                    if ii%2 == 0:
                        continue
                    if ii < len(vals)-1:
                         header[val.strip(':')] = vals[ii+1]
            elif l.strip('\n')[0:1] != "%":
                    break
            else:
                raise ValueError('Improper header for ibe!!??')
        # get data into dataframe
        df = pd.read_csv(f, header=None, names=header['columns'], delim_whitespace=True, comment='!')
    return ibeSummary(header, df)

def write_ibe(file, ibe_filt, target, rate_f):
    # Write the ibe
    with open(file,'w', newline='\r\n') as f:
        data = [target] + rate_f
        f.write('%ibe-file\ttarget:\t{0}\ta:\t{1}\tb:\t{2}\tc:\t{3}\n'.format(*data))
        f.write('%x\ty\tremoval\n')
        f.write('%mm\tmm\tnm\n')
        ibe_filt.to_csv(f, header=False, index=False, mode='a', sep="\t", quoting=csv.QUOTE_NONE)

def file_not_exist(file):
    """Return true or false depending is file exist"""
    save = True
    if os.path.exists(file):
        if not user_input('File %s exist, overwrite?' % file, typ=['y', 'n']):
            save = False
            print('not saved')
    return save

def exist_spec(dirs, test_spec, test_step_path):
    """
    function exist_spec: (list, string, os.path) -> True
    
    parameters:
        dirs: list of dirs matching test spec
        test_step_path: path of test step (WaferMap, DieTest, etc). Camel case. 
        test_spec: string representation of test spec. For example 'd80275' could be shortened to 'd8'
    returns:
        True if len(dirs) == 1 else raises error
    """
    if len(dirs) == 0:
         raise ValueError("There are no {0} spec tests in {1}".format(test_spec, test_step_path))
        
    elif len(dirs) > 1:
         raise ValueError("There is more than one {0} spec in {1}".format(test_spec, test_step_path), "clean up that directory and then re-run your analysis")
            
    return True
    
def exist_dir(d8_path):
    """
    ensures that the new path is actually a directory
    """
    if not os.path.isdir(d8_path):
        raise NotADirectoryError("The file at {0} is not a directory and so cannot be used for Yield Analysis".format(d8_path))
    else:
        return True

    
# Clean up and eventually remove ##################################################################
    
def find_d8_path(freq, wafer_id, test_step, test_spec):
    """
    function find_d8_path: (string, string, string, string) -> IO(Either(os.path))
    
    parameters:
        freq: string representation of frequency, 4 characters long. Zero padding on left to 
                    match format in K:/ptestbend
        wafer_id:  string representation of wafer id.
        test_step: string representing test step (WaferMap, DieTest, etc). Camel case. 
        test_spec: string representation of first two characters of test spec. For example 
                    'd80275' should be shortened to 'd8'                    
    returns: 
        IO(Either(os.path)): an IO computation which will return a tuple when run. The left side of the tuple
                            will contain an error if one occured. If no error occured, then the right side 
                            will contain an os.path
    """
    
    test_step_path = os.path.join(find_base_path() ,str(freq), str(wafer_id), str(test_step))
    
    def pathIO():        
        d8_path =(Either.Try(lambda: [x for x in os.listdir(test_step_path) if x.lower()[0:len(test_spec)] == test_spec.lower()]) # finad all matching test spec
                  .filter(lambda x: exist_spec(x,test_spec,test_step_path)) # f checks the that the length of the returned list is 1
                  .map(lambda x: x[0]) # extract the first element
                  .map(lambda x: os.path.join(test_step_path, x)) # join that element to make a path
                  .filter(exist_dir) # ensures that the new path is actually a directory
                  )

        return d8_path

    return pathIO