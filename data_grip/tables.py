import pandas

class Table:  

    def __init__(self, filename):  
        self.df = pandas.read_excel(filename)
        self.df = self.df.head(20)
        print(self.df)
    # def display_count(self):  
    def get_rows(self):
        return self.df.dtypes.astype(str).to_dict()
    
    def get_table(self, n=10, pg=0):
        if n == 0 and pg == 0:
            data = self.df.to_dict('records')
            return data
        start_idx = pg * n
        end_idx = start_idx + n
        data = self.df.iloc[start_idx:end_idx].to_dict('records')
        return data
    
    def apply_operation(self, df, operation):
        key = operation['key']
        filter_condition = operation['filter']
        expression = operation['expression']
        value = operation['value']
        
        # Apply filter if present
        if filter_condition:
            if '@' in filter_condition:
                filter_str = filter_condition.replace('@', f"`{key}`")
            else:
                filter_str = f"`{key}` {filter_condition}"
            df = df.query(filter_str)
        
        # Apply expression if present
        if expression:
            if '@' in expression:
                expression_str = expression.replace('@', f"`{key}`")
            else:
                 expression_str = f"`{key}` {expression}"
            df[key] = df.eval(expression_str)
        
        # Apply value if present
        if value is not None:
            dtype = df[key].dtype  # Get the dtype of the column
            df[key] = df[key].apply(lambda x: dtype.type(value))
        
        # Process sub operations recursively
        sub_operations = operation['sub']
        if sub_operations:
            for sub_operation in sub_operations:
                df = self.apply_operation(df, dict(sub_operation))
        
        return df

    def use_filter(self, data):
        df = self.df.copy()  # Create a copy of the DataFrame to avoid modifying the original
        for operation in data:
            df = self.apply_operation(df, dict(operation))
        
        return df.to_dict('records')