from glob import iglob
import os
import re
import json

def traverseDir(folder,search_term = None):    
    if search_term:
        return [f for f in iglob(f'dps/**/{folder}/*.html' , recursive=True) if os.path.isfile(f) and search_term in f]
    else:
        return [f for f in iglob(f'dps/**/{folder}/*.html' , recursive=True) if os.path.isfile(f)]

def get_latest_file(dirs):
    dirs = sorted(dirs,reverse=True,key=lambda y: re.findall('[0-9]',y)[0])
    if dirs:
        return dirs[0]
    else:
        return None

def create_dirs(dirName):
    try:
        if not os.path.exists(dirName):
            os.makedirs(dirName)
            print("Directory " , dirName ,  " Created ")
        else:    
            print("Directory " , dirName ,  " already exists")
    except Exception as e:
        print(e)

def comapre_file_contents(file1,content2):
    with open(file1,'r') as f1:
        content1 = json.loads(f1.read())
        content2 = json.loads(content2)
        del content1['responses'][0]['meta']
        del content2['responses'][0]['meta']
        return content1 == content2

def extract_id(url):
    '''
        input -> meetup member's profile url,
        output -> id
    '''
    return url.split('members/')[1].split('/')[0]
    
if __name__=="__main__":
    contents = traverseDir('events','_past')
    print(contents)
    res = comapre_file_contents(contents[0],contents[1])
    print(res)
    #get_latest_file('events',typ = '_past')