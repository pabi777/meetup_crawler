from scraper import MeetUpScraper
from time import sleep
from selenium.webdriver.common.keys import Keys
from urllib.request import urlretrieve
import os
import datetime
import requests
from random import randint
from s3_upload import AwsS3
import json
from threading import Thread
from utils import *
from dbstaffs.db import Dbconnect
import shutil

class MainPages(MeetUpScraper):
    def __init__(self):
        super().__init__()
        self.dbconnect = Dbconnect()
        self.s3_bucket = AwsS3('operative-meetup')
        
    
    def set_url(self,url_id,url):
        self.url_id,self.url = url_id,url
        print(self.url_id,self.url)


    def about_scrape(self,url=None):
        grp_id = None
        try:
            #self.save_html
            self.driver.get(self.url)
            data_dict = {}
            if "about" in self.config:
                for key,value in self.config["about"].items():
                    try:
                        val = self.driver.find_element_by_xpath(value).text
                        data_dict.update({key:val})
                    except Exception as e:
                        print(e)
                        self.restart_db()
                data_dict.update({'url_id':self.url_id})
                result = self.dbconnect.query(f'''select * from Meetup_Group where name like '{data_dict["name"]}' ''')
                if not result:
                    grp_id = self.dbconnect.query(table='Meetup_Group',data = data_dict,op='insert',return_id=True,pk='group_id')    
                else:
                    q = f'''select group_id from meetup_group where url_id = (select url_id from meetup_url where url like '{self.url}') '''
                    grp_id = self.dbconnect.query(q)[0][0]
        except Exception as e:
            self.restart_db()
        finally:
            path = f'/tmp/dps/{grp_id}/about'
            if not os.path.exists(path):
                create_dirs(path)                
            self.save_html(self.url,path,filename=grp_id)
            return self.url_id

    def send_to_schedule_table(self,data_dict):
        data_dicty = data_dict.copy()
        for key in data_dict.keys():
            if key not in ['url','type','status','priority']:
                del data_dicty[key]
        data_dicty.update({'priority':randint(0,500)})
        self.dbconnect.query(table='Meetup_Schedule',data=data_dicty,op='insert')

    def get_all_members(self):
        if "members" in self.config:
            st = f"select url_id from Meetup_url where url like '{self.url}'"
            url_id = self.dbconnect.query(st)[0][0]
            page_no = 1
            while True:
                try:
                    
                    url = self.config["members"].format(self.url[::-1].split('/')[1][::-1],self.url[::-1].split('/')[1][::-1],page_no,self.url[::-1].split('/')[1][::-1])
                    self.driver.get(url)
                    sleep(1)
                    element = self.driver.find_element_by_xpath('//body//pre')
                    data = eval(element.text)
                    value = data["responses"][0]["value"]["value"]
                    if not value:
                        sleep(4)
                        break
                    #print(data,type(data))
                    page_no += 1
                    for v in value:
                        member_url = self.url+f'members/{v["id"]}/?showAllGroups=true#my-meetup-groups-list'
                        data_dict = {'url_id': url_id, 'url':member_url,'type':1,'status':1}
                        result = self.dbconnect.query(f"select * from Meetup_collection where url like '{member_url}'")
                        if not result:
                            self.dbconnect.query(table='Meetup_collection',data=data_dict,op='insert')
                except Exception as e:
                    print(e)
                    self.restart_db()

    def event_url_scrape(self,future = True):
        q = f'''select group_id from meetup_group where url_id = (select url_id from meetup_url where url like '{self.url}') '''
        grp_id = self.dbconnect.query(q)[0][0]
        if "event" in self.config:
            url = None
            if future:
                url = self.config['event']['future'].format(self.url[::-1].split('/')[1][::-1],self.url[::-1].split('/')[1][::-1].lower(),self.url[::-1].split('/')[1][::-1].lower())
            else:
                url = self.config['event']['past'].format(self.url[::-1].split('/')[1][::-1],self.url[::-1].split('/')[1][::-1].lower(),self.url[::-1].split('/')[1][::-1].lower())
            #print(url)
            self.driver.get(url)
            collection_data = {'url_id':self.url_id,'url':url,'type':2,'status':1}
            try:
                self.dbconnect.query(table='Meetup_collection',data = collection_data,op='insert')
            except Exception as e:
                self.restart_db()
                print(e)
            sleep(2)
            path = f'/tmp/dps/{grp_id}/events'
            if not os.path.exists(path):
                create_dirs(path)
            if future:
                suffix = '_future'
            else:
                suffix = '_past'
            #collect all file name
            dirs = traverseDir('events',search_term=suffix)
            #use regex to extract digits
            latest_file = get_latest_file(dirs)
            #check last future/past file's content if equal dont save.
            r = requests.get(url)
            html_content = r.text
            result = None
            if latest_file:
                result = comapre_file_contents(latest_file,html_content)
                print("compare result=========>",result)
            if result == False or not dirs:
                self.save_html(url,path,filename=grp_id,suffix = suffix,html_content = html_content)
            if future:
                print('Changing mode---------------------------------------------------')
                self.event_url_scrape(future=False)

    def get_profile_details(self,limit=None):
        try:
            q = 'select id,url_id,url from Meetup_collection where status = 1 and type = 1 order by created_at desc '
            if limit:
                q = q+f'limit {limit}'
            results = self.dbconnect.query(q)
            
            for collection_id,url_id,url in results:
                try:
                    q = f'select group_id from meetup_group where url_id={url_id}'
                    grp_id = self.dbconnect.query(q)[0][0]
                    print('grp_id',grp_id)
                    q = f'update Meetup_collection set status = 2 where id={collection_id}'
                    self.dbconnect.query(q,op='update')
                    max_id = self.dbconnect.query('select max(member_id) from Meetup_Members')[0][0]
                    if not max_id:
                        max_id = 1
                    else:
                        max_id+=1
                    self.driver.get(url)
                    #Invalid Page check
                    error_message = "The page you're looking for doesn't exist."
                    try:
                        got_message = self.driver.find_element_by_xpath("//div[@class='docSection']//h2").text
                    except:
                        got_message = ''
                    
                    exist = self.dbconnect.query(f'''select * from Meetup_Members where profile_url like '{url}' ''')
                    #print(got_message,error_message,got_message == error_message,'Exist',exist)
                    if got_message == error_message or exist:
                        continue 
                    data_dict = {'profile_url':url}
                    if "profile" in self.config:
                        for key,value in self.config["profile"].items():
                            try:
                                if key == "profile_pic_xpath":
                                    img = self.driver.find_element_by_xpath(value) 
                                    src = img.get_attribute('src')
                                    path = f'/tmp/dps/{grp_id}/profile/{max_id}'
                                    
                                    create_dirs(path)
                                    #t1 = Thread(target=self.create_dirs,args=(path,))
                                    #t1.start()
                                    
                                    # download the image
                                    img_filepath = path+f"/{max_id}.jpg"
                                    
                                    urlretrieve(src, img_filepath)
                                    #t2 = Thread(target=urlretrieve,args=(src, img_filepath),daemon=True)
                                    #t1.join()
                                    #t2.start()
                                    
                                    self.s3_bucket.upload_file(img_filepath,img_filepath)
                                    #t3 = Thread(target=self.s3_bucket.upload_file,args=(img_filepath,img_filepath))
                                    #t1.join()
                                    #t2.join()
                                    #t3.start()

                                    self.save_html(url,path,filename=max_id)
                                    #t4 = Thread(target=self.save_html,args=(url,path))
                                    #t1.join()
                                    #t2.join()
                                    #t3.join()
                                    #t4.start()

                                    data_dict.update({"profile_pic_path":img_filepath})
                                    continue
                                try:
                                    val = self.driver.find_elements_by_xpath(value)
                                except:
                                    continue
                                if len(val)>1:
                                    for v in val:
                                        if key not in data_dict:
                                            if '_links' in key:
                                                data_dict.update({key:[v.get_attribute("href")]})
                                            else:    
                                                data_dict.update({key:[v.text]})
                                        else:
                                            if '_links' in key:
                                                data_dict[key].append(v.get_attribute("href"))
                                            else:    
                                                data_dict[key].append(v.text)
                                    data_dict[key]=','.join(data_dict[key])
                                else:
                                    try:
                                        val = self.driver.find_element_by_xpath(value)           
                                        data_dict.update({key:val.text})
                                    except:
                                        data_dict.update({key:''})
                            except Exception as e:
                                self.restart_db()
                                print('Exception on getting value:',e)
                                #continue
                        print(data_dict)
                        exist = self.dbconnect.query(f'''select * from Meetup_Members where profile_url like '{data_dict['profile_url']}' ''')
                        if not exist:
                            member_id = self.dbconnect.query(table='Meetup_Members',data = data_dict,op='insert',return_id=True,pk='member_id')
                            print(grp_id,member_id)
                            self.dbconnect.query(table='meetup_member_in_group',data={'group_id':grp_id,'member_id':member_id},op='insert')
                            self.dbconnect.query(f'update Meetup_collection set status=3 where id={collection_id}',op='update')  
                        data_dict = {}
                except Exception as e:
                    #raise
                    print('Exception in inserting values in db:',e)
                    self.dbconnect.query(f'update Meetup_collection set status=4 where id={collection_id}',op='update')
                    self.restart_db()
        except Exception as e:
            #raise
            print('Most outer loop:',e)
            self.restart_db()

    def restart_db(self):
        self.dbconnect.closeconn()
        self.dbconnect = Dbconnect()
        
    def save_html(self,url,path,filename = '',suffix = '',html_content = None):
        try:
            if not html_content:
                r = requests.get(url)
                html_content = r.text
            if filename:
                html_file_path = f'{path}/{filename}'
            else:
                html_file_path = path+f"/{datetime.datetime.now()}"
            if suffix:
                html_file_path += suffix

            html_file_path += '.html'
            if not os.path.isfile(html_file_path):
                with open(html_file_path,'w') as txtf:
                    txtf.write(str(html_content))
            self.s3_bucket.upload_file(html_file_path,'dps'+html_file_path.split('dps')[1])
            shutil.rmtree(path)
        except Exception as e:
            print(e)
          
                 
    def event_scrape(self):
        event_id = None
        q = f'''select group_id from meetup_group where url_id = (select url_id from meetup_url where url like '{self.url}') '''
        grp_id = self.dbconnect.query(q)[0][0]
        event_urls = self.dbconnect.query('select id,url from Meetup_collection where type = 2 and status=1')        
        for collection_id,event_url in event_urls:
            self.driver.get(event_url)
            event_json_string = self.driver.find_element_by_xpath('//body//pre').text
            event_json = json.loads(event_json_string)
            #print(event_json)    
            if not event_json["responses"][0]["value"]:
                continue
            try:
                
                for event in event_json["responses"][0]["value"]:
                    self.dbconnect.query(f"update Meetup_collection set status = 2 where url like '{self.url}/events/{event['id']}/'",op = 'update')
                    event_type = 'offline'
                    if event["is_online_event"]:
                        event_type = 'online'
                    data_dict2 = {
                        'group_id': grp_id,
                        'event_title': event['name'],
                        'event_datetime': f"{event['local_date']} {event['local_time']}",
                        'event_type': event_type,
                        'details': event["plain_text_no_images_description"]
                        }
                    #print(data_dict2)
                    event_id = self.dbconnect.query(table='Meetup_Events',data = data_dict2,op='insert',return_id=True,pk='event_id')
                    #print(event_id)
                    self.dbconnect.query(f'update Meetup_collection set status=3 where id={collection_id}',op='update')
                    #self.get_attendees(event_json,event_id)
            except Exception as e:
                raise
                print(e)
                self.restart_db()
                self.dbconnect.query(f'update Meetup_collection set status=4 where id={collection_id}',op='update')
            
            try:    
                if "member" in event_json["responses"][0]["value"][0]["rsvp_sample"][0]:
                    #event_id = self.dbconnect.query('select max(event_id) from Meetup_Events')[0][0]
                    data = {'collection_id':collection_id,'event_id':event_id,'group_id':grp_id}
                    self.dbconnect.query(table='meetup_event_collection',data=data,op='insert')
                    #self.get_attendees(event_json,event_id,grp_id)
                    q = f'update Meetup_collection set status = 2 where id = {collection_id}' 
                    self.dbconnect.query(q,op='update')
            except:
                raise
                q = f'update Meetup_collection set status = 4 where id = {collection_id}' 
                self.dbconnect.query(q,op='update')
                

    def get_attendees(self): 
        print("entered get attendies")
        q = f'select collection_id,event_id,group_id from meetup_event_collection where collection_id in(select id from meetup_collection where type = 2 and status = 2 and url_id = {self.url_id})'
        print(q)
        res = self.dbconnect.query(q)
        print('1st res',res)
        if res:
            url_id = self.url_id
            print('url_id',url_id)
            for collection_id,event_id,group_id in res:
                try:
                    q = f'select url from meetup_collection where id = {collection_id}'
                    res = self.dbconnect.query(q)
                    print('2nd res',res)
                    if res:
                        event_url=res[0][0]
                    else:
                        continue 
                    self.driver.get(event_url)
                    event_json_string = self.driver.find_element_by_xpath('//body//pre').text
                    event_json = json.loads(event_json_string)
                       
                    if not event_json["responses"][0]["value"]:
                        print("empty Event")
                        continue
                    
                    for member_details in event_json["responses"][0]["value"][0]["rsvp_sample"]:
                        data_dict={
                            'url_id' : url_id,
                            'url': f"{self.url}members/{member_details['id']}/?showAllGroups=true#my-meetup-groups-list",
                            'type': 1,
                            'status' : 1
                        }
                        print(data_dict)
                        #if member is present in member table
                        q = f"select member_id from meetup_members where profile_url like '%members/{extract_id(data_dict['url'])}/%' "
                        member_id = self.dbconnect.query(q)
                        print('member_id=',member_id,f"%members/{extract_id(data_dict['url'])}/%")
                        if member_id:
                            member_id = member_id[0][0]
                            print('member_id',member_id,'member found in profile table')
                            data4 = {'event_id':event_id,'grp_id':group_id,'member_id':member_id}
                            if 'role' in member_details:
                                data4.update({'role_in_event':member_details['role']})
                            if 'event_context' in member_details:
                                if member_details["event_context"]["host"]:
                                    self.dbconnect.query(table='meetup_organizers',data={'event_id':event_id,'member_id':member_id},op='insert')
                            self.dbconnect.query(table='meetup_member_attends_event',data=data4,op='insert')                
                        else:
                            #if member not present in member table
                            print('data not found in profile table')
                            data5 = {'url_id': self.url_id,'url':data_dict['url'],'type':1,'status':1}
                            self.dbconnect.query(table='Meetup_collection',data=data5,op='insert')
                        
                        q = f'update Meetup_collection set status = 3 where id = {collection_id}' 
                        self.dbconnect.query(q,op='update')
                except Exception as e:
                    raise
                    q = f'update Meetup_collection set status = 4 where id = {collection_id}' 
                    self.dbconnect.query(q,op='update')
    

    def close_all(self):
        self.dbconnect.closeconn()
        self.driver.quit()

    def restart_all(self):
        self.dbconnect.closeconn()
        self.driver.quit()
        self.driver = self.get_new_driver()
        

            



if __name__ == "__main__":
    print('from __name__==__main__',traverseDir('events'))