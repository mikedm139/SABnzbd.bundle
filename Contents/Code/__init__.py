from base64 import b64encode

####################################################################################################

APPLICATIONS_PREFIX = '/applications/sabnzbd'

NAME          = 'SABnzbd+'
ART           = 'art-default.png'
ICON          = 'icon-default.png'

####################################################################################################

def Start():
    Plugin.AddPrefixHandler(APPLICATIONS_PREFIX, MainMenu, NAME, ICON, ART)
    Plugin.AddViewGroup('InfoList', viewMode='InfoList', mediaType='items')

    MediaContainer.art = R(ART)
    MediaContainer.title1 = NAME
    MediaContainer.viewGroup = 'InfoList'

    DirectoryItem.thumb = R(ICON)
    PopupDirectoryItem.thumb = R(ICON)

    HTTP.CacheTime = 1
    
####################################################################################################

def AuthHeader():
    header = {}

    if Prefs['sabUser'] and Prefs['sabPass']:
        header = {'Authorization': 'Basic ' + b64encode(Prefs['sabUser'] + ':' + Prefs['sabPass'])}

    return header

####################################################################################################

def GetSabUrl():
    return 'http://' + Prefs['sabHost'] + ':' + Prefs['sabPort']

####################################################################################################

def GetSabApiUrl(mode):
    if Dict['sabApiKey']:
        return GetSabUrl() + '/api?mode=%s&apikey=%s' % (mode, Dict['sabApiKey'])
    else:
        return GetSabUrl() + '/api?mode=%s' % (mode)

####################################################################################################

def ApiKey():
    if not Prefs['sabApiKey']:
        apiKey = HTML.ElementFromURL(GetSabUrl() + '/config/general', headers=(AuthHeader())).xpath('//input[@id="apikey"]')[0].get('value')
        return apiKey
    else: return Prefs['sabApiKey']

####################################################################################################

def ValidatePrefs():
    auth_type = HTTP.Request(GetSabUrl() + '/sabnzbd/api?mode=auth')

    if auth_type == 'apikey':
        if not Prefs['sabApiKey']:
            return MessageContainer(NAME, 'You must enter your SABnzbd+ API key for the plugin to function properly.')

####################################################################################################
    
def MainMenu():
    dir = MediaContainer(noCache=True)

    if not Dict['sabApiKey']:
        Dict['sabApiKey'] = ApiKey()
    
    try:
        mode = 'queue&start=0&output=json'
        test = JSON.ObjectFromURL(GetSabApiUrl(mode), errors='ignore', headers=AuthHeader())
        if test['queue']:
            new_user = False
    except:
        new_user = True
        Dict['sabApiKey'] = ApiKey()

    if new_user == False:
        dir.Append(Function(DirectoryItem(SabQueue, title='Queue', subtitle='View and make changes to the SABnzbd+ queue.',
            summary='View the queue. Change the order of queued donwloads, delete items from the queue.')))
        dir.Append(Function(DirectoryItem(SabHistory, title='History', subtitle='View SABnzbd\'s download history.',
            summary='Number of items to display is set in preferences.')))

        sabStatus = GetQueue()
        if sabStatus['paused'] != True:
            dir.Append(Function(PopupDirectoryItem(PauseMenu, title='Pause', subtitle='Pause downloading for a specified time period.',
                summary = 'Choose a time period from the list and downloading will resume automatically')))
        else:
            dir.Append(Function(DirectoryItem(ResumeSab, title='Resume', subtitle='Resume downloading')))

        dir.Append(Function(DirectoryItem(RestartSab, title='Restart', subtitle='Restart SABnzbd+',
            summary='It may take a minute or two before SABnzbd+ is back online and functions are accessible.')))
        dir.Append(Function(DirectoryItem(ShutdownSab, title='ShutDown', subtitle='Shut down SABnzbd+',
            summary='If you shut down SABnzbd+, you will have to exit Plex to restart it manually.')))

    dir.Append(PrefsItem(title='Preferences', subtitle='For SABnzbd+ plug-in',
        summary='Set plug-in preferences to allow proper communication with SABnzbd+', thumb=R('icon-prefs.png')))
    return dir

