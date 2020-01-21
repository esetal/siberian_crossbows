# -*- coding: utf-8 -*-
__author__ = 'a.sekretov'
import requests
import logging
from redis import StrictRedis
from game_svc.utils.other import get_redis_statuses_unique_key
from game_svc.config.game_settings import SERVICE_STATE_UP, SERVICE_STATE_DOWN, SERVICE_STATE_MUMBLE, SERVICE_STATE_CORRUPTED
from datetime import datetime
from names import get_first_name, get_last_name
from random import randint, choice
import string
import re
from bs4 import BeautifulSoup
from pathlib import Path
import traceback

logger = logging.getLogger('checkers')
logger.propagate = False

PORT = "3000"
PROJ_DIR = str(Path(__file__).parent.absolute())

def svc1_checker(team_id, ip, flag, redis_conf):
    logger.info('Starting svc2_checker')

    redis_conn = StrictRedis(**redis_conf, charset="utf-8", decode_responses=True)

    # getting state from last run
    state_key = get_redis_statuses_unique_key(team_id=team_id, service_id=1)
    state = redis_conn.hgetall(state_key)

    last_flag = state.get("last_flag")
    flag_pushed = state.get("flag_pushed") == 'True'
    status = state.get("status")
    email = state.get("email")
    password = state.get("password")
    id_ = state.get("flag_at_id")

    # PUSH if flag is new (new round) or we didn't pushed in last try
    if last_flag != flag or not flag_pushed:
        logger.info('Pushing flag svc2_checker')
        name = get_first_name() + '-' + ''.join(choice(string.ascii_uppercase + string.digits) for _ in range(10))
        email = name + '@gmail.com'
        password = get_password(10)
        print("Name: " + name + " / Password: " + password)
        status, trace, id_ = push_flag(flag, ip, name, email, password)
        flag_pushed = status == SERVICE_STATE_UP

    # try pull if flag is pushed
    if flag_pushed:
        logger.info('Try to pull flag svc2_checker')
        #name = None
        status, trace = pull_flag(flag, ip, password, id_, email)

    # if PUSH is OK
    if status == SERVICE_STATE_UP:
        logger.info('Checking svc2_checker')

        public_name = get_first_name() + '-' + ''.join(choice(string.ascii_uppercase + string.digits) for _ in range(10)) + '-' + str(randint(1980,2002))
        public_email = public_name + '@gmail.com'
        
        print("Check - Name: " + public_name)

        status, trace = check_functionality(flag, ip, public_name, public_email, get_password(6))
        #status = SERVICE_STATE_UP
        #trace = 'ok'

    # state for checker, write whatever need. No strict format
    service_status = {'date': datetime.now().isoformat(),
                      'last_flag': flag,
                      'flag_pushed': flag_pushed,
                      'email': email,
                      'password': password,
                      'flag_at_id': id_}

    # saving full state
    redis_conn.hmset(state_key, service_status)

    # state for scoreboard, strict properties
    redis_conn.hset(state_key, 'status', status)
    redis_conn.hset(state_key, 'trace', trace)

    logger.info('Finishing svc2_checker')

    # return status for SLA calculation
    return status

def generate_str(length=10):
    """Generate a random string of fixed length."""
    letters = string.ascii_letters + string.digits
    return ''.join(choice(letters) for _ in range(length))

def get_password(size=16, chars=string.printable):
    return ''.join(choice(chars) for _ in range(size))

