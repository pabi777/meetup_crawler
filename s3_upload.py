import boto3, os
import datetime
from pathlib import Path
import boto3.session




class AwsS3(object):
    

    def __init__(self,bucket=None):
        super(AwsS3, self).__init__()
        self.bucket = os.environ.get('BUCKET_NAME', 'DEFAULT KEY')
        # Create your own session
        self.my_session = boto3.session.Session(
            aws_access_key_id = os.environ.get('ID', 'DEFAULT SEC'),
            aws_secret_access_key = os.environ.get('SECRET', 'DEFAULT SECRET'),
            region_name = os.environ.get('REGION', 'DEFAULT REGION')
            #output = os.environ.get('OUTPUT', 'DEFAULT KEY')
        )
        # Now we can create low-level clients or resource clients from our custom session
        #sqs = my_session.client('sqs')
        #s3 = my_session.resource('s3')
        print('bucket_name: ',self.bucket)
        
    def __enter__(self,*_):
        return self

    def __exit__(self,*_):
        pass

    def upload_file(self,local_path,s3_path):
        '''
        '''
        try:
            s3_path = 'dps'+s3_path.split('dps')[1]
            s3 = self.my_session.resource('s3')
            s3.meta.client.upload_file(local_path, self.bucket, s3_path)
            return True
        except Exception as e:
            print("error inside upload file bucket code:  "+str(e))
    
    def download_file(self,id):
        try:
            s3 = boto3.resource('s3')
            serverpath = f'dps/{id}/'
            my_bucket = s3.Bucket(self.bucket)
            return [my_bucket_object for my_bucket_object in my_bucket.objects.all()]
            
            #my_bucket = s3.Bucket(serverpath)
            #return my_bucket
            #localpath = str(Path().absolute())+'/htmls/'+str(id)+'profile.html'
            #print(serverpath+' '+localpath)
            #s3.meta.client.download_file(self.bucket, serverpath , localpath)
        except Exception as e:
            print(e)   


if __name__ == '__main__':
    aws = AwsS3()
    aws.upload_file('/home/pabi/Documents/meetupcrawler/dps/4.tar.xz','4.tar.xz')
