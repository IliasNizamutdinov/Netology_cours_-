import requests
from pprint import pprint

import pyprind
import sys


token_vk = 'a67f00c673c3d4b12800dd0ba29579ec56d804f3c5f3bbcef5328d4b3981fa5987b951cf2c8d8b24b9abd'
token_ya = ''

class VkUser:
    url = 'https://api.vk.com/method/'
    def __init__(self,token,version):
        self.params = {
            'access_token': token,
            'v': version
        }
    def search_foto(self,owner_id,id_alboms):
        search_groups_url = self.url + 'photos.get'
        search_groups_params = {
              'owner_id': owner_id,
              'album_id': id_alboms,
              'extended': 1,
              'photo_sizes': 1,
              'count': 100,
              'rev': 0
            }
        req = requests.get(search_groups_url, params={**self.params, **search_groups_params}).json()
        return req
    def get_link(self,owner_id, count,id_alboms):
        list_return = []
        json_vk = self.search_foto(owner_id,id_alboms)
        json_vk = json_vk['response']['items']
        for pict_rec in json_vk:
            likes = pict_rec['likes']['count']
            list_size = pict_rec['sizes']
            list_size.reverse()  # самые большие в конце списка
            url = list_size[0]['url']
            size = int(list_size[0]['height']) * int(list_size[0]['width'])
            list_return.append({'size': size, 'likes': likes, 'url': url})
        list_return = sorted(list_return, key=lambda s: s['size'], reverse=True)
        return list_return[:count]
    def get_list_albom(self,owner_id):
        list_albom_url = self.url + 'photos.getAlbums'
        list_albom_params = {
              'owner_id': owner_id,
            }
        req = requests.get(list_albom_url, params={**self.params, **list_albom_params}).json()
        req = req['response']
        if req['count'] == 0: #альбомов нет
            return []
        else:
            list_return = []
            for albom in req['items']:
                size = albom['size']
                if size != 0:
                    list_return.append({'id':albom['id'],'title':albom['title']})
            return list_return
    def get_user_json(self,user_name):
        method_url = self.url + 'users.get'
        search_groups_params = {
              'user_ids': user_name,
            }
        req = requests.get(method_url, params={**self.params, **search_groups_params}).json()
        req = req['response']
        if len(req) == 0:
            return {'is_closed': True}
        else:
            return req[0]
    def get_user_first_name(self,user_json):
        return user_json['first_name']
    def get_user_last_name(self,user_json):
        return user_json['last_name']
    def get_user_id(self,user_json):
        return user_json['id']
class YandexUser:
    def __init__(self, token):
        self.token = token
    def _get_headers_(self):
        return {
            'Content-Type': 'application/json',
            'Authorization': 'OAuth {}'.format(self.token)
        }

    def create_folder(self, name_folder: str, host: str ):
        params = {"path": name_folder}
        resp = requests.put(host, headers = self._get_headers_(),params= params)
        return resp.status_code
    def download_file(self,link_file: str, host: str, path: str):
        params = {
            'url':link_file,
            'path': path
        }
        resp = requests.post(host, headers= self._get_headers_(),params=params)
        return resp.status_code
def main():
 list_return = []
 user_name = str(input("Введите id пользователя (вместе с id)  или короткое имя: "))

 vk_client = VkUser(token_vk,'5.131')
 user_json = vk_client.get_user_json(user_name)
 if user_json['is_closed'] != True: #профиль может быть закрыт
    user_id = vk_client.get_user_id(user_json)

    user_first_name = vk_client.get_user_first_name(user_json)
    user_last_name = vk_client.get_user_last_name(user_json)

    count_photos_input = input("Сколько фотографий сохранить? ")
    if count_photos_input.isnumeric():
        count_photos = int(count_photos_input)
        if count_photos == 0:
            count_photos = 5
    else:
        count_photos = 5  # если ввели 0, или ни чего не ввели, то по умолчанию 5 фото

    list_pict = vk_client.get_link(user_id,count_photos,'profile')

    print("***** Сохранение фотографий профиля *****")

    host_create = 'https://cloud-api.yandex.net/v1/disk/resources/'
    host_download = 'https://cloud-api.yandex.net/v1/disk/resources/upload'
    ya_client = YandexUser(token_ya)
    name_folder = f"{user_first_name} {user_last_name}"
    status_create = ya_client.create_folder(name_folder, host_create)

    if status_create == 201:
        bar = pyprind.ProgBar(len(list_pict),stream=sys.stdout)
        for pict in list_pict:
            status = ya_client.download_file(pict['url'],host_download,f"{name_folder}/{pict['likes']}.jpg")
            if status != 202:
                print(f"Не удалось загрузить картинку {pict['likes']}.jpg")
            else:
                list_return.append({'file_name': f"{pict['likes']}.jpg", 'size':'z'})
            bar.update()
        save_alboms = input("Сохранить фотографии из других альбомов (Y - сохранить)? ")
        if save_alboms == 'Y':
            list_albom = vk_client.get_list_albom(user_id)
            for albom in list_albom:
                title = albom['title']
                print(f"***** Сохранение фотографий альбома {title} *****")
                #создаем папку для альбома
                name_folder_albom = f"{user_first_name} {user_last_name}/{title}"
                status_create = ya_client.create_folder(name_folder_albom, host_create)
                if status_create == 201:
                    list_albom_pict = vk_client.get_link(user_id, count_photos, albom['id'])
                    bar = pyprind.ProgBar(len(list_albom_pict), stream=sys.stdout)
                    for pict in list_albom_pict:
                        status = ya_client.download_file(pict['url'], host_download, f"{name_folder_albom}/{pict['likes']}.jpg")
                        if status != 202:
                            print(f"Не удалось загрузить картинку {pict['likes']}.jpg")
                        else:
                            list_return.append({'file_name': f"{pict['likes']}.jpg", 'size': 'z'})
                        bar.update()

                else:
                    print(f"Не удалось создать каталог {name_folder_albom}")
    else:
        print(status_create)
        print("Не удалось создать каталог")
 else:
     print("Указанный профиль для вас закрыт, или его не существует!")
 return list_return

if __name__ == '__main__':
    if len(token_ya) == 0:
        print("Токен яндекса пустой")
    else:
        list = main()
        if len(list) != 0:
            pprint(list)
