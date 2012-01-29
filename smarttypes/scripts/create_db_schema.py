
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

################################################
##twitter_user
################################################
twitter_user = """
create table twitter_user(
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

    following_count integer,
    followers_count integer,
    statuses_count integer,
    favourites_count integer,
    
    last_loaded_following_ids timestamp,
    caused_an_error timestamp
);
CREATE TRIGGER twitter_user_modified BEFORE UPDATE
ON twitter_user FOR EACH ROW
EXECUTE PROCEDURE ts_modifieddate();
"""
postgres_handle.execute_query(twitter_user, return_results=False)
postgres_handle.connection.commit()

################################################
##twitter_user_following
################################################
twitter_user_following = """
create table twitter_user_following_%(postfix)s(
    createddate timestamp not null default now(),
    modifieddate timestamp not null default now(),
    
    twitter_user_id text unique not null references twitter_user(id),
    following_ids text[] not null
);
CREATE TRIGGER twitter_user_following_modified_%(postfix)s BEFORE UPDATE
ON twitter_user_following_%(postfix)s FOR EACH ROW
EXECUTE PROCEDURE ts_modifieddate();
""" 
for year_week_st in time_utils.year_weeknum_strs(datetime.now(), 50):
    postgres_handle.execute_query(twitter_user_following % {'postfix':year_week_st}, return_results=False)
    postgres_handle.connection.commit()

################################################
##twitter_reduction
################################################    
twitter_reduction = """
create table twitter_reduction(
    createddate timestamp not null default now(),
    modifieddate timestamp not null default now(),
    
    id serial unique,
    root_user_id text not null references twitter_user(id),
    user_ids text[] not null,
    x_coordinates real[] not null,
    y_coordinates real[] not null,
    group_indices real[],
    group_scores real[]
);
CREATE TRIGGER twitter_reduction_modified BEFORE UPDATE
ON twitter_reduction FOR EACH ROW
EXECUTE PROCEDURE ts_modifieddate();  
"""
postgres_handle.execute_query(twitter_reduction, return_results=False)
postgres_handle.connection.commit()
    
################################################
##twitter_group
################################################    
twitter_group = """
create table twitter_group(
    createddate timestamp not null default now(),
    modifieddate timestamp not null default now(),

    id serial unique,
    reduction_id integer not null references twitter_reduction(id), 
    index integer not null,
    user_ids text[] not null,
    scores real[] not null,
    tag_cloud text[],
    unique (reduction_id, index)
);
CREATE TRIGGER twitter_group_modified BEFORE UPDATE
ON twitter_group FOR EACH ROW
EXECUTE PROCEDURE ts_modifieddate();  
"""
postgres_handle.execute_query(twitter_group, return_results=False)
postgres_handle.connection.commit()

################################################
##twitter_tweet
################################################
twitter_tweet = """
create table twitter_tweet_%(postfix)s(
    createddate timestamp not null default now(),
    modifieddate timestamp not null default now(),
    
    id text unique not null,
    author_id text not null references twitter_user(id),
    retweet_count integer not null default 0,
    tweet_text text
);
CREATE TRIGGER twitter_tweet_modified_%(postfix)s BEFORE UPDATE
ON twitter_tweet_%(postfix)s FOR EACH ROW
EXECUTE PROCEDURE ts_modifieddate();
""" 
for year_week_st in time_utils.year_weeknum_strs(datetime.now(), 50):
    postgres_handle.execute_query(twitter_tweet % {'postfix':year_week_st}, return_results=False)
    postgres_handle.connection.commit()

################################################
##twitter_credentials
################################################
twitter_credentials = """
create table twitter_credentials(
    createddate timestamp not null default now(),
    modifieddate timestamp not null default now(),

    access_key text unique not null,
    access_secret text unique not null,
    twitter_id text unique references twitter_user(id),
    email text
);
CREATE TRIGGER twitter_credentials_modified BEFORE UPDATE
ON twitter_credentials FOR EACH ROW
EXECUTE PROCEDURE ts_modifieddate();  
"""
postgres_handle.execute_query(twitter_credentials, return_results=False)
postgres_handle.connection.commit()

################################################
##twitter_session
################################################
twitter_session = """
create table twitter_session(
    createddate timestamp not null default now(),
    modifieddate timestamp not null default now(),

    request_key text unique not null,
    request_secret text unique not null,
    access_key text references twitter_credentials(access_key) on delete cascade
);
CREATE TRIGGER twitter_session_modified BEFORE UPDATE
ON twitter_session FOR EACH ROW
EXECUTE PROCEDURE ts_modifieddate();  
"""
postgres_handle.execute_query(twitter_session, return_results=False)
postgres_handle.connection.commit()







