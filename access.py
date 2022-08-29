import requests
#import datetime
import filecmp
import os
import io
import secret
from common import *

class IGAuthentications:
    # instagram API url
    insta_api = 'https://api.instagram.com/v1/'
    insta_media = 'users/self/media/recent/'
    endpoints = {'media': insta_api+insta_media}

    # instagram API authentication
    client_id = secret.ig_client_id
    client_secret = secret.ig_client_secret

    # instagram accounts with access
    access = secret.ig_access

    def get_endpoint(endpoint):
        return IGAuthentications.endpoints[endpoint]

    def get_token(username):
        token = {'access_token': IGAuthentications.access[username]}
        return token

class IGAccount:
    def __init__(self,username):
        self.username = username
        self.id = None
        self.urls = {'profile':{},
                     'images':{},
                     'videos':{}}
        self.endpoint = IGAuthentications.get_endpoint('media')
        self.parameters = IGAuthentications.get_token(self.username)

    def ping(self):
        # contact Instagram API and get urls
        ok = True
        jason = None
        print('Contacting Instagram API')
        # get profile image
        ok = self._get_profile()
        if ok:
            max_id = None
            print(' + recent media')
            while ok:
                # get rest of images
                max_id,ok = self._get_info(max_id)

    def _id(self,id):
        id = id.replace('_'+self.id,'')
        return id

    def _get_profile(self):
        # get basic information
        endpoint = IGAuthentications.get_endpoint('media')
        parameters = IGAuthentications.get_token(self.username)
        response = requests.get(endpoint,parameters)

        if not response.ok:
            print(' ...no response')
        else:
            print(' ...success')
            jason = response.json()
            print(' ...getting profile picture',end='')

            # set id and get profile picture if first pass
            if not self.id:
                self.id = jason['data'][0]['user']['id']
                profile_url = self._get_image_urls(jason['data'][0]['user'],self.id,'profile')

        return response.ok

    def _get_info(self,max_id):
        # get all images from a user
        endpoint = IGAuthentications.get_endpoint('media')
        parameters = IGAuthentications.get_token(self.username)

        # continue from next page
        if max_id:
            parameters['max_id'] = max_id

        response = requests.get(endpoint,parameters)

        ok = response.ok
        if ok:
            # collect media from recent posts
            jason = response.json()
            ok = len(jason['data']) > 0
            if ok:
                max_id = jason['data'][-1]['id']
                for j in jason['data']:
                    media = self._get_media_type(j)
                    self._get_image_urls(j[media],j['id'],media)
            
        return max_id,ok

    def _get_media_type(self,data):
        # returns if data is a carousel post or videos or images
        m = ''
        for m in ['carousel_media','videos','images']:
            if m in data:
                media = m
                break
        return media

    def _get_image_urls(self,data,id,media):
        if media == 'carousel_media':
            for c in data:
                media = self._get_media_type(c)
                self._get_image_urls(c[media],id,media)
        else:
            if id in self.urls[media]:
                n = len([u for u in self.urls[media] if '{}_'.format(id) in u]) + 1
                id = '{}_{}'.format(id,n)

            if media == 'profile':
                url = data['profile_picture']
            else:
                url = data['standard_resolution']['url']
            self.urls[media][id] = url

class IGDownloader:
    def __init__(self,ig_account:IGAccount,photos_path='',videos_path='',
                 profile_path='',download_path='downloads'):
        self.paths = {'profile':{'path':profile_path,'ext':'jpg'},
                      'images':{'path':photos_path,'ext':'jpg'},
                      'videos':{'path':videos_path,'ext':'mp4'}}
        self.download_path = download_path
        self.urls = ig_account.urls

    def _compare_files(self,url_content,files):
        # check if a file has already been downloaded to folder
        p = 0
        unique = True
        url_btye = io.BytesIO(url_content)
        while unique & (p < len(files)):
            file_byte = open(files[p])
            unique = (url_byte != file_byte)
            file_byte.close()

        return unique

    def download_media(self):
        # download files from urls
        print(' ...downloading new media')

        # check what videos already exists
        collect_profile = (self.paths['profile']['path'] is not False)
        collect_videos = (self.paths['videos']['path'] is not False)

        if collect_videos:
            videos = Common.find_files(self.paths['videos']['path'],[self.paths['videos']['path']])
        
        for media in self.urls:
            path = '{}/{}'.format(self.paths[media]['path'],self.download_path)
            if not os.path.isdir(path):
                os.makedirs(path)
            ext = self.paths[media]['ext']

            # get file naming
            for id in self.urls[media]: 
                url = self.urls[media][id]
                files = Common.find_files(path)
                save_name = '{}.{}'.format(id,ext)
                
                # check if already downloaded
                if '{}/{}'.format(path,save_name) not in files:
                    # save url image or video to folder
                    r = requests.get(url)

                    # if file is a video, check if it has already been downloaded
                    save_file = True

                    if collect_videos & (media == 'videos'):
                        save_file = self._compare_files(r.content,videos)

                    if save_file:
                        if (media == 'images') | ((media == 'videos') & collect_videos) | ((media == 'profile') & collect_profile):
                            save_path = '{}/{}.{}'.format(path,id,ext)
                            with open(save_path, 'wb') as f:  
                                f.write(r.content)