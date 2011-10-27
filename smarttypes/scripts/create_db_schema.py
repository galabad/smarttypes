
import smarttypes
from smarttypes.config import *
from smarttypes.utils import time_utils

import psycopg2
from smarttypes.utils.postgres_handle import PostgresHandle
postgres_handle = PostgresHandle(smarttypes.connection_string)


"""
two main tables:
- twitter_user
- twitter_tweet

to preserve old networks (twitter_user), and to help scale (twitter_tweet)
postfix each table with year_weeknumber ('%Y_%U')
"""       

try:
    postgres_handle.execute_query("CREATE LANGUAGE plpgsql;", return_results=False)
    postgres_handle.connection.commit()
except psycopg2.ProgrammingError:
    postgres_handle.connection.rollback()
    pass    

ts_modifieddate = """
CREATE FUNCTION ts_modifieddate() RETURNS trigger
AS $$
BEGIN
    NEW.modifieddate = now();
    RETURN NEW;
END;
$$
LANGUAGE plpgsql;      
"""
postgres_handle.execute_query(ts_modifieddate, return_results=False)
postgres_handle.connection.commit()

twitter_user = """
create table twitter_user_%(postfix)s(
    createddate timestamp not null default now(),
    modifieddate timestamp not null default now(),
    
    twitter_id integer unique not null,
    screen_name text not null,
    twitter_account_created timestamp,
    protected boolean,
    
    time_zone text,
    lang text,
    location_name text,
    description text,
    url text,
    
    following_ids integer[],    
    following_count integer,
    followers_count integer,
    statuses_count integer,
    favourites_count integer,
    
    caused_an_error timestamp
);

CREATE TRIGGER twitter_user_modified_%(postfix)s BEFORE UPDATE
ON twitter_user_%(postfix)s FOR EACH ROW
EXECUTE PROCEDURE ts_modifieddate();
""" 
for year_week_st in time_utils.year_weeknum_strs(datetime.now(), 100):
    postgres_handle.execute_query(twitter_user % {'postfix':year_week_st}, return_results=False)
    postgres_handle.connection.commit()




