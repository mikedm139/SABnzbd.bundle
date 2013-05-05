####################################################################################################

PREFIX = '/applications/sabnzbd'

NAME          = 'SABnzbd+'
ART           = 'art-default.png'
ICON          = 'icon-default.png'

####################################################################################################

def Start():
    ObjectContainer.art = R(ART)
    ObjectContainer.title1 = NAME

    DirectoryObject.thumb = R(ICON)
    PopupDirectoryObject.thumb = R(ICON)

    HTTP.CacheTime = 1
    
####################################################################################################
@route(PREFIX + '/auth')
def AuthHeader():
    header = {}

    if Prefs['sabUser'] and Prefs['sabPass']:
        header = {'Authorization': 'Basic ' + String.Base64Encode(Prefs['sabUser'] + ':' + Prefs['sabPass'])}

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
def ApiRequest(mode, success_message=None):
    if success_message:
        success_message = success_message.replace('"', '')
    content = HTTP.Request(GetSabApiUrl(mode), errors='ignore', headers=AuthHeader()).content
    try:
        if content.strip().lstrip('-').isdigit():
            raise e #not JSON
        data = JSON.ObjectFromString(content)
        return data
    except:
        #not all API calls return a JSON response so we'll return the success_message or an error
        if not content.strip().startswith('error:'):
            return ObjectContainer(header=NAME, message=success_message)
        else:
            return SabError()
    
####################################################################################################
@route(PREFIX + '/validateprefs')
def ValidatePrefs():
    return
    
####################################################################################################
@route(PREFIX + '/error')
def SabError():
    return ObjectContainer(header=NAME, message='An error occurred. Your request did not succeed')

####################################################################################################
@handler(PREFIX, NAME, ICON, ART)
def MainMenu():
    oc = ObjectContainer(no_cache=True)
    
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
        oc.add(DirectoryObject(key=Callback(SabQueue), title='Queue',
            summary='View the queue. Change the order of queued donwloads, delete items from the queue.'))
        oc.add(DirectoryObject(key=Callback(SabHistory), title='History',
            summary='View SABnzbd\'s download history. Number of items to display is set in preferences.'))

        sabStatus = ApiRequest(mode='queue&start=0&output=json')['queue']
        if sabStatus['paused'] != True:
            oc.add(PopupDirectoryObject(key=Callback(PauseMenu), title='Pause',
                summary = 'Choose a time period from the list and downloading will resume automatically'))
        else:
            oc.add(PopupDirectoryObject(key=Callback(ApiRequest, mode='resume', success_message='Downloading resumed.'),
                title='Resume'))
        
        oc.add(PopupDirectoryObject(key=Callback(SpeedLimitPopup), title='Set Speed Limit',
            summary='Currently %skbps' % sabStatus['speedlimit']))
    
        oc.add(DirectoryObject(key=Callback(ApiRequest, mode='restart', success_message='SABnzdb+ is restarting.'), title='Restart',
            summary='It may take a minute or two before SABnzbd+ is back online and functions are accessible.'))
        oc.add(DirectoryObject(key=Callback(ApiRequest, mode='shutdown', success_message='SABnzdb+ shutting down.'), title='ShutDown',
            summary='If you shut down SABnzbd+, you may have to exit Plex to restart it manually (depending on your setup).'))

    oc.add(PrefsObject(title='Plug-in Preferences', summary='Set plug-in preferences to allow proper communication with SABnzbd+',
        thumb=R('icon-prefs.png')))
    
    if API_KEY:
        oc.add(DirectoryObject(key=Callback(ResetApiKey), title="Reset saved API Key",
            summary="If you have changed your setup or SABnzbd+ API key, use this to clear the saved key so the new one can be retrieved."))

    return oc

####################################################################################################  
@route(PREFIX +'/queue')
def SabQueue():
    oc = ObjectContainer(title2='Queue', no_cache=True)

    try:
        queue = ApiRequest(mode='queue&start=0&output=json')['queue']

        for item in queue['slots']:
            oc.add(DirectoryObject(key=Callback(QueueMenu, nzo_id=item['nzo_id'], name=item['filename']),
                title=item['filename'], summary = 'Completed: ' + item['percentage']+'%\n' + 
                'Size: '+item['sizeleft']+'/'+item['size'] + '\n' + 'TimeLeft: ' + item['timeleft'] + '\n' + 
                'Category: ' + str(item['cat']) + '\n' + 'Priority: ' + item['priority'] + '\n' +
                'Script: ' + item['script']))
    except:
        return ObjectContainer(header=NAME, message='Error loading queue')
    
    if len(oc) == 0:
        return ObjectContainer(header=NAME, message='The queue is empty.')

    return oc

