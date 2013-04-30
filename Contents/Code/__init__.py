from base64 import b64encode

####################################################################################################

PREFIX = '/applications/sabnzbd'

NAME          = 'SABnzbd+'
ART           = 'art-default.png'
ICON          = 'icon-default.png'

####################################################################################################

def Start():
    Plugin.AddViewGroup('InfoList', viewMode='InfoList', mediaType='items')

    ObjectContainer.art = R(ART)
    ObjectContainer.title1 = NAME
    ObjectContainer.view_group = 'InfoList'

    DirectoryObject.thumb = R(ICON)
    PopupDirectoryObject.thumb = R(ICON)

    HTTP.CacheTime = 1
    
####################################################################################################
@route(PREFIX + '/auth')
def AuthHeader():
    header = {}

    if Prefs['sabUser'] and Prefs['sabPass']:
        header = {'Authorization': 'Basic ' + b64encode(Prefs['sabUser'] + ':' + Prefs['sabPass'])}

    return header

####################################################################################################
@route(PREFIX + '/saburl')
def GetSabUrl():
    if Prefs['https']:
        url =  'https://%s:%s' % (Prefs['sabHost'], Prefs['sabPort'])
    else:
        url =  'http://%s:%s' % (Prefs['sabHost'], Prefs['sabPort'])
    return url

####################################################################################################
@route(PREFIX +'/apiurl')
def GetSabApiUrl(mode):
    if Dict['sabApiKey']:
        return GetSabUrl() + '/api?mode=%s&apikey=%s' % (mode, Dict['sabApiKey'])
    else:
        if ApiKey():
            return GetSabUrl() + '/api?mode=%s&apikey=%s' % (mode, Dict['sabApiKey'])
        else:
            Log("Unable to build without API Key.")

####################################################################################################
@route(PREFIX + '/apikey')
def ApiKey():
    try:
        url = GetSabUrl() + '/config/general'
        headers = AuthHeader()
        configPage = HTML.ElementFromURL(url, headers=headers)
        apiKey = configPage.xpath('//input[@id="apikey"]')[0].get('value')
        Dict['sabApiKey'] = apiKey
        Dict.Save()
        return True
    except:
        Log("Unable to retrieve API Key")
        return None

####################################################################################################
@route(PREFIX + '/apirequest')
def ApiRequest(mode):
    content = HTTP.Request(GetSabApiUrl(mode), errors='ignore', headers=AuthHeader()).content
    try:
        data = JSON.ObjectFromString(content)
    except:
        #not all API calls return a JSON response so we'll just return the plain text for those
        data = content
        
    return data
    
####################################################################################################
@route(PREFIX + '/validateprefs')
def ValidatePrefs():
    return
    
####################################################################################################
@route(PREFIX + '/error')
def SabError():
    return ObjectContainer(header=NAME, message='An error occurred. Your request did not succeed')

####################################################################################################
@handler(PREFIX, NAME, ART, ICON)
def MainMenu():
    oc = ObjectContainer(noCache=True)
    
    API_KEY = False
    
    try:
        if Dict['sabApiKey']:
            API_KEY = True
        else:
            Log('No API Key saved.')
            API_KEY = ApiKey()
    except:
        API_KEY = ApiKey()

    if API_KEY:
        oc.add(DirectoryObject(key=Callback(SabQueue), title='Queue', subtitle='View and make changes to the SABnzbd+ queue.',
            summary='View the queue. Change the order of queued donwloads, delete items from the queue.'))
        oc.add(DirectoryObject(key=Callback(SabHistory), title='History', subtitle='View SABnzbd\'s download history.',
            summary='Number of items to display is set in preferences.'))

        sabStatus = ApiRequest(mode='queue&start=0&output=json')['queue']
        if sabStatus['paused'] != True:
            oc.add(PopupDirectoryObject(key=Callback(PauseMenu), title='Pause', subtitle='Pause downloading for a specified time period.',
                summary = 'Choose a time period from the list and downloading will resume automatically'))
        else:
            oc.add(PopupDirectoryObject(key=Callback(ResumeSab), title='Resume', subtitle='Resume downloading'))
        
        oc.add(PopupDirectoryObject(key=Callback(SpeedLimitPopup), title='Set Speed Limit',
            summary='Currently %skbps' % sabStatus['speedlimit']))
    
        oc.add(DirectoryObject(key=Callback(RestartSab), title='Restart', subtitle='Restart SABnzbd+',
            summary='It may take a minute or two before SABnzbd+ is back online and functions are accessible.'))
        oc.add(DirectoryObject(key=Callback(ShutdownSab), title='ShutDown', subtitle='Shut down SABnzbd+',
            summary='If you shut down SABnzbd+, you will have to exit Plex to restart it manually.'))

    oc.add(PrefsObject(title='Plug-in Preferences', summary='Set plug-in preferences to allow proper communication with SABnzbd+',
        thumb=R('icon-prefs.png')))

    return oc