####################################################################################################  

def SabQueue(sender):
    dir = MediaContainer(title2='Queue', noCache=True)

    try:
        queue = GetQueue()

        for item in queue['slots']:
            dir.Append(Function(DirectoryItem(QueueMenu, title=item['filename'],
                subtitle='Size: '+item['sizeleft']+'/'+item['size'], infoLabel=item['percentage']+'%',
                summary='Category: '+str(item['cat'])+'\nPriority: '+item['priority']+'\nScript: '+item['script']+
                '\nTimeLeft: '+item['timeleft']), nzo_id=item['nzo_id'], name=item['filename']))
    except:
        return MessageContainer(NAME, 'Error loading queue')
    
    if len(dir) == 0:
        return MessageContainer(NAME, 'The queue is empty.')

    return dir

####################################################################################################

def SabHistory(sender):
    dir = MediaContainer(title2='History', noCache=True)
    history = GetHistory()

    for item in history['slots']:
        dir.Append(Function(PopupDirectoryItem(HistoryMenu, title=item['name'], subtitle='Size: '+item['size'],
            infoLabel=item['status'], summary='Category: '+str(item['category'])+'\nScript: '+item['script']+
            '\nFilePath: '+item['storage']+'\nTime to download: '+str(item['download_time']//3600)+' hours, '+
            str((item['download_time']%3600)//60)+' minutes, '+str((item['download_time']%3600)%60)+' seconds.'),
            nzo_id=item['nzo_id']))

    if len(dir) == 0:
        return MessageContainer(NAME, 'History is empty.')

    return dir

####################################################################################################

def GetQueue():
    mode = 'queue&start=0&output=json'
    queue = JSON.ObjectFromURL(GetSabApiUrl(mode), errors='ignore', headers=AuthHeader())
    return queue['queue']

####################################################################################################

def GetHistory():
    mode = 'history&start=0&limit=%s&output=json' % (Prefs['historyItems'])
    history = JSON.ObjectFromURL(GetSabApiUrl(mode), errors='ignore', headers=AuthHeader())
    return history['history']

####################################################################################################

def PauseMenu(sender):
    dir = MediaContainer()

    dir.Append(Function(DirectoryItem(PauseSab, title='Until I Resume'), pauseLength=0))
    dir.Append(Function(DirectoryItem(PauseSab, title='30 minutes'), pauseLength=30))
    dir.Append(Function(DirectoryItem(PauseSab, title='1 hour'), pauseLength=60))
    dir.Append(Function(DirectoryItem(PauseSab, title='1.5 hours'), pauseLength=90))
    dir.Append(Function(DirectoryItem(PauseSab, title='2 hours'), pauseLength=120))
    dir.Append(Function(DirectoryItem(PauseSab, title='3 hours'), pauseLength=180))

    return dir

####################################################################################################

def PauseSab(sender, pauseLength):

    if pauseLength == 0:
        mode = 'pause'
    else:
        mode = 'config&name=set_pause&value=%d' % pauseLength

    response = HTTP.Request(GetSabApiUrl(mode), errors='ignore', headers=AuthHeader()).content
    Log(response)

    return MessageContainer(NAME, 'Downloading paused.')

####################################################################################################

def ResumeSab(sender):

    mode = 'resume'
    response = HTTP.Request(GetSabApiUrl(mode), errors='ignore', headers=AuthHeader()).content
    Log(response)

    return MessageContainer(NAME, 'Downloading resumed.')

####################################################################################################

def RestartSab(sender):

    mode = 'restart'
    response = HTTP.Request(GetSabApiUrl(mode), errors='ignore', headers=AuthHeader()).content
    Log(response)

    return MessageContainer(NAME, 'SABnzdb+ is restarting.')

####################################################################################################

def ShutdownSab(sender):

    mode = 'shutdown'
    response = HTTP.Request(GetSabApiUrl(mode), errors='ignore', headers=AuthHeader()).content
    Log(response)

    return MessageContainer(NAME, 'SABnzdb+ shutting down.')

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

    mode = 'queue&name=priority&value=%s&value2=%d' % (nzo_id, priority)
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
