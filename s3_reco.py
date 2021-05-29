from s3_upload import AwsS3
from dbstaffs.db import Dbconnect

s3 = AwsS3('operative-meetup') 
dbconnect = Dbconnect()
q = 'select member_id from meetup_members'
results = dbconnect.query(q)
results = [ids[0] for ids in results]
allobj = s3.download_file(1)
print(allobj)