####################################################################################################  
@route(PREFIX +'/queue')
def SabQueue():
    oc = ObjectContainer(title2='Queue', noCache=True)

    try:
        queue = ApiRequest(mode='queue&start=0&output=json')['queue']

        for item in queue['slots']:
            oc.add(DirectoryObject(key=Callback(QueueMenu, nzo_id=item['nzo_id'], name=item['filename']),
                title=item['filename'], summary = 'Completed: ' + item['percentage']+'%\n' + 
                'Size: '+item['sizeleft']+'/'+item['size'] + '\n' + 'TimeLeft: ' + item['timeleft'] + '\n' + 
                'Category: ' + str(item['cat']) + '\n' + 'Priority: ' + item['priority'] + '\n' +
                'Script: ' + item['script'] +))
    except:
        return ObjectContainer(header=NAME, message='Error loading queue')
    
    if len(oc) == 0:
        return ObjectContainer(header=NAME, message='The queue is empty.')

    return oc

####################################################################################################
@route(PREFIX + '/history')
def SabHistory():
    oc = ObjectContainer(title2='History', noCache=True)
    history = ApiRequest(mode='history&start=0&limit=%s&output=json' % (Prefs['historyItems']))['history']

    for item in history['slots']:
        oc.add(PopupDirectoryObject(key=Callback(HistoryMenu, nzo_id=item['nzo_id']), title=item['name'],
            summary = 'Status: ' + item['status'] + '\n' + 'Size: '+item['size'] + '\n' +
            'Category: ' + str(item['category']) + '\n' + 'Script: ' + str(item['script']) + '\n' +
            'FilePath: ' + str(item['storage']) + '\n' + 'Time to download: ' + str(item['download_time']//3600) +
            ' hours, ' + str((item['download_time']%3600)//60) + ' minutes, ' + str((item['download_time']%3600)%60) + ' seconds.'

    if len(oc) == 0:
        return ObjectContainer(header=NAME, message='History is empty.')

    return oc

####################################################################################################
@route(PREFIX + '/pausemenu')
def PauseMenu():
    oc = ObjectContainer()

    oc.add(DirectoryObject(key=Callback(PauseSab, pauseLength=0), title='Until I Resume'))
    oc.add(DirectoryObject(key=Callback(PauseSab, pauseLength=30), title='30 minutes'))
    oc.add(DirectoryObject(key=Callback(PauseSab, pauseLength=60), title='1 hour'))
    oc.add(DirectoryObject(key=Callback(PauseSab, pauseLength=90), title='1.5 hours'))
    oc.add(DirectoryObject(key=Callback(PauseSab, pauseLength=120), title='2 hours'))
    oc.add(DirectoryObject(key=Callback(PauseSab, pauseLength=180), title='3 hours'))

    return oc

####################################################################################################
@route(PREFIX + '/pause')
def PauseSab(pauseLength):

    if pauseLength == 0:
        mode = 'pause'
    else:
        mode = 'config&name=set_pause&value=%d' % pauseLength

    response = ApiRequest(mode=mode)
    if response == 'ok':
        return ObjectContainer(header=NAME, message='Downloading paused.')
    else:
        return SabError()

####################################################################################################
@route(PREFIX + '/speedmenu')
def SpeedLimitPopup():
    oc = ObjectContainer()
    
    defaultLimit = Prefs['speedlimit']
    LIMITS = ['100','250','500','1000','1500','2500','3500']
    
    oc.add(DirectoryObject(key=Callback(SpeedLimit, speedlimit=defaultLimit), title='Default: %skbps' % defaultLimit))
    oc.add(DirectoryObject(key=Callback(SpeedLimit, speedlimit='0'), title='None'))
    for limit in LIMITS:
        oc.add(DirectoryObject(key=Callback(SpeedLimit, speedlimit=limit), title='%skbps' % limit))
    
    return oc

####################################################################################################
@route(PREFIX + '/speedlimit')
def SpeedLimit(speedlimit):

    
    mode = 'config&name=speedlimit&value=%s' % speedlimit
    
    response = ApiRequest(mode=mode)
    if response == 'ok':
        return ObjectContainer(header=NAME, message='Speedlimit set to %skpbs' % speedlimit)
    else:
        return SabError()

####################################################################################################
@route(PREFIX + '/resume')
def ResumeSab():

    mode = 'resume'
    response = ApiRequest(mode=mode)

    if response == 'ok':
        return ObjectContainer(header=NAME, message='Downloading resumed.')
    else:
        return SabError()

####################################################################################################
@route(PREFIX + '/restart')
def RestartSab():

    mode = 'restart'
    response = ApiRequest(mode=mode)
    
    if response == 'ok':
        return ObjectContainer(header=NAME, message='SABnzdb+ is restarting.')
    else:
        return SabError()

####################################################################################################
@route(PREFIX + '/shutdown')
def ShutdownSab():

    mode = 'shutdown'
    response = ApiRequest(mode=mode)
    
    if response == 'ok':
        return MessageContainer(NAME, 'SABnzdb+ shutting down.')
    else:
        return SabError()

####################################################################################################

def QueueMenu(sender, nzo_id, name):

    dir = MediaContainer(title2=name)

    dir.Append(Function(PopupDirectoryItem(PriorityMenu, 'Change Priority'), nzo_id=nzo_id))
    #dir.Append(Function(InputDirectoryItem(MoveItem, 'Move item to new position in queue'), nzo_id=nzo_id))
    dir.Append(Function(PopupDirectoryItem(CategoryMenu, 'Change Category'), nzo_id=nzo_id))
    dir.Append(Function(PopupDirectoryItem(ScriptMenu, 'Change Script'), nzo_id=nzo_id))
    dir.Append(Function(PopupDirectoryItem(PostProcessingMenu, 'Change Post-processing'), nzo_id=nzo_id))
    dir.Append(Function(PopupDirectoryItem(DeleteMenu, 'Delete from Queue'), nzo_id=nzo_id))

    return dir

####################################################################################################

def HistoryMenu(sender, nzo_id):

    dir = MediaContainer()

    dir.Append(Function(DirectoryItem(RetryDownload, 'Retry'), nzo_id=nzo_id))
    dir.Append(Function(DirectoryItem(DeleteFromHistory, 'Delete'), nzo_id=nzo_id))
    dir.Append(Function(DirectoryItem(ClearHistory, 'Clear History')))

    return dir

####################################################################################################

def PriorityMenu(sender, nzo_id):

    dir = MediaContainer(title2='Priority')

    dir.Append(Function(DirectoryItem(ChangePriority, 'High'), nzo_id=nzo_id, priority='1'))
    dir.Append(Function(DirectoryItem(ChangePriority, 'Normal'), nzo_id=nzo_id, priority='0'))
    dir.Append(Function(DirectoryItem(ChangePriority, 'Low'), nzo_id=nzo_id, priority='-1'))

    return dir

####################################################################################################

def ChangePriority(sender, nzo_id, priority):

    mode = 'queue&name=priority&value=%s&value2=%s' % (nzo_id, priority)
    response = HTTP.Request(GetSabApiUrl(mode), errors='ignore', headers=AuthHeader()).content
    Log(response)

    return MessageContainer(NAME, 'Item priority changed')

####################################################################################################

def MoveItem(sender, query, nzo_id): ### Currently non-functioning

    mode = 'switch&value=%s&value2=%s' % (nzo_id, query)
    response = HTTP.Request(GetSabApiUrl(mode), errors='ignore', headers=AuthHeader()).content
    Log(response)

    return MessageContainer(NAME, 'Moving item to slot #%s' % query)

####################################################################################################

def CategoryMenu(sender, nzo_id):

    dir = MediaContainer(title2='Categories')

    mode = 'get_cats&output=json'
    categories = JSON.ObjectFromURL(GetSabApiUrl(mode), errors='ignore', headers=AuthHeader())
    for category in categories['categories']:
        dir.Append(Function(DirectoryItem(ChangeCategory, title=category), nzo_id=nzo_id, category=category))

    return dir

####################################################################################################

def ChangeCategory(sender, nzo_id, category):

    mode = 'change_cat&value=%s&value2=%s' % (nzo_id, category)
    response = HTTP.Request(GetSabApiUrl(mode), errors='ignore', headers=AuthHeader()).content
    Log(response)

    return MessageContainer(NAME, 'Category changed for this item.')

####################################################################################################

def ScriptMenu(sender, nzo_id):

    dir = MediaContainer(title2='Scripts')

    mode = 'get_scripts&output=json'
    scripts = JSON.ObjectFromURL(GetSabApiUrl(mode), errors='ignore', headers=AuthHeader())
    for script in scripts['scripts']:
        dir.Append(Function(DirectoryItem(ChangeScript, title=script), nzo_id=nzo_id, script=script))

    return dir

####################################################################################################

def ChangeScript(sender, nzo_id, script):

    mode = 'change_script&value=%s&value2=%s' % (nzo_id, script)
    response = HTTP.Request(GetSabApiUrl(mode), errors='ignore', headers=AuthHeader()).content
    Log(response)

    return MessageContainer(NAME, 'Post-processung script changed for this item.')
    
####################################################################################################

def PostProcessingMenu(sender, nzo_id):

    dir = MediaContainer(title2='Post-Processing')

    dir.Append(Function(DirectoryItem(ChangePostProcessing, 'Skip'), nzo_id=nzo_id, process='0'))
    dir.Append(Function(DirectoryItem(ChangePostProcessing, 'Repair'), nzo_id=nzo_id, process='1'))
    dir.Append(Function(DirectoryItem(ChangePostProcessing, 'Repair/Unpack'), nzo_id=nzo_id, process='2'))
    dir.Append(Function(DirectoryItem(ChangePostProcessing, 'Repair/Unpack/Delete'), nzo_id=nzo_id, process='3'))

    return dir

####################################################################################################

def ChangePostProcessing(sender, nzo_id, process):

    mode = 'change_opts&value=%s&value2=%s' % (nzo_id, process)
    response = HTTP.Request(GetSabApiUrl(mode), errors='ignore', headers=AuthHeader()).content
    Log(response)

    return MessageContainer(NAME, 'Post-processung work-flow changed for this item.')

####################################################################################################

def DeleteMenu(sender, nzo_id):

    dir = MediaContainer(title2='Delete item?')

    dir.Append(Function(DirectoryItem(DeleteFromQueue, 'Delete item from Queue?'), nzo_id=nzo_id))

    return dir

####################################################################################################

def DeleteFromQueue(sender, nzo_id):

    mode = 'queue&name=delete&value=%s' % nzo_id
    response = HTTP.Request(GetSabApiUrl(mode), errors='ignore', headers=AuthHeader()).content
    Log(response)

    return MessageContainer(NAME, 'Deleting item from queue.')

####################################################################################################

def RetryDownload(sender, nzo_id):

    mode = 'retry&value=%s' % nzo_id
    response = HTTP.Request(GetSabApiUrl(mode), errors='ignore', headers=AuthHeader()).content
    Log(response)

    return MessageContainer(NAME, 'Item re-added to queue.')

####################################################################################################

def DeleteFromHistory(sender, nzo_id):

    mode = 'history&name=delete&value=%s' % nzo_id
    response = HTTP.Request(GetSabApiUrl(mode), errors='ignore', headers=AuthHeader()).content
    Log(response)

    return MessageContainer(NAME, 'Item deleted from history.')

####################################################################################################

def ClearHistory(sender):

    mode = 'history&name=delete&value=all'
    response = HTTP.Request(GetSabApiUrl(mode), errors='ignore', headers=AuthHeader()).content
    Log(response)

    return MessageContainer(NAME, 'All items cleared from history.')

####################################################################################################
