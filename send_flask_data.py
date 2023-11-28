import requests
r = requests.post("http://bugs.python.org", data={'number': '12524', 'type': 'issue', 'action': 'show'})