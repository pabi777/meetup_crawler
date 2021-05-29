# meetup_crawler
Schedule Crawls Data from Meetup.com

# Export theses in env

## AWS Example Config

export BUCKET_NAME=<BUCKET_NAME>

export ID=<ID>

export SECRET=<SECRET>

export REGION=<REGION>
  
export OUTPUT=<OUTPUT>

## Postgresql Database Config

export HOST=<HOST>
  
export DATABASE=<DATABASE>
  
export USER=<USER>
  
export PASSWORD=<PASSWORD>

### How to run
  
Go to project Root folder.  
create virtualenv : python3 -m venv env \n
  activate it: source env/bin/acticate \n
  install requirements: pip3 install -r requirements.txt \n
  Run it and relax : python3 mainpage.py \n
