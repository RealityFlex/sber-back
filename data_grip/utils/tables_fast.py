import pandas as pd
import utils.mini_fast as mini
import utils.read_data_fast as read_data
import os
import asyncio

class Table:  

    def __init__(self):
        pass
        
    # async def init(self):
    #     self.base_df = await read_data.load_df("Default-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", "bills")
    #     print(self.base_df.head())
    #     print("Tables starting")

    # def display_count(self):  
    def get_rows(self, sub, df_name):
        df = pd.DataFrame()
        if len(mini.list_files('user-tabels',sub,df_name)) == 0: 
            df = self.base_df
        else:
            df = read_data.get_df(sub, df_name)
            if df.empty:
                df = read_data.load_df(sub, df_name)
        return df.dtypes.astype(str).to_dict()
    
    def get_table(self, sub, df_name, n=10, pg=0):
        df = pd.DataFrame()
        if len(mini.list_files('user-tabels',sub,df_name)) == 0:
            df = self.base_df
        else:
            df = read_data.get_df(sub, df_name)
            print("<<<")
            if df.empty:
                print(">>>")
                df = read_data.load_df(sub, df_name)
        if df.empty:
            return "Таблица не загружена"
        if n == 0 and pg == 0:
            os.makedirs(f"../data_tables/{sub}", exist_ok=True)
            df.to_excel(f"../data_tables/{sub}/{df_name}.xlsx")
            return "Таблица загружена"
        # start_idx = pg * n
        # end_idx = start_idx + n
        # print(n, pg, start_idx, end_idx)
        # data = df.iloc[start_idx:end_idx].to_dict('records')
        # return data
    
    def pre_load_table(self, sub, df_name, n=10, pg=0):
        df = pd.DataFrame()
        if len(mini.list_files('user-tabels',sub,df_name)) == 0:
            df = self.base_df
        else:
            df = read_data.get_df(sub, df_name)
            print("<<<")
            if df.empty:
                print(">>>")
                df = read_data.load_df(sub, df_name)
        read_data.add_user_table(sub,df_name,df)
    
    def apply_operation(self, df, column, operation):
        value = operation.get('value')
        filter_condition = operation.get('filter')
        expression = operation.get('expression')
        sub_operations = operation.get('sub')

        # Apply filter if present
        if filter_condition:
            filter_str = filter_condition.replace('@', f"`{column}`")
            df = df.query(filter_str)
        
        # Apply expression if present
        if expression:
            expression_str = expression.replace('@', f"`{column}`")
            df[column] = df.eval(expression_str)
        
        # Apply value if present
        if value is not None:
            dtype = df[column].dtype  # Get the dtype of the column
            df[column] = df[column].apply(lambda x: dtype.type(value))
        
        # Process sub operations recursively
        if sub_operations:
            for sub_operation in sub_operations:
                df = self.apply_operation(df, sub_operation)
        return df

    async def use_filter(self, data, sub, df_name='filter', df_real=None):
        df = df_real
        read_data.set_df(sub, df_name, pd.DataFrame())
        read_data.set_df(sub, df_name + "_edit", pd.DataFrame())
        try:
            for configuration in data:
                column = configuration['column']
                for operation in configuration['operations']:
                    df = self.apply_operation(df, column, operation)
        except Exception as e:
            print(e)
        read_data.set_df(sub, df_name, df)
        read_data.set_df(sub, df_name + "_edit", df)
        asyncio.create_task(read_data.save_df_to_minio(sub, df_name, df))
        return "data_saved"
    
    async def restore_table(sub, df_name):
        df_t = df_name + "_edit"
        read_data.set_df(sub, df_t, read_data.get_df(sub, df_name))
        
            # start_idx = pg * n
            # end_idx = start_idx + n
            # print(n, pg, start_idx, end_idx)
            # df = df.iloc[start_idx:end_idx]
            # return df.to_dict('records')