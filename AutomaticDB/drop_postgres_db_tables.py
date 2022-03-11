#!/usr/bin/python
import psycopg2
from config_connection import config
 
def drop_postgres_db_tables(query):
    """ Connect to the PostgreSQL database server and execute query to drop existing tables """
    conn = None
    try:
        # read connection parameters
        params = config()
        # connect to the PostgreSQL server
        print('Connecting to the PostgreSQL database %s' % params['database'])
        with psycopg2.connect(**params) as conn:
            conn.autocommit=True
        # create a cursor
        cur = conn.cursor()
        # execute a statement
        query = query % params['user']
        print('Clearing All DB tables with sql command',query, ' !')
        cur.execute(query)
        
        """Loop to run query results to select only certain tables to drop"""
        #for i in range(len(dropped_tables)):
        
            #command = (str(dropped_tables[i][0]))
            #print(command)
            #cur.execute(command)
            #print(cur)
            #stat = cur.fetchone()
            #print(stat)
       
        # close the communication with the PostgreSQL
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
            print('Database connection closed.')
 
 
if __name__ == '__main__':
    """ Various SQL queries and commands to dropped selected tables:
    
    query_by_schema_table = 'SELECT '+ '\'drop table if exists ' + '\"\' || tablename || \'\"' + ' cascade;\'' + ' FROM pg_tables' + ' WHERE tableowner = \'%s\';'
    query_by_table_owner = 'select \'Drop OWNED BY \"%s\" cascade;\' FROM pg_tables;' 
    
    """
    command_by_table_owner = 'Drop OWNED BY \"%s\" cascade;' 
    drop_postgres_db_tables(command_by_table_owner)
    