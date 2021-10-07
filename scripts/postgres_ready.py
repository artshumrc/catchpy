#!/usr/bin/python3
import sys
import os
import psycopg2

def main():
    print(os.environ.get('CATCHPY_DB_NAME'), os.environ.get('CATCHPY_DB_USER'), os.environ.get('CATCHPY_DB_HOST'), os.environ.get('CATCHPY_DB_PASSWORD'), os.environ.get('CATCHPY_DB_PORT'))
    try:
        conn = psycopg2.connect(
                dbname=os.environ.get('CATCHPY_DB_NAME'),
                user=os.environ.get('CATCHPY_DB_USER'),
                password=os.environ.get('CATCHPY_DB_PASSWORD'),
                host=os.environ.get('CATCHPY_DB_HOST'),
                port=os.environ.get('CATCHPY_DB_PORT'),
        )
        # create a cursor
        cur = conn.cursor()
        
	    # execute a statement
        print('PostgreSQL database version:')
        cur.execute('SELECT version()')

        # display the PostgreSQL database server version
        db_version = cur.fetchone()
        print(db_version)

        cur.close()
    # except psycopg2.OperationalError:
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        sys.exit(-1)
    sys.exit(0)

if __name__ == '__main__': 
    main()
