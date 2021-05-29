import psycopg2
#if __name__=='__main__':
#    from config import config
#else:
#    from .config import config
from psycopg2.extensions import AsIs
import os

class Dbconnect:
    def __init__(self,mode=None):
        """ Connect to the PostgreSQL database server """
        self.conn = None
        self.cur = None
        try:
            # read connection parameters
            #self.params = config()

            # connect to the PostgreSQL server
            print('Connecting to the PostgreSQL database...')
            self.conn = psycopg2.connect(
                host = os.environ.get('HOST', 'DEFAULT HOST'),
                database = os.environ.get('DATABASE', 'DEFAULT DATABASE'),
                user = os.environ.get('USER', 'DEFAULT USER'),
                password = os.environ.get('PASSWORD', 'DEFAULT PASSWORD')
            )
            
            # cselect * from meetup_urlreate a cursor
            self.cur = self.conn.cursor()
            
            # execute a statement
            print('PostgreSQL database version:')
            self.cur.execute('SELECT version()')

            # display the PostgreSQL database server version
            db_version = self.cur.fetchone()
            print(db_version)
        
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
        
    def query(self,string=None,table=None,data=None,op=None,return_id=False,pk=None):
       
        try:
            if op=='insert':
                columns = data.keys()
                values = [data[column] for column in columns]
                
                if pk:
                    insert_statement = 'insert into '+str(table)+' (%s) values %s RETURNING '+str(pk)
                    self.cur.execute(insert_statement, (AsIs(','.join(columns)), tuple(values)))
                    id_of_new_row = self.cur.fetchone()
                    while not isinstance(id_of_new_row,int):
                        id_of_new_row = id_of_new_row[0]
                    
                else:
                    insert_statement = 'insert into '+str(table)+' (%s) values %s'
                    self.cur.execute(insert_statement, (AsIs(','.join(columns)), tuple(values)))
                    #self.cur.mogrify(insert_statement, (AsIs(','.join(columns)), tuple(values)))
                    #self.cur.execute(string)
                self.cur.execute("commit")
                self.conn.commit
                if return_id and pk:
                    return id_of_new_row

            elif op=='delete' or op=='update':
                self.cur.execute(string)
                self.cur.execute("commit")
                self.conn.commit
            else :
                self.cur.execute(string)
                self.records=self.cur.fetchall()
                return self.records
        except Exception as e :
            raise
            print ("Error while connecting to Postgres: ", e)

    def safe_query(self,string,t=None,op=None,return_id=False,pk=None):
        print("Inside Safe Query")
        try:
            if t is not None:
                if pk:
                    self.cur.execute(string+f' RETURNING {pk}',t)
                    id_of_new_row = self.cur.fetchone()
                    while not isinstance(id_of_new_row,int):
                        id_of_new_row = id_of_new_row[0]  
                else:
                    self.cur.execute(string,t)
                self.cur.execute("commit")
                self.conn.commit
                if return_id and pk:
                    return id_of_new_row
                    
            elif op=='delete' or op=='update':
                self.cur.execute(string)
                self.cur.execute("commit")
                self.conn.commit
            else :
                self.cur.execute(string)
                self.records=self.cur.fetchall()
                return self.records
        except Exception as e :
            raise
            print ("Error while connecting to Postgres: ", e)
    
    def closeconn(self):
        self.conn.close()
        

if __name__=="__main__":
    # import datetime
    

    # dbconnect = Dbconnect()
    # q = f"update meetup_collection set last_crawled = '{str(datetime.datetime.now())}' where id=9"
    # dbconnect.query(q,op='update')
    data_dict = {'profile_url': 'h://meetup.com/Orlando-Tech-and-Beer/members/255696927/?showAllGroupsmy-meetup-groups-list', "name": "Nïck's G.", 'designation': '', 'location': 'Orlando, FL', 'member_since': 'May 31, 2018', 'introduction': 'delete koro', 'profile_pic_path': 'dps/23', 'group_links': 'SunBlock - Central Florida Blockchain Community'}
    # member_id = dbconnect.query(table='Meetup_Members',data = data_dict,op='insert',return_id=True,pk='member_id')
    # print(member_id)
    # dbconnect.closeconn()

  