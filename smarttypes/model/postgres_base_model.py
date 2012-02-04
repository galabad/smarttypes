from datetime import datetime, timedelta

class PostgresBaseModel(object):
    
    def __init__(self, **kwargs):
        if 'postgres_handle' not in kwargs:
            raise Exception('Cant initialize a PostgresBaseModel object without a postgres_handle.')
        self.__dict__.update(kwargs)
        
    @property
    def insert_sql_str(self):
        qry = """
        insert into %(table_name)s (%(table_columns)s)
        values (%(place_holder)s)
        returning %(key_name)s;
        """
        place_holder = ','.join(['%%(%s)s' % x for x in self.table_columns])
        params = {'table_name':self.table_name,
                  'table_columns':','.join(self.table_columns),
                  'place_holder':place_holder,
                  'key_name':self.table_key,}
        return qry % params
    
    @property
    def update_sql_str(self):
        qry = """
        update %(table_name)s
        set %(place_holder)s
        where %(key_name)s = %(key_value)s
        returning %(key_name)s;
        """
        place_holder = ','.join(["%s = %%(%s)s" % (x,x) for x in self.table_columns])
        params = {'table_name':self.table_name,
                  'place_holder':place_holder,
                  'key_name':self.table_key,
                  'key_value':'%('+self.table_key+')s'}
        return qry % params
    
    def save(self):     
        key_value = getattr(self, self.table_key, None)
        if not self.get_by_id(key_value, self.postgres_handle):
            qry = self.insert_sql_str        
        else:
            qry = self.update_sql_str
        params = {self.table_key:key_value}
        for prop_name in self.table_columns:            
            params[prop_name] = getattr(self, prop_name, self.table_defaults.get(prop_name))
            setattr(self, prop_name, params[prop_name])
        results = self.postgres_handle.execute_query(qry, params, True, print_qry=False)
        if not key_value:
            setattr(self, self.table_key, results[0][self.table_key])
        return self
    
    @classmethod
    def get_by_id(cls, key_value, postgres_handle):
        qry = """
        select * 
        from %(table_name)s
        where %(key_name)s = %(key_value)s;
        """
        params = {'table_name':cls.table_name,
                         'key_name':cls.table_key,
                         'key_value':'%(key_value)s'}
        results = postgres_handle.execute_query(qry % params, {'key_value':key_value}, print_qry=False)
        if len(results) == 1:
            return cls(postgres_handle=postgres_handle, **results[0])
        else:
            return None
        
    @classmethod
    def get_by_ids(cls, key_values, postgres_handle):
        if not key_values: return []
        qry = """
        select * 
        from %(table_name)s
        where %(key_name)s in %(key_values)s;
        """
        params = {'table_name':cls.table_name,
                         'key_name':cls.table_key,
                         'key_values':'%(key_values)s'}
        results = postgres_handle.execute_query(qry % params, {'key_values':tuple(key_values)})
        return [cls(postgres_handle=postgres_handle, **x) for x in results]
    
    @classmethod
    def get_by_name_value(cls, name, value, postgres_handle):
        qry = """
        select * 
        from %(table_name)s
        where %(name)s = %(value)s;
        """
        params = {'table_name':cls.table_name,
                         'name':name,
                         'value':'%(value)s'}
        results = postgres_handle.execute_query(qry % params, {'value':value})
        return [cls(postgres_handle=postgres_handle, **x) for x in results]
    
    