def push_flag(flag, ip, name, email, password):
    trace = ''
    status = None
    url = 'http://' + ip + ':' + PORT + '/'
    print("\n---------------------------------")
    print("Push flag to team: " + ip)
    s = requests.session()
    try:
        r = s.get(url+'users/sign_up')
    except Exception as e:
        print("Failed with " + str(e) + ' ' + traceback.format_exc())
        status = SERVICE_STATE_DOWN
        trace = 'Cant GET csrf token '
        return status, trace, None
    soup = BeautifulSoup(r.text, 'html.parser')
    try:
        csrf_token = soup.find('meta', {'name':'csrf-token'})['content']
        print(csrf_token)
    except Exception as e:
        print("Failed with " + str(e) + ' ' + traceback.format_exc())
        status = SERVICE_STATE_MUMBLE
        trace = 'Smth wrong with index page'
        return status,trace, None

    try:
        r = s.post(url + 'users', allow_redirects=False, data={
            'utf8': '✓',
            'authenticity_token': csrf_token,
            'user[name]': name,
            'user[email]': email,
            'user[password]': password,
            'user[password_confirmation]': password,
            'commit': 'Sign+up'}, timeout=4)
        print(r.request.body)
    except Exception as e:
        print("Failed with " + str(e) + ' ' + traceback.format_exc())
        status = SERVICE_STATE_DOWN
        trace = 'Cant send signup request'
        return status, trace, None

    try:
        session = r.cookies['_scm_session']
    except Exception as e:
        print("Failed with " + str(e) + ' ' + traceback.format_exc())
        status = SERVICE_STATE_MUMBLE
        trace = 'Smth wrong with signup response. Can\'t get session'
        return status, trace, None

    if r.status_code != 302 or not session:
        status = SERVICE_STATE_MUMBLE
        trace = 'Error in signup response. Can\'t register'
        return status, trace, None

    try:
        burp0_url = url + "crossbows"
        burp0_headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:70.0) Gecko/20100101 Firefox/70.0", "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", "Accept-Language": "ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3", "Accept-Encoding": "gzip, deflate", "Content-Type": "multipart/form-data; boundary=---------------------------240546899130750783984090322", "Connection": "close", "Upgrade-Insecure-Requests": "1"}
        burp0_data = "-----------------------------240546899130750783984090322\r\nContent-Disposition: form-data; name=\"utf8\"\r\n\r\n\xe2\x9c\x93\r\n-----------------------------240546899130750783984090322\r\nContent-Disposition: form-data; name=\"authenticity_token\"\r\n\r\n" + csrf_token + "\r\n-----------------------------240546899130750783984090322\r\nContent-Disposition: form-data; name=\"crossbow[title]\"\r\n\r\n" + generate_str(10) + "\r\n-----------------------------240546899130750783984090322\r\nContent-Disposition: form-data; name=\"crossbow[price]\"\r\n\r\n" + str(randint(1,10000)) + "\r\n-----------------------------240546899130750783984090322\r\nContent-Disposition: form-data; name=\"crossbow[model]\"\r\n\r\n" + generate_str(10) + "\r\n-----------------------------240546899130750783984090322\r\nContent-Disposition: form-data; name=\"crossbow[description]\"\r\n\r\n" + generate_str(10) + "\r\n-----------------------------240546899130750783984090322\r\nContent-Disposition: form-data; name=\"crossbow[brand]\"\r\n\r\nSelf-Made\r\n-----------------------------240546899130750783984090322\r\nContent-Disposition: form-data; name=\"crossbow[condition]\"\r\n\r\nExcellent\r\n-----------------------------240546899130750783984090322\r\nContent-Disposition: form-data; name=\"crossbow[secret]\"\r\n\r\n" + flag + "\r\n-----------------------------240546899130750783984090322\r\nContent-Disposition: form-data; name=\"crossbow[image]\"; filename=\"file.png\"\r\nContent-Type: image/png\r\n\r\n\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x003\x00\x00\x003\x08\x06\x00\x00\x00:\xa10*\x00\x00\x00\x04gAMA\x00\x00\xb1\x8f\x0b\xfca\x05\x00\x00\x00 cHRM\x00\x00z&\x00\x00\x80\x84\x00\x00\xfa\x00\x00\x00\x80\xe8\x00\x00u0\x00\x00\xea`\x00\x00:\x98\x00\x00\x17p\x9c\xbaQ<\x00\x00\x00\x06bKGD\x00\xff\x00\xff\x00\xff\xa0\xbd\xa7\x93\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\x07tIME\x07\xe3\x0b\x08\x11!$C\x18\xe2\x07\x00\x00\r3IDATh\xde\xedZ{\x8c\\\xe5u\xff\x9d\xf3}\xf7\xce\xcc\x9d\xc7\xce\xce\xda\xbb\xd8\xde5^c\xc7/\x0c\xd8@\x08\xd4\xad\x9c\xb28\xe5]R\x11\x8aH\xdb?J\x85\xaaFn\x9b\"\xd4V\x8d\"U\xad\x94\xa4\xa5\x91Z\xa5\x89\x08A\xa8\n\x16$\x8d\xa2\x16\xf2\xb01\x846-o0\x01\x1b\n\x18\xbf\xd6\xeb\xdd\xf5\xbegfg\xee\xdc\xfb}\xe7\xf4\x8f\xdd5(1\xeb]0\nT=\xccO3\x9a{\xef\xf9}\xbf{\x1e\xdf\xb9\x97\xfa\xfa\xb6\x13\xfeo\x98\xf2;\xbe\xd0G\x1d\xf9\x1d?\xe8G\x1d\xe7\xc8\xfc\xd2\x1d9\x1b\xf8\xff\xca([m-\xdd\xa8P\x91\x0f\x93\xb2v\xb1\xca$\xe5\xd5Z<\xf4\xe3L4\xf4b\xb7\x12\x19\x10\x1f\xaf\xad\xba\xaa\x11\xd4O\xfc\xb2\t\xc9\xa2\x94Q\x13j\xf7\xee\xfb\x94]\xdc\x0b\xe8\xbf\x93\xca\xa3$\xfe\xd2\xd2\xfe]\xcaa\x0e>SV\xb1\xd9Y\xcc\xc1g\xdaTl\x0ej2\x1f.e\x94\x8d\x06\xd5c<\xb1q\xad\xdax<\x07\xd5N\x00E\x85\xe6\x1e\x99\xdc\xc0\xdb\x8e\xbch\xda\xf2Y\x82w\xaal\x89d\x0eS\x95\xb0\xa0I\xb1\xc7\x93\xfa\x0fT\x9992g<\xa0\xf3\xd9\xc7\xb4\xbe\xb2\xf2)@\xef\x08\x0c\xe5\xcbQ\x90\x03\xc0\x07G\xe2\xbfZ\x1f\x1c\xb9C\x12\xabl\x13\x06\xe0g\x8f!\x00\x02 d\xd7\xdc\xb5\xec\xe97v\x1d\xeb\xdb\xfe\x81&\x9b\x05+\xd3\xecb\x05\xb0\x1a\xc0\r\x00\\.d\"\x82\x11\xd5\xcb\x15 Ux\x00F\x01\x07\x80g\x97H\x01\x18\x00/\x8clnG2\xbcO\xc3\xae-\x8a\xb7m\x8e0\xf6\xee}B\xb7m\xfb\x04\x88X\xc30 \"\xfa\xe0\x941\xb1\xc0g\xd4\x03\xf0\xa2Hk\xb1g\x02\xa4\x12Y\x8dBCQ\xc8>\x1f\xb2\xe0m2\x94\xcf\x18\xb1\x0c\xe43fkw%\xfc\xa3\x89\x86\xc3KG_f/H@\xfco\xabV\xad\x19\xd2\x9eK\xb6\x01\xd8z\xc9%\x9f\xd0\x9e\x9e\x1e\x10!v\xce\xe7\xce\x9d\xa3}\x8bTr\xc1\xca\xf8,+@\x06P\xe3E\x83\x89iG\x04pg[\x80(4\x04U\x06\x11\x03\nU0\x13\xd1\xf2\xf6@r\x01\x1b\x85^\x03\xe0:\x02\x9c*\x8c\xaa\xd6\xa0~\xdfxj\x86*D\xd7\xab\xea]\xa7\xa4\"\x1e\xb3\x96\x9e\xfe\xfa\xd7\xffy\xf4\xa1\x87v\xc1Z{\xf6\x95\tj\x02\x9f\xc1\x18\x80\x03 6\xca\xe1\xb9J\xb0\x02\x1c\x87j\xbd\xe5\xb5=\xf5\xb2\x0c\x807\x04%\"\xaa\xc5^ZN\xe6n%i9\xf5\xe5\xbcUQh\xc3VV\x0f\xb4\xa2j\xbe\xd5\x920\x0c_\x9b\x8b5U\xad\x01\xe8\xf1^\xf4\xd3\x9f\xfe\xcc\xe0\xce\x9d;\xc7\xfb\xfa\xb6/\x88\x10\xcdv\xcdg\xfc\xa3\xcbwi\xa1\xff?s\x9c\xd4s\xad\xf6u\xe7KP\xf8\x1e\x80B\x06\xad\xcf^\x11\xbd\xb9\xe7\xfb\x07\xe2\xcf'N\xbeh\x99\x92|\xc60\x11\x88\x89\x84fbFD\x95\xbb+Yw\xfd\xd6NVb}\xe4h\xfb\xd4\x89F\xc0a`\xffn\xe3\xa6M\xf7Xk\xcd\xb2s\xceA\x18\x06e\"\xbe\x9f\x886\xaa\xea\x9d\xbd\xbd\xab\xbfu\xf7\xdd_\xe2\xb3\xaa\x8c\x9d\x1e\xa6z\xf7\xaf4\xb3c\x87\x1b>S\x1e\x03\xd0\x02\x90i\"\x98\xfe\xcbGF\xab\x9b\xba\x0bM\x15u\xa2H3^\x99\x08\x00T\x00X\x05H\x04&\xf1\xca\x81!V\"eF\xd92\xac\xba\x84_\xb9\xfb\xee)\xdaP27=\xf0T\xf2\xfc?\xae\xc6\xa0(\"e\x00\xd9r\xb9\xb2 \xff\x16\x153\x00\xd46F\xc9\xe5X\x01\x1c\x03p\x1b\x80\x1cAo\xea\xeb\xeb\xbb+iT\x9f\x1c=\xf2\xf2\xd5D\x0c\x10\xd1lc\xae\x04\xc8\xe4\xb4\xfb\xdd\xd4\xc9\xef\xa5^\xf4\xbb\xcf\x0eKh\x19\x9b{!\x97\x9f\x13\xea\xa1\x13\x13\xbf\xf3\xea\xe6\xf6+\x99\xf0\xdc_|\xe6\xe2/|\xfc\xb7\xfe\x18<\x93\xc9\x00@\x1b\x8d\xe6B\xfd[\xb82oc\x9e\x01W#\n\x9eP\xd5\x0c\x80?\x01\xb0=\x8cJ\xcf.\xdf\xb8m/\xb1\xc1\xa3{v\x9f\xca\xbd+\xdbC\x80\xb0\r\n\x88*\x1d:\xd9\xe0\\`\xb0}}\x0b\xdde\xa2\xc1\xa1t\xad\xaa\xaeW\x90\x0b\xd2\x98\x9a\x8d\xa6\xaa\xca\xa9=J\xb1\xd8\xb6`\xff\xcc\xea\xd5\xab\x16\x143\xbf\x88\x1e\x00\x13@\x19U=X\xa9T\xa6{{{?\xde\xd1QY\xbde\xeb\xd67\xc6\x8e\x1c\xe0r\xce\xdc\x02\xe0Sm9\xfb\xab\xa5\x9c9\xaf\x901i>c4\xb4$ \xf2CS\t\x1a-\xe7\x0b!s\x94\x8f\xd2\xa9\x8e\xad\xd1\xf8\xc4\xd4\x96b\xb1\xd0o\xad}\x16\xc0O\x96-\xeb\xee\xe3\x8dW\x17\x123J\xef\xd86\xbf\xd7\xca\xab\x1b6l\x06\x80\xbb\x00|\x19\xc0\x0b\xc6\xd8+w}\xe3\xabi.\nw+\xb0\xad\xab\x14\xca\xb2R\xc0s\x05U\x01L\xc5^R\xaf\xf6\xa2\x9e\xc8\x9f\xbf<k\x86Zy}fj\x19\th\x0c\xc0'\x01\xbcBp\x8bYh\x9c\x8d\xfd\x0c\x9d\xfe\x16\xa8\xea\x90\xaa\xbe\xc4\xccG{z\xba/\xfa\xdc\x9f\xe1\xe2r1\x9f\xcb\x05\xac\xd9\x80\\h\xd9\x05\x86\x1cf\x089\xcb\xe4\x02C\xae\x95\x8a\x1b\x9b\xf6\xae\xd9J]\x9bm\xb96\x13k\xb1y|S4\xfc\xdc\xc5\xd9\x91\xfd\x9do\xdd\xfc#Y\xa8?gC\x19\xaa\xd7kz\xe1E\x97d\xbc\x93`\xc3\x86\xf5\x17\xe5r\xb9\x07\xbcKK\xcf<|_86p8\xd3^\x08\xa5\x92\xb7\x1c;q'\xab\x8eU\x15:S{l\xcb\xa9O\x9c\x98\xceR\xa8\x97\xae.\x92\x17\xb8\x97\x8f\xd5\x1a\xb5\xa67D\xf8\xb3\xb0:\xf1\xcd\xa95\x0b*\x1fgE\x19-W\x96\xd0\xee\xef\xfd\x8b\xbf\xf7\xdeo\xa6\x8d\xda\xa4x\x97\x16\xc5\xbb\x92\xb5\xd6\x06aH\xc6\x18\"\x02\x11\x88f?\x88\x00\"\x80D\x94Z^)\xf5B\xa4\x9e\x18\x9e\x01\x14\x88P$\xa2P3\xb4`\xff\xe6\x12\xc0\xfb\"\xf4\xe4\xee\xc7$\xca\x99[KY\xf3\x8f\x87^{\xe9Z7vx\xc5\xc9\xc3\xaf\xd2\x8au[\xb5\xf7\x82m\xe4Dtp\xe08\x9c@\xda\xf3\x86\xf2!k\xe2TDA\x93M'cuG\x89\x13m\xa5\xc0H-\xd5\\\xc8R\xccZS\xc8\x98\x1f\xae\xcc\xd4\x9f;\x11\xaeZ\x90\xef[\x19f#\x1d\x95\x10\xaa\xba\x02\x84m\xad\xb8\xb9el\xe0P8>x\x84\xa3\xb6\x0e^\xbar\xad\t\xa2vn\xc4\xa9I\x9d\xe7l\xc0\x9c\r\xd9\x18&C\x80\xf1^M+\x15\xd3H\xc4\x8cO;3\xd1\xf0\xc62\x99l@\x94\r\x08\xb5\xdc\xb2\xb9\xd4\xfc\xc1)\x13d\xb28\xf6\xda>3|\xf4\xe0g\x01\xdc\xd4\x96\xb3\xbfV\x8e\xecym\x91\x91\xae\xb6\x0cE\x19\x83\xd4\x89N\x0c\xf5\xb3Bti\xf7\x1a\xca\xb7uHu\xec$5Z\x0e'&S\x9dlzn9\xdd\x1b\xa7rh\xf9\x04\x886yU\xea]\x92\xd1\xb6\x9c\xe5Z\xcb\xcb\xd1\xd1\xd6\xba\xb0qr9\x89{\xcdGKe\xbe\r\xde\xa2g\x00s\xc1\xf6\xdc\x9e\x1fkT\x0c\r\x01\xb7\xa9bGh\xc9w\x95\x02\x84\x96Q\xc9[\x80\x80\xc1\xd7\x9fG\xb3\xe5\xb0\xee\xb2\x1dX\xc5\xd5\x18\x1dx\x0b\xc7^\tI\x92\xe2d5A#\x15\x00x,\x0c\xf8+ \xec\x98\x8a\xdd\xcd\xb9\x80\x83B\xd6\xa0#ou\xb8\x9a\xfe\x06\x01\xd7\x03\xfa\x08\xa7\xd3\xff\xaal<\xf9\xb3\xd8\x01\x9c\xb3\xeacx\xf2\xe1\x07\xa2B[\xf6|\x82FY\xcbE\x85j.`\x97\xb1\xac\x86\xc9\xc5nf\xb6\x10X#\x00\x906\xab2v\xe2\x107\xab\xe3\xae\xdc\xd9\xc3i\x9a\xf8\x13\xf5\x81\xd7\x1a\xc9t\x8b\x99\x06\xd28F\xa6\x18\x01\xaan\xce1\x9d\xb9\xa6\x03\x10\x00\xf0`\x03\xe5`\xde\x85_\xb42\xdf\xbd\xf7\x1eY\xb6$\xbbZE\xbe\x03\xa2%\x9d\xa5 (d\x8c\xb6\xe5\x0cW\n\x96[\xa9\xf2H-eU`i\xc9R6\xb0\\=\xf6\n\xfa_\xff\x19\x97\xbbz\xcc\x96\x1d\xbfm\xd8\x06\xcduc\xa3\x9f\xff\xe2_\xff\xed\xb3\xab\x96\xe4|\xab\n\xe4\x8b\x00f:l3\xeb\x93!\x82\x9c\xf2O\x04$\xe9|\x0b\xbfxeZ\x00\x08\n\x10\xe5\x88\x903Db\x99\xc0D\xb37\xe0\xec\xf9h\xf68\x05\xbcwH\x92\x14.M\x1c\xdb\xb0a\x83\xb0^,w\xe0\xf6\xdb\xff\xc0\xd8\xc0\xe8\xe3\x0f~\x03\x04x\x05j\x00\x02Ude\xb6\x18\x9d2\xe63*\xb3\xe8l\xf6\xb1\x10h\xcf\x07\xd4\x1e\x19\xa9DV:KV\xce)\x07B\x04\x19\x9cJd\xaa\xe9di1\xd0\xceb \xb5\xa6\xc8\xe0T*\xfd\xe3\x89\x1c\x1ema\xff\xc1\xe3\x07&\xc7G\xaf\x8f\xe3\xf8\xd6\xa3G\x8f~.\x97\xcb\xfe\xd4\x1a{\xcb\xb5\xb7\xfd!\x88\xcd\xf3\n\xba\xba\x9857\xd7b\xe4\xc4D\x8a\xe9\x96\xc8\\\xf7\r=\xa32\x8b\x9ehJyE\x1e\x96T\x03C\xc6\x1a\x98\xd0\xb2\xcdZ\xb6D\xb0q\xaa\xd6y5\x19K&\x13\x90\xf5\xaa6qb\xe3Tl#\x15\x9e\xacM\xc7_\xfb\xca\xdf\xbcp\xac\xbf\xffg\"\xb2\x12\xc0E\x00\xba\x1cY\xec\xef\xafM]\xb9\xbe\xf4\xc2\xe6\x15\xd1\xbe\xd4k\xdaL\xc58Q3\x9bj\r\xe8\xcc\xca,8f\x1e\xdb\xfb\x84\x9c\xdb\x91\xdd&*7\xb6\xe5leMg64\x0c\x97z\xd5\xd1zJD\xe4;\nVU\xe1'\x1aNU\x81\xe1j\"\xcdD8q\xfa(\x81\xf6\x12a *D\xae\xd9lJ`\xed?\x11\xd1\xf2\xe1\xe1\xe1h||\xfc\x1f\xfa\xfa\xfa\xfe\xe7)\x9f\xbf\xef\x9a\xe2\x8b\xc4PO\x80\x8c\xd4R?Rw`\x82\xe74A\x04\x079\x0b1#++!T\xe5\x02\x00w\xaa\xaa\xeb*\x05\x1cZ\xe2\xc1\xc9T\x1b\x89P{d\xa9=oM\xec\x04C\x93);Q\x8c\xd5\x9d\xd4c\xcf <C\xa0\xbf\xdft\xc5\x95H\xe2\x98\xdf|\xe3U\x8d\xe3\xf8\xdbQT\x02\x80/\x13\xd1\x9f\x02\xd8\x03\x95\xfb;\xf3\xac\x022D`Q\xb5\x13\r\x07\"05\xaa\xf2_?\xf8\x81\xf6]\xf5I\x82\xea\xe2\x95a6t\xb2\xff\x10&G\x06\xb7\x80\xa8\x120\xad\x03T-\x93\xc4\xa9\xc0\t\xc1\x1a\xd2(d\xf2\xaa2\xd1p\x948\x91z\xcb\xc3\x8b\n\x14\xfb\x880MD\x87\xfa\xc7ZX\xdbl\xf0\xccy\x99\xa2(\x82jI\x89\xaa\x07\x01\xfc\x07\x80ce\x1b\xff\xfa\xe3c\xdd\xd1\x86\xb0?\xb2\xe4\xd50\xc9\x92\x82\x85a\xea(eM\xdf\x9a\xce\\SG\x0e<_]sm#\x9c<\xfc\x0b\x0b>o\xd7\xfc\xe8\xa3?\x91\x8d\xbd]A\xa3:\xf9 \x80\x1bs!\xb7\x8aY\x93\x0b\x98\\\xa5\x10\xb0!\xe2\xa5E\xabQ\xc840\x99\xc8\xf1\x89\x96q\x0271\xedX\x15M\x007f\x8b\xe5\x9f\xaaw\xbar\xe3\x16/\xde\x9dfEM0\x83\xb4\x03\xc0\x83\xa4\xdef'_7\xec\x9a\xb6\x1c\xd9\xb4\x983A3\x11\x19\xa9\xa6\xa2\xc0\t\x10_\x95\x1b\x1a{s|\xf3\xf6\x9f\xdf\xb0\x9d\xbek\x0e\xc2\x0c\x06\xde<\xc0\xe7u\x15\x96\xb4\xa6kKB\xcbQ`\xc8X&c\x88\x84\x98TD\xc5\x8bj*\xaa\x89W\x15EC\x15#\xaa:\xaa\x8aQQ\x1dS\xd0\xf4\xd0\x91\xe1d\xf5\x85\x97\xb9\xd3\x13\x01\x01.\x05l\n`\x1a@UU\xebN\xd4\xa5^\xc5\x89\xaa\xf3\xaa^4\x9dM\xdbu\x00R\x18>}h\x9c6f~\xf4\xc3\xdd\xd2\xbb4\xd7-\xde\xdf\xc7D]\x1b\xba\xa3\xe5\x95\x82\xf5\x8d\x96H-\xf6*\x02\x9djz\xa8\xaa\xf4O\xb4\xe0D\r\x13=\x14\x85\xfcU\x101H@Dj\x8c=r\xcd\xef\xdfN\xc3G\x0f\xce\x93d\x88\x80\x9a\x02\xd1\x0bD\xbc\xa3\xd5\xa8\xb6\x8f\x8d\xd7\xefQ\x95u\xc3\xb5T\x98\x89\x89\xf0\xe4\xd2|x'3\x9ab2\x03o\xfd\xe6\xad\x14\xd4\x07\x17\x1c3P\xd1\x10\xc0z@\x97e\x03\xd6r\xce\x02\xeaL3\x11\xe3\xa0\xf0\xa2\xe4U\xb9\x91x\xb4\x9c\x02\xc0\xf8T\x03\xaf\x12\x13.\xbf\xea\x06\xa4i\x82z\xbd~\x06\"s\x182\xe0\xea\xc7\xf7?u\x80\x98;\xa0\xa7F\xbcs\xe3\xcc\xe9Z\xdc\xdc\x0f\xef\xd2\x15\x17\\xZ\"\xf3f3\"@\x15N\x01d4\xf6\xc3\xd5\x94\x8aY\xe3\x96\x14\x02\x9aN\xbc\xeb\x1fo\xb1\x13\x15U\xfa\x16A_'\xe2}G\xc6c\xf4\xf5m\xe7\xd1\xd1\x91\xf7\xb4\x9d\xd8r\xc3\x1d\xd8\xbf\xe7\xdbM\x97\xc4_\x02\xb0\x04\x80\xa7\x99\xf6\xe6P\xa1\xd2%\x95\xee\xb5\xe4\xd3d\xd1u\x06:\xd3JXU\x98\xa1j\xca\xa2)\x9d\xb74\x835\x9dY\x0b(\xc5\xa9p\xea5\x05\xf00@{\xd6]\xba\x8d\xd68\xb7\xa0)\xca\xbb\xe1\xc9\xb7^\xa6\xce\xf3.h\x02\xd8\x05\x00{\xf7>\x81\xd9\xe19\x00\xccKd~e\x98\xa6\xd5c\x0f\x80\x0e\x02\xb62aY#\x11\x19\x98L\xb4\x95J\x15\xa0\xa7\x01m\x12\xf3\xe8\xe0h\x8c\xb5\xce\xbd\xaf\xad\xf7\xcf!\x00\xd0Bg\xccsx\xdaY3\x11Qu\xec$\xea\x93\xe3&n\xd4\x02\x97$\xdf\x01p-\x11R\x00\x01@\xfb\x89\xf9\xaa|[e4\xccd\xa5c\xc5\xb9P\x91\xb3E\xe4\xbd\xe2\xe9\x9fi\xaa\xaa\x96::q\xd9\xb5\xb7\xb8L.\x9f\x02\x18\x070\xa2\x8a!U\x9cT\xd5\x11\"N\xf7\x1f\x1cpKV\xac\xfae\x139\xe5\xff\xbcO\x01\x88\x98\xa6F\x071r\xfc\xc8r\x15)\x80H\xa1\n\"N\xb2\x85b\xff\xaa\x8d[|\x9a\xb4\x16\x90\xad>P\"s\xa6\xf3\xf6f\xaa\xa2\xa5\x8e.*ut\x1d\x9f\x0b\xc8\xeb\xae\xbb\x1aD@\x1c\xc7\xf4!\"\x823*\xf3!\xc6\xd3\xd9G\xf2\xdd\x99w\xb3\x8f\xdc\xbb3\xf3\xd9GN\x99\xf9\x8c\xe6*6\x80S\x93\x90\x0f;\xbek\xcc\xfc/\xd4BcE\xe19\xd8%\x00\x00\x00%tEXtdate:create\x002019-11-08T17:33:36-05:00\x8b\xf5\"\x84\x00\x00\x00%tEXtdate:modify\x002019-11-08T17:33:36-05:00\xfa\xa8\x9a8\x00\x00\x00\x00IEND\xaeB`\x82\r\n-----------------------------240546899130750783984090322\r\nContent-Disposition: form-data; name=\"commit\"\r\n\r\nCreate Crossbow\r\n-----------------------------240546899130750783984090322--\r\n"
        r = s.post(burp0_url, headers=burp0_headers, data=burp0_data, timeout=5, allow_redirects=False)
        # r = s.post(url + 'crossbows', allow_redirects=False, data={
            # 'utf8': '✓',
            # 'authenticity_token': csrf_token,
            # 'crossbow[title]': generate_str(10),
            # 'crossbow[price]': randint(1,10000),
            # 'crossbow[model]': generate_str(length=10),
            # 'crossbow[description]': generate_str(length=10),
            # 'crossbow[brand]': generate_str(length=10),
            # 'crossbow[secret]': flag,
            # 'user[password_confirmation]': password,
            # 'commit': 'Create crossbow'},
            # files = {
                # f'{get_last_name()}': open(PROJ_DIR + '/file.png', 'rb').read()
            # },
             # timeout=5)
        # print('Send img request: ' + r.request.body)
        if r.status_code == 302:
            id_ = re.search(r'/crossbows/(\d+)', r.text).group(1)
            trace = 'push_flag ok'
            status = SERVICE_STATE_UP
            print('Push successful!')
            return status, trace, id_
        print(r.status_code, r)
    except Exception as e:
        print("Failed with " + str(e) + ' ' + traceback.format_exc())
        status = SERVICE_STATE_MUMBLE
        trace = 'Cant add crossbow'
        return status, trace, None



