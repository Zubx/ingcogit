import gspread
import pandas as pd
import requests
from oauth2client.service_account import ServiceAccountCredentials
import json

# Google Sheets API credentials
scopes = ['https://www.googleapis.com/auth/spreadsheets']
creds = ServiceAccountCredentials.from_json_keyfile_name('plexiform-dream-356203-0c93dbe2c11a.json', scopes)
gc = gspread.authorize(creds)

# Opening JSON file
f = open('secret.json')
  
# returns JSON object as 
# a dictionary
jsonpass = json.load(f)

jubelio = jsonpass["jubelio"][0]
#email_jub = (jubelio['email'])
#pass_jub = (jubelio['password'])

#jubelio credential
email = (jubelio['email'])
password = (jubelio['password'])
login = requests.post("https://api2-lb.jubelio.com/login", data={"email":email,"password":password}).json()
header = {"Authorization" : login['token']}

# ini untuk stok live
wbsl = gc.open_by_key('15mhxufZJaBMNtj7w92LQzYT0as6qVRj7Y8wFmPuhlwI')
wsstok = wbsl.worksheet('Data')
wsstokref = wbsl.worksheet('RefWH')
wspushtoimp = wbsl.worksheet('push_to_import_lounge')
wspushtoimpv2 = wbsl.worksheet('push_to_import_lounge_v2')

#ini untuk import-longue
wbim = gc.open_by_key('1OaPIV2yDbbbNeOzsoghF6vAXSC96xDElAIwPeVKDZ9Y')
wsstatus = wbim.worksheet('Internal_stok_status')
miqdadwsstatus = wbim.worksheet('Internal_stok_status_nospareparts')


###preparing the dataframe untuk update stok
dfstok_live = pd.DataFrame(columns=['item_id','item_code','item_name','location_id','location_code','available'])

### API Call untuk stok live jubelio
url_inventory = "https://api2-lb.jubelio.com/inventory/?pageSize=200"
stok_wh = []
page = 1
while True:
    discover_api = (url_inventory + f"&page={page}")
    #print("Requesting ", discover_api)
    new_response = requests.get(discover_api,headers=header).json()
    dataitem = new_response['data']

    #do we find any activities ?
    if len(dataitem) == 0:
      #if not, exit the loop
      break

    #if we did find acitivities, add them
    #to the list he, and move on next page
    stok_wh.extend(dataitem)
    page = page + 1

##### filling the dataframe from json parsing
for inventor in stok_wh:
   item_id = inventor['item_id']
   item_id = str(item_id)
   item_code = inventor['item_code']
   item_name = inventor['item_name']
   item_name = str(item_name).replace("&","")
   for nested in inventor['location_stocks']:
     location_id = nested['location_id']
     location_code = nested['location_code']
     available = nested['available']

     dfstok_live = dfstok_live.append({'item_id':item_id,'item_code':item_code,'item_name':item_name,'location_id':location_id,'location_code':location_code,'available':available}, ignore_index=True)

##store the dataframe in spreadsheet so it can be pivoted
dataToWrite = []
#convert panda dataframe ke satu data body, ignore kolom header
lofLists = dfstok_live.to_numpy().tolist()
#recall kolom header dari panda dataframe
colheaders = dfstok_live.columns.to_list()
#combine antara header dan data body
dataToWrite = [colheaders] + lofLists
#final push ke
wsstok.update("A1",dataToWrite)

### we need to clean the text value
stok_spreadsheets = gc.open_by_key('15mhxufZJaBMNtj7w92LQzYT0as6qVRj7Y8wFmPuhlwI')
stok_sheet_id = 0
batch_update= {
    # A list of updates to apply to the spreadsheet.
    # Requests will be applied in the order they are specified.
    # If any request is not valid, no requests will be applied.
    'requests': [
                {
            'findReplace' : {
                'find' : "'",
                'replacement' : "",
                "matchCase": False,
                "matchEntireCell": False,
                "searchByRegex": False,
                "includeFormulas": True,

                #cellrange
                "range" : {
                    "sheetId": stok_sheet_id
                }

            }
        }
    ],  # TODO: Update placeholder value.

    # TODO: Add desired entries to the request body.
}
stok_spreadsheets.batch_update(batch_update)

### after handled, take the data and save it in dataframe
############################################ untuk non spareparts dan sby dipisah ########################## M untuk request miqdad
mlistpushkeimport1 = []
mlistpushkeimport2 = []
mlistpushkeimport3 = []
mlistpushkeimport4 = []
#Stok Gudang Offline
mkolomstok = wspushtoimpv2.get('A2:G')
mdfkolomstok =  pd.DataFrame.from_records(mkolomstok[1:],columns=mkolomstok[0])
mlistpushkeimport1 = mdfkolomstok.to_numpy().tolist()  #ini list offline
#Stok gudang Online
mkolomonline = wspushtoimpv2.get('Q2:Q')
mdfkolomonline =  pd.DataFrame.from_records(mkolomonline[1:],columns=mkolomonline[0])
mlistpushkeimport2 = mdfkolomonline.to_numpy().tolist() #ini list online
#Stok gudang Buffer
mkolombuffer = wspushtoimpv2.get('AA2:AA')
mdfkolombuffer =  pd.DataFrame.from_records(mkolombuffer[1:],columns=mkolombuffer[0])
mlistpushkeimport3 = mdfkolombuffer.to_numpy().tolist() #ini list buffer
#Stok gudang Surabaya
mkolombuffer = wspushtoimpv2.get('AF2:AH')
mdfkolombuffer =  pd.DataFrame.from_records(mkolombuffer[1:],columns=mkolombuffer[0])
mlistpushkeimport4 = mdfkolombuffer.to_numpy().tolist() #ini list surabaya

### MIQDAD ###
#Push ke kolom A~G dulu alias Offline
miqdadwsstatus.update('A3',mlistpushkeimport1)
#Push ke kolom Surabaya
miqdadwsstatus.update('H3',mlistpushkeimport4)
#Push ke kolom H alias Online
miqdadwsstatus.update('K3',mlistpushkeimport2)
#push ke kolom I alias buffer
miqdadwsstatus.update('L3',mlistpushkeimport3)

#### clean text value in stoklive##
mstoklive_sheet_id = 461898158
mbatch_update1= {
    # A list of updates to apply to the spreadsheet.
    # Requests will be applied in the order they are specified.
    # If any request is not valid, no requests will be applied.
    'requests': [
                {
            'findReplace' : {
                'find' : "'",
                'replacement' : "",
                "matchCase": False,
                "matchEntireCell": False,
                "searchByRegex": False,
                "includeFormulas": True,

                #cellrange
                "range" : {
                    "sheetId": mstoklive_sheet_id,
                    "startRowIndex": 2,
                    "startColumnIndex": 2,
                    "endColumnIndex": 11
                }

            }
        }
    ],  # TODO: Update placeholder value.

    # TODO: Add desired entries to the request body.
}
wbim.batch_update(mbatch_update1)
