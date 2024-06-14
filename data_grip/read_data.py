import pandas as pd
import json
import time
import mini
from multiprocessing import Manager
import redis

# manager = Manager()
# users = manager.dict()
redis_client = redis.StrictRedis(host='62.109.8.64', port=6377, db=0, decode_responses=True)
users = {}

def flush():
    redis_client.flushdb()

def add_user(exp, user):
    print(user)
    data = redis_client.hget("users", user)
    if not data:
        redis_client.hset("users", user, json.dumps({'exp': int(exp)}))
    else:
        jsonn = json.loads(data)
        jsonn['exp'] = int(exp)
        redis_client.hset("users", user, json.dumps(jsonn))
    print(data)

def get_user(user):
    return redis_client.hget("users", user)

def add_user_table(user, df_name, df):
    if user in users:
        users[user][df_name] = df
    else:
        users[user] = {df_name: df}


def get_user_table(user, df_name):
    if user in users:
        if df_name in users[user]:
            return users[user][df_name]
        else:
            return pd.DataFrame()
    else:
        return pd.DataFrame()

def get_df(user, df_name):
    data = redis_client.hget("df", f'{user}/{df_name}')
    if data:
        return pd.read_json(data)
    else:
        return pd.DataFrame()
    
def load_df(user, df_name):
    df = pd.DataFrame()
    print(users)
    for i in mini.list_files('user-tabels', user, df_name):
        print(i)
        df = pd.concat([df, pd.read_excel(mini.presigned_get_object('user-tabels',f'{user}/{df_name}/{i}'))], ignore_index=True)
    df.replace([float('inf'), float('-inf'), float('nan')], 0, inplace=True)

    redis_client.hset("df", f'{user}/{df_name}', df.to_json())
    print(df)
    return df

# def set_df(user, table, df):
#     if user in users:
#         users[user][table] = df
#     else:
#         users[user] = {'exp': None, table: df}

# def remove_expired_users():
#     current_time = int(time.time())
#     expired_users = [user for user, data in users.items() if data['exp'] is not None and data['exp'] < current_time]
#     for user in expired_users:
#         del users[user]