####################################################################################################
@route(PREFIX + '/history')
def SabHistory():
    oc = ObjectContainer(title2='History', no_cache=True)
    history = ApiRequest(mode='history&start=0&limit=%s&output=json' % (Prefs['historyItems']))['history']

    for item in history['slots']:
        oc.add(PopupDirectoryObject(key=Callback(HistoryMenu, nzo_id=item['nzo_id']), title=item['name'],
            summary = 'Status: ' + item['status'] + '\n' + 'Size: '+item['size'] + '\n' +
            'Category: ' + str(item['category']) + '\n' + 'Script: ' + str(item['script']) + '\n' +
            'FilePath: ' + str(item['storage']) + '\n' + 'Time to download: ' + str(item['download_time']//3600) +
            ' hours, ' + str((item['download_time']%3600)//60) + ' minutes, ' + str((item['download_time']%3600)%60) + ' seconds.'))

    if len(oc) == 0:
        return ObjectContainer(header=NAME, message='History is empty.')

    return oc

####################################################################################################
@route(PREFIX + '/pause')
def PauseMenu():
    oc = ObjectContainer()

    oc.add(DirectoryObject(key=Callback(ApiRequest, mode='pause', success_message='Downloading paused until manually resumed.'),
        title='Until I Resume'))
    for pause_length in ['30','60','90','120','180']:
        oc.add(DirectoryObject(key=Callback(ApiRequest, mode='config&name=set_pause&value=%d' % pause_length,
            success_message='Downloading paused for %s minutes' % pause_length), title='%s minutes' % pause_length))

    return oc

####################################################################################################
@route(PREFIX + '/speedlimit')
def SpeedLimitPopup():
    oc = ObjectContainer()
    
    defaultLimit = Prefs['speedlimit']
    LIMITS = ['100','250','500','1000','1500','2500','3500']
    
    oc.add(DirectoryObject(key=Callback(ApiRequest, mode = 'config&name=speedlimit&value=%s' % defaultLimit,
        success_message='Speedlimit set to %skpbs' % defaultLimit), title='Default: %skbps' % defaultLimit))
    oc.add(DirectoryObject(key=Callback(ApiRequest, mode = 'config&name=speedlimit&value=%s' % '0',
        success_message='Speedlimit set to None'), title='None'))
    for limit in LIMITS:
        oc.add(DirectoryObject(key=Callback(ApiRequest, mode = 'config&name=speedlimit&value=%s' % limit,
        success_message='Speedlimit set to %skpbs' % limit), title='%skbps' % limit))
    
    return oc

####################################################################################################
@route(PREFIX + '/queuemenu')
def QueueMenu(nzo_id, name):

    oc = ObjectContainer(title2=name)

    oc.add(PopupDirectoryObject(key=Callback(PriorityMenu, nzo_id=nzo_id), title='Change Priority'))
    oc.add(PopupDirectoryObject(key=Callback(MoveItemMenu, nzo_id=nzo_id), title='Move item to new position in queue'))
    oc.add(PopupDirectoryObject(key=Callback(CategoryMenu, nzo_id=nzo_id), title='Change Category'))
    oc.add(PopupDirectoryObject(key=Callback(PostProcessingMenu, nzo_id=nzo_id), title='Change Post-Processing'))
    oc.add(PopupDirectoryObject(key=Callback(DeleteMenu, nzo_id=nzo_id), title='Delete from Queue'))

    return oc

####################################################################################################
@route(PREFIX + '/historymenu')
def HistoryMenu(nzo_id):

    oc = ObjectContainer()

    oc.add(DirectoryObject(key=Callback(ApiRequest, mode='retry&value=%s' % nzo_id,
        success_message='Item re-added to queue.'), title='Retry'))
    oc.add(DirectoryObject(key=Callback(ApiRequest, mode='history&name=delete&value=%s' % nzo_id,
        success_message='Item deleted from history.'), title='Delete'))
    oc.add(DirectoryObject(key=Callback(ApiRequest, mode='history&name=delete&value=all',
        success_message='All items cleared from history.'), title='Clear History'))

    return oc

####################################################################################################
@route(PREFIX + '/priorities')
def PriorityMenu(nzo_id):

    oc = ObjectContainer(title2='Priority')

    oc.add(DirectoryObject(key=Callback(ApiRequest, mode='queue&name=priority&value=%s&value2=%s' % (nzo_id, '1'),
        success_message='Item priority changed to "High"'), title='High'))
    oc.add(DirectoryObject(key=Callback(ApiRequest, mode='queue&name=priority&value=%s&value2=%s' % (nzo_id, '0'),
        success_message='Item priority changed to "Normal"'), title='Normal'))
    oc.add(DirectoryObject(key=Callback(ApiRequest, mode='queue&name=priority&value=%s&value2=%s' % (nzo_id, '-1'),
        success_message='Item priority changed to "Low"'), title='Low'))

    return oc

####################################################################################################
@route(PREFIX + '/move')
def MoveItemMenu(nzo_id):
    
    oc = ObjectContainer()
    
    queue = ApiRequest(mode='queue&start=0&output=json')['queue']

    i = 0
    
    while i < len(queue['slots']):
        oc.add(DirectoryObject(key=Callback(ApiRequest, mode='switch&value=%s&value2=%s' % (nzo_id, i),
            success_message='Moving item to slot #%s' % i), title='%s' % i))
        i = i + 1
    
    return oc

####################################################################################################
@route(PREFIX + '/category')
def CategoryMenu(nzo_id):

    oc = ObjectContainer(title2='Categories')

    mode = 'get_cats&output=json'
    categories = ApiRequest(mode=mode)
    for category in categories['categories']:
        oc.add(DirectoryObject(key=Callback(ApiRequest, mode='change_cat&value=%s&value2=%s' % (nzo_id, category),
            success_message='Category changed to %s.' % category), title=category))

    return oc

####################################################################################################
@route(PREFIX + '/script')
def ScriptMenu(nzo_id):

    oc = ObjectContainer(title2='Scripts')

    mode = 'get_scripts&output=json'
    scripts = ApiRequest(mode=mode)
    for script in scripts['scripts']:
        oc.add(DirectoryObject(key=Callback(ApiRequest, mode = 'change_script&value=%s&value2=%s' % (nzo_id, script),
            success_message='Post-processung script changed to %s.' % script), title=script))

    return oc

####################################################################################################
@route(PREFIX + '/postprocessing')
def PostProcessingMenu(nzo_id):

    oc = ObjectContainer(title2='Post-Processing')

    oc.add(DirectoryObject(key=Callback(ApiRequest, mode='change_opts&value=%s&value2=%s' % (nzo_id, '0'),
        success_message='Post-processing work-flow set to "Skip"'), title='Skip'))
    oc.add(DirectoryObject(key=Callback(ApiRequest, mode='change_opts&value=%s&value2=%s' % (nzo_id, '1'),
        success_message='Post-processing work-flow set to "Repair"'), title='Repair'))
    oc.add(DirectoryObject(key=Callback(ApiRequest, mode='change_opts&value=%s&value2=%s' % (nzo_id, '2'),
        success_message='Post-processing work-flow set to "Repair/Unpack"'), title='Repair/Unpack'))
    oc.add(DirectoryObject(key=Callback(ApiRequest, mode='change_opts&value=%s&value2=%s' % (nzo_id, '3'),
        success_message='Post-processing work-flow set to "Repair/Unpack/Delete"'), title='Repair/Unpack/Delete'))

    return oc

####################################################################################################
@route(PREFIX + '/confirmdelete')
def DeleteMenu(nzo_id):

    oc = ObjectContainer(title2='Delete item')

    oc.add(DirectoryObject(key=Callback(ApiRequest, mode='queue&name=delete&value=%s' % nzo_id,
        success_message='Deleting item from queue.'), title='Delete item from Queue?'))
    
    return oc

####################################################################################################
@route(PREFIX + '/resetapikey')
def ResetApiKey():
    try:
        Dict.Reset()
        return ObjectContainer(header=NAME, message="Saved API Key has been deleted. A new one will now be retrieved.")
    except:
        Log("Unable to reset Dict(). Failed to remove saved API Key.")
        return ObjectContainer(header=NAME, message="Failed to remove saved API Key.")
    
####################################################################################################
