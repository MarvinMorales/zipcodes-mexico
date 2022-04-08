from flask import Flask
from flask_cors import CORS
from flask_sock import Sock
from itertools import groupby
import json
import os

app = Flask(__name__)
socket = Sock(app)
CORS(app)

dataBase = dict()
finalList = list()
accents = {"Ciudad de Mexico":"Ciudad de México", 
"Mexico":"México", "Michoacan":"Michoacán", 
"Nuevo Leon":"Nuevo León", "Queretaro":"Querétaro", 
"San Luis Potosi":"San Luis Potosí", "Yucatan":"Yucatán"}

def same_codes_filter(lst):
    for _, grp in groupby(lst, lambda d: (d['zipcode'])):
        yield list(grp)[0]

rootPath = os.path.join(os.getcwd(), 'data')
for file in os.listdir(rootPath):
    f = open(f'{rootPath}/{file}', 'r', encoding='utf-8')
    data = f.read().split("..")
    finalDat = [json.loads(x) for x in data]
    if file.split('.')[0] in accents:
        dataBase[accents[file.split('.')[0]]] = finalDat
    else: dataBase[file.split('.')[0]] = finalDat
    f.close()

@socket.route("/api/server/socket")
def communication_socket(ws):
    while True:
        response = json.loads(ws.receive())
        if response['type'] == "__REQUEST_ZIPCODE__":
            if 'code' in response and 'state' in response:
                lista = dataBase.get(response['state'])
                finalList = filter(lambda x: x['zipcode'].startswith(response['code']), lista)
                final_response = json.dumps({
                    'type': '__SERVER_RESP__', 
                    'payload': list(same_codes_filter(finalList))})
                ws.send(final_response)
            else: ws.send(json.dumps({"__ERROR__": "'state' and 'code' keys are required!"}))

        elif response['type'] == "__GET_STATES__":
            ws.send(json.dumps({'type': '__SERVER_RESP__', 'payload': list(dataBase.keys())}))

        elif response['type'] == "__GET_INFO_BY_CITY__":
            if 'state' in response:
                lista = dataBase.get(response['state'])
                final_response = json.dumps({'type': '__SERVER_RESP__', 'payload': lista})
            else: ws.send(json.dumps({"__ERROR__": "'state' key is required!"}))

        elif response['type'] == "__HELP__":
            ws.send(json.dumps({
                "type": "__SERVER_RESP__",
                "socket api version": "1.0.1",
                "description": "Types allowed to get especific data from database",
                "types": {
                    "__REQUEST_ZIPCODE__": {"keys": ["type[string]", "code[string]", "state[string]"]},
                    "__GET_STATES__": {"keys": ["type[string]"]},
                    "__GET_INFO_BY_CITY__": {"keys": ["type[string]", "state[string]"]},
                    "__HELP__": {"keys": ["type[string]"]},
                }
            }))

        else: ws.send(json.dumps({
            'type': '__TYPE_NOT_FOUND__', 
            'reason': 'wrong endpoint',
            'help': 'Send \'{"type": "__HELP__"}\'',
            'payload': None
        }))

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=8000)