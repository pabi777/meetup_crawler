'''
url types:

profile link - 1
event link - 2

status type:

0 - dead link
1 - ready to be crawled
2 - crawling
3 - crawl done successfully
4 - crawl done with error
10 - need to crawl members of that event
'''
import datetime
from mainpage import MainPages
from dbstaffs.db import Dbconnect
from random import randint
from pyvirtualdisplay import Display
import sys

dbconnect = Dbconnect()


def set_queue(status = None):
    
    q = f'select url_id,url from meetup_url where status={status}'
    results = dbconnect.query(q)
    if not results:
        return None
    url_id = results[0][0] 
    if results:
        print(results)
        for url_id,url in results:
            try:  
                q = f'update meetup_url set status = 2 where url_id={url_id}'
                dbconnect.query(q,op='update')
                for i in range(1,7):
                    q = dbconnect.query(table = 'meetup_schedule',data = {'url':url,'type':i,'status':1,'priority':randint(0,100)} ,op='insert')
                
            except Exception as e:
                print(e)
                q = f'update meetup_url set status = 4 where url_id={url_id}'
                dbconnect.query(q,op='update')
    return url_id


def run_queue(mainPages,url_id=None):
    got_url_id = url_id
    final_url_id = None
    try:
        q = 'select schedule_id,url,type from meetup_schedule where schedule_id in(select schedule_id from meetup_schedule where status = 1 order by priority desc)order by type asc'
        results = dbconnect.query(q)
        for schedule_id,url,url_type in results:
            mainPages.set_url(url_id,url)
            if not got_url_id:
                q = f"select url_id from meetup_url where url like '{url}'"
                final_url_id = dbconnect.query(q)
                if final_url_id:
                    final_url_id = final_url_id [0][0]             
                print(url,dbconnect.query(q))
            try: 
                if url_type == 1:
                    q = f"update meetup_schedule set status = 2,crawl_start_time = '{str(datetime.datetime.now())}' where schedule_id={schedule_id}"
                    dbconnect.query(q,op='update')
                    print('About crawl')
                    final_url_id = mainPages.about_scrape()
                    print('final_url_id',final_url_id)
                elif url_type == 2:
                    q = f"update meetup_schedule set status = 2,crawl_start_time = '{str(datetime.datetime.now())}' where schedule_id={schedule_id}"
                    dbconnect.query(q,op='update')
                    print('Profile url Crawl')
                    mainPages.get_all_members()
                elif url_type == 3:
                    print('Profile Crawl')
                    q = f"update meetup_schedule set status = 2,crawl_start_time = '{str(datetime.datetime.now())}' where schedule_id={schedule_id}"
                    dbconnect.query(q,op='update')
                    mainPages.get_profile_details()
                elif url_type == 4:
                    print('Event url Crawl')
                    q = f"update meetup_schedule set status = 2,crawl_start_time = '{str(datetime.datetime.now())}' where schedule_id={schedule_id}"
                    dbconnect.query(q,op='update')
                    mainPages.event_url_scrape()
                elif url_type == 5:
                    print('event Crawl')
                    q = f"update meetup_schedule set status = 2,crawl_start_time = '{str(datetime.datetime.now())}' where schedule_id={schedule_id}"
                    dbconnect.query(q,op='update')
                    mainPages.event_scrape()
                elif url_type == 6:
                    print("members in a event crawl")
                    q = f"update meetup_schedule set status = 2,crawl_start_time = '{str(datetime.datetime.now())}' where schedule_id={schedule_id}"
                    dbconnect.query(q,op='update')
                    mainPages.get_attendees()

                

                q = f"update meetup_schedule set status = 3 where schedule_id={schedule_id}"
                dbconnect.query(q,op='update')
                
                q = f'update meetup_url set status = 3 where url_id={url_id}'
                dbconnect.query(q,op='update')
            except Exception as e:
                print(e)
                q = f'update meetup_schedule set status = 4 where schedule_id={schedule_id}'
                dbconnect.query(q,op='update')
                q = f'update meetup_url set status = 4 where url_id={url_id}'
                dbconnect.query(q,op='update')
            finally:
                q = f"update meetup_schedule set crawl_end_time = '{str(datetime.datetime.now())}' where schedule_id={schedule_id}"
                dbconnect.query(q,op='update')
    
    except Exception as e:
        print(e)
        q = f'update meetup_schedule set status = 4 where schedule_id={schedule_id}'
        dbconnect.query(q,op='update')
        q = f'update meetup_url set status = 4 where url_id={final_url_id}'
        dbconnect.query(q,op='update')

    
def reset_collection():
    dbconnect.query('update meetup_collection set status = 1',op='update')


#with Display() as disp:
    #reset_collection()
url_id = None
mainPages = None
try:
    mainPages = MainPages()
    while True:
        #check for ready to crawl url
        q = 'select url_id,url,status from meetup_url where status !=3'
        try:
            results = dbconnect.query(q)
        except Exception as e:
            print('Error at first from fetching url from meetup_schedule')
            results = []
        if results:
            
            for url_id,url,status in results:
                if status == 3:
                    continue
                if status == 1:
                    #mainPages.set_url(url_id,url)
                    urlid = set_queue(1)
                elif status == 4:
                    try:
                        if str(sys.argv[0])=='--fix-broken':
                            #mainPages.set_url(url_id,url)
                            q = 'update meetup_url set status = 1 where status status = 4'
                            dbconnect.query(q,op='update')
                            q = 'update meetup_schedule set status = 1 where status status = 4'
                            dbconnect.query(q,op='update')
                    except Exception as e:
                        print(e)
                run_queue(mainPages,url_id)
                
except:
    raise
finally:
    if mainPages:
        mainPages.close_all()
    dbconnect.closeconn()
    print("Closed all connection")















    # set_q=str(input("Press 1 for set queue,press 2 for reset last meetup url status:\n"))
    # if set_q=='1':
    #     status=int(input("set queue for status=?\n"))
    #     url_id = set_queue(status)
    # elif set_q=='2':
    #     dbconnect.query('update meetup_url set status=2 where url_id=(select max(url_id) from meetup_url)',op='update')
    #     dbconnect.query('update meetup_schedule set status=1 where url=(select url from meetup_url where url_id=(select max(url_id) from meetup_url))',op='update')
    # mainPages = MainPages()
    # while True:
    #     if url_id:
    #         run_queue(mainPages,url_id)
    #     url_id = set_queue(1)

