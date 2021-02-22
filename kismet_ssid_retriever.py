#!/usr/bin/env python
# This script queries Kismet Wireless Server for all clients that are associated with predefined SSIDs.
# The script goes on to store the data to a JSON file every time it runs.
# If a JSON file already exists, any new devices will trigger a pushover notification with the MAC address, manufacturer name and last time seen.
# This script assumes a pushover.net account is already setup.
# A file myPersonalAuthInfo.py file must exist in the same directory as this file configured with all the necessary parameters.
# By Efrain Ortiz
# Hereuco LLC
# https://github.com/netcoredor/WirelessNetworkMonitor

import requests
import json
import time
import datetime
import certifi
from myPersonalAuthInfo import *
pushoverAlert = 0

def main():
    # Set currentTime - 1 hour. This will be used to retrieve devices seen in the last hour.
    lastHour = int(time.time()) - 3600
    # The Kismet Server IP
    # PUSHOVER CONFIG
    pushoverUrl = "https://"+ pushoverServer +"/1/messages.json"
    pushoverHeaders = {'Content-Type': 'application/x-www-form-urlencoded'}
    url = "http://" + kismetUsername + ":" + kismetPassword + "@" + kismetServer + ":2501/session/check_session"
    # Set empty headers and payload for authentication request
    payload={}
    headers = {}
    authResponse = requests.request("GET", url, headers=headers, data=payload)
    # set kismetCookie to Set-Cookie response in header from Kismet Wireless server. The Set-Cookie response contains two values seperated by a ;, so we split it up and grab the first value.
    kismetCookie = str((authResponse.headers['Set-Cookie'].split(";"))[0])
    # set to 1 if you wish to use pushover.net for pushing notificationsf to your phone.
    # The SSID(s) to monitor
    def AlertNew(newDevice):
        for i,each in enumerate(logs):
            if  each['kismet.device.base.type'] not in ['Wi-Fi Bridged', 'Wi-Fi AP'] and str(each['kismet.device.base.commonname']) == str(newDevice):
                message = 'Device ' + str(each['kismet.device.base.manuf']) + ' with MAC addresss ' + str(each['kismet.device.base.macaddr']) + ' found. Last connected at ' + datetime.datetime.utcfromtimestamp(each['kismet.device.base.last_time']).isoformat()
                payload ='token='+ pushoverToken +'&user='+ pushoverUser +'&device='+ pushoverDevice +'&title=NewDevice&message=' + str(message)
                response = requests.request("POST", pushoverUrl, headers=pushoverHeaders, data=payload)
    # try to open JSON file with all the clients. If the file is non-existant it flags an exception and loads a basic SSID map with the home network SSIDs
    try:
        incomingSSID_to_Client_Map = open('SSID_to_Client_Map.json','r')
        SSID_to_Client_Map = json.load(incomingSSID_to_Client_Map)
        incomingSSID_to_Client_Map.close()
        # Check to see if any of the SSIDs of interest are greater than 0, if so enable alerting. If not, assumption that its a new data collection.
        for items in SSID_to_Client_Map:
            if len(items) > 0:
                pushoverAlert = 1
    except:
        print('No existing SSID map file. Will create and save all associted clients.')
        SSID_to_Client_Map = {'SSIDUno': [], 'SSIDNI': [], 'SSIDSan': [], 'SSIDFour': []}
        pushoverAlert = 0
    # create device request endpoint with dynamically created epoch timestamp of current time minus 60 minutes
    getDevicesUrl = "http://" + kismetServer + ":2501/devices/last-time/"+ str(lastHour) +"/devices.json"
    getDevicesPayload = {}
    getDevicesHeaders = {
    'Content-Type': 'application/x-www-form-urlencoded',
    'charset': 'utf-8',
    'Cookie': kismetCookie
    }
    #Retrieve list of all devices for the last 60 minutes.
    deviceResponse = requests.request("GET", getDevicesUrl, headers=getDevicesHeaders, data=getDevicesPayload)
    #Convert the new line json file to a proper json for handkling in memory in python
    logs = json.loads(deviceResponse.text.replace("\n",","))
    # Loop through every log but only look for Access Points that are in out SSID_to_Client_Map and that have clients associated.
    # If a client is not already in the SSID_to_Client_Map and pushoverAlert = 1 then it sends a message using pushover.net
    for i,each in enumerate(logs):
        if each['kismet.device.base.type'] == 'Wi-Fi AP' and each['kismet.device.base.commonname'] in list(SSID_to_Client_Map) and bool('dot11.device.associated_client_map' in list(each['dot11.device'])):
            for client in each['dot11.device']['dot11.device.associated_client_map']:
                if client not in SSID_to_Client_Map[each['kismet.device.base.commonname']]:
                    SSID_to_Client_Map[each['kismet.device.base.commonname']].append(str(client))
                    if pushoverAlert == 1:
                        AlertNew(client)
                        #print('pushing to pushover.net')
    # Open a new file to store the updated data.
    newSSID_to_Client_Map = open('SSID_to_Client_Map.json','w')
    # Save the SSID_to_Client_Map data in json format to the newSSID_to_Client_Map handle
    print('Saving all entries, including any new deltas to JSON file.')
    newSSID_to_Client_Map.write(json.dumps(SSID_to_Client_Map,indent=4))
    # Close the file handle.
    newSSID_to_Client_Map.close()

if __name__ == "__main__":
    main()