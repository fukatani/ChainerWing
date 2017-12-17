# http://d.hatena.ne.jp/shi3z/20160309/1457480722

import datetime
import os
import time
from urllib.request import urlopen
from urllib.request import urlretrieve
from urllib.error import URLError
from urllib.error import HTTPError
import argparse
import random
from PIL import Image


def parse_arg():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data_dir', type=str, default='images')
    parser.add_argument('--num_of_categories', type=int, default=1)
    parser.add_argument('--num_of_pics', type=int, default=100)

    return parser.parse_args()


def safe_retrieve(url, output):
    try:
        urlretrieve(url, output)
    except HTTPError as e:
        print(e.reason)
        return False
    except URLError as e:
        print(e.reason)
        return False
    except IOError as e:
        print(e)
        return False
    except UnicodeEncodeError as e:
        print(e)
        return False
    return True


if __name__ == '__main__':
    # arguments
    args = parse_arg()

    if not os.path.isfile('words.txt'):
        print('retrieving word list')
        ret = safe_retrieve('http://image-net.org/archive/words.txt', 'words.txt')
        if not ret:
            exit(1)

    word_dict = {}
    for line in open('words.txt', 'r'):
        line = line.replace(',', '')
        line = line.split()
        assert len(line) >= 2
        word_dict[line[0]] = line[1]

    if not os.path.isfile('imagenet.synset.obtain_synset_list'):
        print('retrieving obtain_synset list')
        ret = safe_retrieve('http://www.image-net.org/api/text/imagenet.synset.obtain_synset_list',
                            'imagenet.synset.obtain_synset_list')
        if not ret:
            exit(1)

    ids = open('imagenet.synset.obtain_synset_list', 'r').read()
    ids = ids.split()
    random.shuffle(ids)

    if not os.path.isdir(args.data_dir):
        os.mkdir(args.data_dir)

    start_time = time.time()
    for category_index in range(args.num_of_categories):
        id = ids[category_index].rstrip()
        category = word_dict[id]
        if not category:
            continue
        category_path = os.path.join(args.data_dir, category)
        if not os.path.isdir(category_path):
            os.mkdir(category_path)
        print('{0} / {1} category: {2}'.format(category_index,
                                               args.num_of_categories,
                                               category))
        try:
            urls = urlopen("http://www.image-net.org/api/text/imagenet.synset.geturls?wnid="+id).read()
            urls = urls.split()
            if not urls:
                continue
            random.shuffle(urls)
            image_index = 0
            cnt = 0
            while cnt < args.num_of_pics and cnt < len(urls):
                url = urls[image_index]
                image_index += 1
                if image_index >= len(urls):
                    break
                print('{0} / {1} picture'.format(image_index, args.num_of_pics))
                print('from: ' + url.decode())
                filename = os.path.split(url)[1].decode('utf-8').replace("'", "")
                output = "%s/%s/%d_%s" % (args.data_dir, category,
                                          cnt, filename)
                if not safe_retrieve(url.decode(), output):
                    continue
                try:
                    img = Image.open(output)
                    size = os.path.getsize(output)
                    if size == 2051:  # flickr Error
                        os.remove(output)
                        continue
                except IOError:
                    os.remove(output)
                    continue
                cnt += 1
                consumpted_time = time.time() - start_time
                progress = image_index + category_index * args.num_of_pics
                progress = progress / args.num_of_categories / args.num_of_pics
                print('Progress: {} %'.format(progress * 100))
                estimated_time = consumpted_time / progress
                print('Estimated time to finish: {}'.format(datetime.timedelta(seconds=estimated_time)))
        except HTTPError as e:
            print(e.reason)
        except URLError as e:
            print(e.reason)
        except IOError as e:
            print(e)
        except UnicodeEncodeError as e:
            print(e)
