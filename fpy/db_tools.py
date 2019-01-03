import pyodbc 
import pandas as pd
from datetime import datetime
from pytz import timezone

def db_connect():
    cnxn = pyodbc.connect("Driver={ODBC Driver 17 for SQL Server};"
                          "Server=rdm0sql01;"
                          "Database=MES_af;"
                          "Uid=austin;"
                          "Pwd=Test;")
                          #"Trusted_Connection=yes;")
    return cnxn


def get_wafer_trimdata(waferid):

    cnxn = db_connect()
    sql = (
        "SELECT "
        " IonTrim.[id]"
        ",IonTrim.[fk_wafer]"
        ",Wafers.Frequency"
        ",IonTrim.[run]"
        ",IonTrim.[a]"
        ",IonTrim.[b]"
        ",IonTrim.[c]"
        ",IonTrim.[m]"
        ",IonTrim.[n]"
        ",IonTrim.[rsqd]"
        ",IonTrim.[created]"
        ",IonTrim.[updated]"
        "FROM [MES_af].[dbo].[IonTrim] INNER JOIN [MES_af].[dbo].[Wafers] "
        "ON IonTrim.fk_wafer = Wafers.id AND IonTrim.fk_wafer = '%s'" % waferid)

    df = pd.read_sql(sql, cnxn)
    return df

def get_wafer_info(waferid):
    
    cnxn = db_connect()
    cursor = cnxn.cursor()

    sql = (
            "SELECT "
            "WaferID, "
            "D8Number, "
            "Frequency "
            "FROM [MES_af].[dbo].[Wafers] "
            "WHERE WaferID = ?")


    cursor.execute(sql, waferid)
    for row in cursor.fetchall():
        print(row)


def insert_ibe (wafer, run, a, b, c):
    cnxn = db_connect()
    cursor = cnxn.cursor()

    sql = (
        'INSERT INTO [MES_af].[dbo].[IonTrim] ('
        '[fk_wafer]'
        ',[run]'
        ',[a]'
        ',[b]'
        ',[c]'
        ',[m]'
        ',[n]'
        ',[rsqd]'
        ',[created]'
        ',[updated])'
        'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)')
    values = (wafer, run, a, b, c, None, None, None, datetime.now(timezone('US/Pacific')), None)
    cursor.execute(sql, values)
    cnxn.commit()

def overwrite_ibe(wafer, run, a, b, c):
    cnxn = db_connect()
    cursor = cnxn.cursor()

    sql = (
        'UPDATE [MES_af].[dbo].[IonTrim] ' 
        'SET '
        '[a] = ?, '
        '[b] = ?, '
        '[c] = ?, '
        '[created] = ? '
        'WHERE '
        '[fk_wafer] = ? AND'
        '[run] = ?')
    values = (a, b, c, datetime.now(timezone('US/Pacific')), wafer, run)
    cursor.execute(sql, values)
    cnxn.commit()
    
def update_ibe(wafer, run, m, n, rsqd):
    cnxn = db_connect()
    cursor = cnxn.cursor()

    sql = (
        'UPDATE [MES_af].[dbo].[IonTrim] ' 
        'SET '
        '[m] = ?, '
        '[n] = ?, '
        '[rsqd] = ?, '
        '[updated] = ? '
        'WHERE '
        '[fk_wafer] = ? AND'
        '[run] = ?')
    values = (m, n, rsqd, datetime.now(timezone('US/Pacific')), wafer, run)
    cursor.execute(sql, values)
    cnxn.commit()