def pull_flag(flag, ip, password, id_, email):
    trace = ''
    status = None
    url = 'http://' + ip + ':' + PORT + '/'
    print("\n---------------------------------")
    print("Pull flag from team: " + ip)
    #print("Name: " + name + " / Password: " + password)
    s = requests.session()
    try:
        r = s.get(url)
    except Exception as e:
        print("Failed with " + str(e) + ' ' + traceback.format_exc())
        status = SERVICE_STATE_DOWN
        trace = 'Cant GET csrf token '
        return status, trace
    soup = BeautifulSoup(r.text, 'html.parser')
    try:
        # print('Sent with: ' + r.request.body)
        csrf_token = soup.find('meta', {'name':'csrf-token'})['content']
    except Exception as e:
        print("Failed with " + str(e) + ' ' + traceback.format_exc())
        status = SERVICE_STATE_MUMBLE
        trace = 'Smth wrong with index page'
        return status,trace

    try:
        r = s.post(url + 'users/sign_in', allow_redirects=False, data={
            'utf8': '✓',
            'authenticity_token': csrf_token,
            'user[email]': email,
            'user[password]': password,
            'commit': 'Log+in'}, timeout=4)
    except Exception as e:
        print("Failed with " + str(e) + ' ' + traceback.format_exc())
        status = SERVICE_STATE_DOWN
        trace = 'Cant send login request'
        return status, trace
    try:
        session = r.cookies['_scm_session']
    except Exception as e:
        print("Failed with " + str(e) + ' ' + traceback.format_exc())
        status = SERVICE_STATE_MUMBLE
        trace = 'Smth wrong with login response. Can\'t get session'
        return status, trace

    if r.status_code != 302 or not session:
        status = SERVICE_STATE_MUMBLE
        trace = 'Smth wrong with login response'
        return status, trace

    try:
        r = s.get(url + 'crossbows/' + id_, allow_redirects=False,  timeout=3)
    except Exception as e:
        print("Failed with " + str(e) + ' ' + traceback.format_exc())
        status = SERVICE_STATE_MUMBLE
        trace = 'Cant find crossbows'
        return status, trace

    if r.status_code != 200:
        print(f'At #{id_}: cannot find crossbow ({r})')
        status = SERVICE_STATE_MUMBLE
        trace = 'Cant find crossbows'
        return status, trace

    if not flag in r.text:
        status = SERVICE_STATE_CORRUPTED
        trace = 'Cant find flag'
        return status, trace

    status = SERVICE_STATE_UP
    trace = 'pull_flag ok'
    print('Pull successful!')

    return status, trace

