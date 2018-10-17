import requests
import datetime
import os
from io import BytesIO
from PIL import Image
from media import Photo,Video

class IGAuthentications:
    # instagram API url
    insta_api = 'https://api.instagram.com/v1/'
    insta_media = 'users/self/media/recent/'
    endpoints = {'media': insta_api+insta_media}

    # instagram API authentication
    client_id = 'ba506cf601104c82a1041d633411a772'
    client_secret = 'bd087ff44cdb455c8fe24a4cbbeb014e'

    # instagram accounts with access
    access = {'mf_traveler':'6269208265.ba506cf.9ee0d1dc151d4255aae6c368b0f9ff2d'}

    def get_endpoint(endpoint):
        return IGAuthentications.endpoints[endpoint]

    def get_token(username):
        token = {'access_token': IGAuthentications.access[username]}
        return token

class IGAccount:
    def __init__(self,username):
        self.username = username
        self.id = ''
        self.photos = {}

    def _id(self,id):
        id = id.replace('_'+self.id,'')
        return id

    def _get_media_from_url(self,url,id,folder):
        if id in self.photos:
            n = len([img for img in self.photos if '{}_'.format(id) in img]) + 1
            id = '{}_{}'.format(id,n)

        # turn a url into an image
        if len(url) > 0:
            url_get = requests.get(url)
            if '.jpg' in url:
                url_byte = BytesIO(url_get.content)
                img = Image.open(url_byte)
                self.photos[id] = {'photo':Photo(url,image=img),'folder':folder}
            elif '.mp4' in url:
                ig_video = Video(url)
                ig_photos = ig_video.get_photos()
                for photo in ig_photos:
                    self.photos['{}_{}'.format(id,ig_photos.index(photo))] = {'photo':photo,'folder':folder}

    def _get_media_from_json(self,jason,id,folder):
        if 'carousel_media' in jason:
            for carousel in jason['carousel_media']:
                self._get_media_from_json(carousel,id,folder)
        else:
            self._get_media_from_url(jason.get('videos',jason['images'])['standard_resolution']['url'],id,folder)

    def get_media(self):
        # get all images from a user
        endpoint = IGAuthentications.get_endpoint('media')
        parameters = IGAuthentications.get_token(self.username)

        print('Contacting Instagram API')
        response = requests.get(endpoint,parameters)

        if not response.ok:
            print(' ... no response')
        else:
            print(' ...success') 
            jason = response.json()
            print(' ...getting profile picture')
            self._get_media_from_url(jason['data'][0]['user']['profile_picture'],'profile','profile')
            
            self.id = jason['data'][0]['user']['id']

            print(' ...getting other media')
            page = 0
            while len(jason['data']) > 0:
                page += 1
                print(' page {}'.format(page))
                n = 0
                for j in jason['data']:
                    n += 1
                    print('  media {}'.format(n),end='\r')
                    date = datetime.date.fromtimestamp(int(j['created_time']))
                    folder = '{}{:02}'.format(date.year,date.month)
                    self._get_media_from_json(j,self._id(j['id']),folder)

                parameters.pop('max_id',None)
                parameters['max_id'] = jason['data'][-1]['id']

                response = requests.get(endpoint,parameters)
                jason = response.json()
            print()

        return self.photos

    def download_images(self,folder):
        print(' ...saving images')
        for id in self.photos:
            path = '{}/{}'.format(folder,self.photos[id]['folder'])
            if not os.path.isdir(path):
                os.makedirs(path)

            self.photos[id]['photo'].image.save('{}/{}.jpg'.format(path,id))


ig_user = IGAccount('mf_traveler')
photos = ig_user.get_media()
ig_user.download_images('C:\\Users\\mfran\\OneDrive\\Documents\\Job Hunt\\Product Presos')