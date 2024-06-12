import pandas as pd
import json
import time
import mini

users = {}

def add_user(exp, user):
    if user not in users:
        users[user] = {'exp': int(exp)}
    else:
        users[user]['exp'] = int(exp)

def get_df(user, df_name):
    if user in users:
        if df_name in users[user]:
            return users[user][df_name]
        else:
            return pd.DataFrame()
    else:
        return pd.DataFrame()
    
def load_df(user, df_name):
    df = pd.DataFrame()
    for i in mini.list_files('user-tabels', user, df_name):
        print(i)
        df = pd.concat([df, pd.read_excel(mini.presigned_get_object('user-tabels',f'{user}/{df_name}/{i}'))], ignore_index=True)
    df.replace([float('inf'), float('-inf'), float('nan')], 0, inplace=True)
    users[user][df_name] = df
    print(df)
    return df

def set_df(user, table, df):
    if user in users:
        users[user][table] = df
    else:
        users[user] = {'exp': None, table: df}

def remove_expired_users():
    current_time = int(time.time())
    expired_users = [user for user, data in users.items() if data['exp'] is not None and data['exp'] < current_time]
    for user in expired_users:
        del users[user]