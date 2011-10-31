
import smarttypes
from smarttypes.config import *
from smarttypes.utils import time_utils

from datetime import datetime
import psycopg2
from smarttypes.utils.postgres_handle import PostgresHandle
postgres_handle = PostgresHandle(smarttypes.connection_string)


try:
    postgres_handle.execute_query("CREATE LANGUAGE plpgsql;", return_results=False)
    postgres_handle.connection.commit()
except psycopg2.ProgrammingError:
    postgres_handle.connection.rollback()
    pass    

ts_modifieddate = """
CREATE OR REPLACE FUNCTION ts_modifieddate() RETURNS trigger
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
    
    id text unique not null,
    screen_name text not null,
    twitter_account_created timestamp,
    protected boolean,
    
    time_zone text,
    lang text,
    location_name text,
    description text,
    url text,
    
    following_ids text[],    
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

twitter_tweet = """
create table twitter_tweet_%(postfix)s(
    createddate timestamp not null default now(),
    modifieddate timestamp not null default now(),
    
    id text unique not null,
    author_id text not null,
    retweet_count integer not null default 0,
    tweet_text text
);
CREATE TRIGGER twitter_tweet_modified_%(postfix)s BEFORE UPDATE
ON twitter_tweet_%(postfix)s FOR EACH ROW
EXECUTE PROCEDURE ts_modifieddate();
""" 

for year_week_st in time_utils.year_weeknum_strs(datetime.now(), 100):
    postgres_handle.execute_query(twitter_user % {'postfix':year_week_st}, return_results=False)
    postgres_handle.execute_query(twitter_tweet % {'postfix':year_week_st}, return_results=False)
    postgres_handle.connection.commit()

twitter_credentials = """
create table twitter_credentials(
    createddate timestamp not null default now(),
    modifieddate timestamp not null default now(),

    access_key text unique not null,
    access_secret text unique not null,
    twitter_id text unique,
    email text
);
CREATE TRIGGER twitter_credentials_modified BEFORE UPDATE
ON twitter_credentials FOR EACH ROW
EXECUTE PROCEDURE ts_modifieddate();  
"""
postgres_handle.execute_query(twitter_credentials, return_results=False)
postgres_handle.connection.commit()

twitter_session = """
create table twitter_session(
    createddate timestamp not null default now(),
    modifieddate timestamp not null default now(),

    request_key text unique not null,
    request_secret text unique not null,
    access_key text,
    foreign key(access_key) references twitter_credentials(access_key) on delete cascade
);
CREATE TRIGGER twitter_session_modified BEFORE UPDATE
ON twitter_session FOR EACH ROW
EXECUTE PROCEDURE ts_modifieddate();  
"""
postgres_handle.execute_query(twitter_session, return_results=False)
postgres_handle.connection.commit()







