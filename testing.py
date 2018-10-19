from PIL import Image,ImageChops
import cv2



#folder = 'C:\\Users\\mfran\\OneDrive\\Projects\\mf_traveler_20181013\\photos\\201712'
#jpegs = ['0dd9ea94585aa604b706865374fdb398',
#         '4e74fa7f388ca3595b9fd667b4171831',
#         '49ee503de28410000c5572894b74042b',
#         '55ff882f677c1546161a30281d765f9b',
#         '72a33eef2a1e7bf067caa5e3a5cf5a53',
#         '084aed846ed5aec93c104fa338f45003',
#         '093ca0371a27e1d85a54f60fd791ad2f',
#         '427e693b85b6c77ab0b67f620e872911',
#         '517af46177dfc9c3dde89d41e16c89d4',
#         '745dd0b68e4a04b501836a4e163ddecb',
#         '7462f18d3d4286832461a8c4127afef8',
#         'b0b85c08c505a4a6f34d3611946c0610',
#         'bcec0d4e0de4d9a62c72852476742b09',
#         'ec8679379563a4a37b29cca06cade8d8',
#         'fc4784103d9f12f8f571a705254c9608']

#originals = ['C:\\Users\\mfran\\OneDrive\\Projects\\mf_traveler_20181013\\photos\\201710\\679bac4580af9aa90675ebff9c3557ba.jpg',
#             'C:\\Users\\mfran\\OneDrive\\Projects\\mf_traveler_20181013\\photos\\201710\\186f6c86d7e1322449c9fa2e372bba30.jpg',
#             'C:\\Users\\mfran\\OneDrive\\Projects\\mf_traveler_20181013\\photos\\201710\\8931249e992b43d58cb0ed8aef4f49e1.jpg',
#             'C:\\Users\\mfran\\OneDrive\\Projects\\mf_traveler_20181013\\photos\\201711\\97bdc8a3f9dbcdb2448bb8a607476414.jpg',
#             'C:\\Users\\mfran\\OneDrive\\Projects\\mf_traveler_20181013\\photos\\201711\\2275fb334e38248f1145e96f2d73459e.jpg',
#             'C:\\Users\\mfran\\OneDrive\\Projects\\mf_traveler_20181013\\photos\\201711\\c0207446f8c820c9e732b41f99c8b124.jpg',
#             'C:\\Users\\mfran\\OneDrive\\Projects\\mf_traveler_20181013\\photos\\201803\\30a5c02d63f38d782e763e80f05c73e4.jpg',
#             'C:\\Users\\mfran\\OneDrive\\Projects\\mf_traveler_20181013\\photos\\201803\\b0b4e3a62805e5a3cc69cf7c614becd8.jpg',
#             'C:\\Users\\mfran\\OneDrive\\Projects\\mf_traveler_20181013\\photos\\201710\\3460de732760682c78711f5d30c6de14.jpg']

#duplicates = ['C:\\Users\\mfran\\OneDrive\\Projects\\mf_traveler_20181013\\photos\\201805\\27368e88d8f1fd1c428553088dd1dc0c.jpg',
#              'C:\\Users\\mfran\\OneDrive\\Projects\\mf_traveler_20181013\\photos\\201804\\40efcefe1d9e63b2079ecf07237f6f88.jpg',
#              'C:\\Users\\mfran\\OneDrive\\Projects\\mf_traveler_20181013\\photos\\201805\\63ffa61f6c03993965b9b03d4a9ca176.jpg',
#              'C:\\Users\\mfran\\OneDrive\\Projects\\mf_traveler_20181013\\photos\\201803\\394e87d09d69b75a35caa7c833032374.jpg',
#              'C:\\Users\\mfran\\OneDrive\\Projects\\mf_traveler_20181013\\photos\\201809\\dcb5ae39a50f7e3a7455af8b8675e904.jpg',
#              'C:\\Users\\mfran\\OneDrive\\Projects\\mf_traveler_20181013\\photos\\201808\\4a2fa6661b8c669b4873ee98ffa92b5d.jpg',
#              'C:\\Users\\mfran\\OneDrive\\Projects\\mf_traveler_20181013\\photos\\201803\\b0b4e3a62805e5a3cc69cf7c614becd8.jpg',
#              'C:\\Users\\mfran\\OneDrive\\Projects\\mf_traveler_20181013\\photos\\201803\\b15c81be85ed425868027f2842d9bd96.jpg',
#              'C:\\Users\\mfran\\OneDrive\\Projects\\mf_traveler_20181013\\photos\\201806\\09886b227876096367faa1b994e60d81.jpg']

#folder_save = 'C:\\Users\\mfran\\Desktop\\differences'
#for i in range(len(originals)):

#    #print('Photo {}'.format(i+1))

#    img1 = Image.open(originals[i]).resize((100,100))
#    img2 = Image.open(duplicates[i]).resize((100,100))

#    diff = ImageChops.difference(img1,img2)
    
#    img1.save('{}/output_{:02}_1.jpg'.format(folder_save,i))
#    img2.save('{}/output_{:02}_2.jpg'.format(folder_save,i))
#    diff.save('{}/output_{:02}_3.jpg'.format(folder_save,i))

    #n = 0
    #diff = 0
    #while (n < 100) & (diff < threshold): 
    #    diff = sum(ImageChops.difference(img1,img2).histogram()[0:n+1])/(10*10)
    #    n += 1
    
    #if diff >= threshold:
    #    print('Hit threshold at {}'.format(n-1))
    #else:
    #    print('Max diff after {} is {:0.03%}'.format(n,diff))


#class Template:
#    def __init__(self,img:Image):
#        self.image = img

#    def set_size(self,size):
#        return

#    def get_box(self,n):
#        return 

#class Pixelated:
#    def __init__(self,img:Image,n_boxes,box,reduce):
#        height_th = round(height/max(height,width)) * reduced
#        width_th = round(width/max(height,width)) * reduced
#        img.thumbnail((height_th,width_th),Image.ANTIALIAS)
#        img = img.crop(box)

#        self.height = img.height
#        self.width = img.width
#        self.pixels = img.load()

#    def compare_pixels(self,pixels):
#        distance = sum([Color(*self.pixels[i,j]).difference(Color(*pixels[i,j])) \
#                        for i in self.height for j in self.width])
#        return distance


#im = Image.open('C:/Users/mfran/OneDrive/Photos/mf_traveler/kitten.jpg')