def check_functionality(flag, ip, name, email, password):
    trace = ''
    status = None
    url = 'http://' + ip + ':' + PORT + '/'
    print("\n---------------------------------")
    print("Check register " + ip)
    s = requests.session()
    try:
        r = s.get(url)
    except Exception as e:
        print("Failed with " + str(e) + ' ' + traceback.format_exc())
        status = SERVICE_STATE_DOWN
        trace = 'Cant GET csrf token '
        return status, trace
    soup = BeautifulSoup(r.text, 'html.parser')
    try:
        csrf_token = soup.find('meta', {'name':'csrf-token'})['content']
    except Exception as e:
        print("Failed with " + str(e) + ' ' + traceback.format_exc())
        status = SERVICE_STATE_MUMBLE
        trace = 'Smth wrong with index page'
        return status,trace

    try:
        r = s.post(url + 'users', allow_redirects=False, data={
            'utf8': '✓',
            'authenticity_token': csrf_token,
            'user[name]': name,
            'user[email]': email,
            'user[password]': password,
            'user[password_confirmation]': password,
            'commit': 'Sign+up'}, timeout=4)
    except Exception as e:
        print("Failed with " + str(e) + ' ' + traceback.format_exc())
        status = SERVICE_STATE_DOWN
        trace = 'Cant send signup request'
        return status, trace

    try:
        r = s.get(url)
    except Exception as e:
        print("Failed with " + str(e) + ' ' + traceback.format_exc())
        status = SERVICE_STATE_DOWN
        trace = 'Cant GET csrf token '
        return status, trace
    soup = BeautifulSoup(r.text, 'html.parser')
    try:
        csrf_token = soup.find('meta', {'name':'csrf-token'})['content']
    except Exception as e:
        print("Failed with " + str(e) + ' ' + traceback.format_exc())
        status = SERVICE_STATE_MUMBLE
        trace = 'Smth wrong with index page'
        return status,trace

    try:
        r = s.post(url + 'users/sign_in', allow_redirects=False, data={
            'utf8': '✓',
            'authenticity_token': csrf_token,
            'user[email]': email,
            'user[password]': password,
            'commit': 'Log+in'}, timeout=4)
    except Exception as e:
        print("Failed with " + str(e) + ' ' + traceback.format_exc())
        status = SERVICE_STATE_DOWN
        trace = 'Cant send login request'
        return status, trace
    try:
        session = r.cookies['_scm_session']
    except Exception as e:
        print("Failed with " + str(e) + ' ' + traceback.format_exc())
        status = SERVICE_STATE_MUMBLE
        trace = 'Smth wrong with login response. Can\'t get session'
        return status, trace

    if r.status_code != 302 or not session:
        status = SERVICE_STATE_MUMBLE
        trace = 'Smth wrong with login response'
        return status, trace


    try:
        r = s.get(url)
    except Exception as e:
        print("Failed with " + str(e) + ' ' + traceback.format_exc())
        status = SERVICE_STATE_DOWN
        trace = 'Cant GET csrf token '
        return status, trace
    soup = BeautifulSoup(r.text, 'html.parser')
    try:
        csrf_token = soup.find('meta', {'name':'csrf-token'})['content']
    except Exception as e:
        print("Failed with " + str(e) + ' ' + traceback.format_exc())
        status = SERVICE_STATE_MUMBLE
        trace = 'Smth wrong with index page'
        return status,trace


    try:
        r = s.post(url + 'crossbows', allow_redirects=False, data={
            'utf8': '✓',
            'authenticity_token': csrf_token,
            'crossbow[title]': generate_str(10),
            'crossbow[price]': randint(1,10000),
            'crossbow[model]': generate_str(length=10),
            'crossbow[description]': generate_str(length=10),
            'crossbow[brand]': generate_str(length=10),
            'crossbow[secret]': flag,
            'user[password_confirmation]': password,
            'commit': 'Create crossbow'},
            files = {
                f'{get_last_name()}': open(PROJ_DIR + '/file.png', 'rb').read()
            },
             timeout=5)
        # print('Send img request: ' + r.request.body)
        id_ = re.search(r'/crossbows/(\d+)', r.text).group(1)

    except Exception as e:
        print("Failed with " + str(e) + ' ' + traceback.format_exc())
        status = SERVICE_STATE_MUMBLE
        trace = 'Cant add crossbow'
        return status, trace

    try:
        r = s.get(url)
    except Exception as e:
        print("Failed with " + str(e) + ' ' + traceback.format_exc())
        status = SERVICE_STATE_DOWN
        trace = 'Cant GET csrf token '
        return status, trace
    soup = BeautifulSoup(r.text, 'html.parser')
    try:
        csrf_token = soup.find('meta', {'name':'csrf-token'})['content']
    except Exception as e:
        print("Failed with " + str(e) + ' ' + traceback.format_exc())
        status = SERVICE_STATE_MUMBLE
        trace = 'Smth wrong with index page'
        return status,trace

    try:
        print("del")
        r = s.post(url + 'crossbows/' + id_, allow_redirects=False, data={
            '_method': 'delete',
            'authenticity_token': csrf_token},
             timeout=5)
        if r.status_code == 302:
            print('Checker ok')
            trace = 'check status ok'
            status = SERVICE_STATE_UP
            return status, trace

    except Exception as e:
        print("Failed with " + str(e) + ' ' + traceback.format_exc())
        status = SERVICE_STATE_MUMBLE
        trace = 'Cant delete crossbow'
        return status, trace
