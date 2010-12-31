####################################################################################################

APPLICATIONS_PREFIX = "/applications/sabnzbd"

NAME            = L('SABnzbd+')
ART             = 'art-default.png'
ICON            = 'icon-default.png'
AUTH_TYPE       = ''
API_QUERY_URL   = ''

####################################################################################################

def Start():
    Plugin.AddPrefixHandler(APPLICATIONS_PREFIX, ApplicationsMainMenu, L('SABnzbd+'), ICON, ART)

    Plugin.AddViewGroup("InfoList", viewMode="InfoList", mediaType="items")
    Plugin.AddViewGroup("List", viewMode="List", mediaType="items")

    MediaContainer.art = R(ART)
    MediaContainer.title1 = NAME
    DirectoryItem.thumb = R(ICON)
    
    #cookies = HTTP.GetCookiesForURL(Get_SAB_URL())
    #Log(cookies)
    #HTTP.Headers['Cookie'] = cookies
    #HTTP.Headers['User-agent'] = 'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.6; en-US; rv:1.9.2.10) Gecko/20100914 Firefox/3.6.10'
    
    global AUTH_TYPE
    AUTH_TYPE = HTTP.Request(Get_SAB_URL()+'/sabnzbd/api?mode=auth')

    global API_QUERY_URL
    API_QUERY_URL = Get_SAB_URL() + '/api?mode=%s&apikey=%s'
    
    if AUTH_TYPE == 'login':
        if Prefs['sabUser'] and Prefs['sabPass']:
            HTTP.SetPassword(Get_SAB_URL(), username=Prefs['sabUser'], password=['sabPass'])   
    
####################################################################################################

def ValidatePrefs():
    if AUTH_TYPE == 'login':
        if Prefs['sabUser'] and Prefs['sabPass']:
            HTTP.SetPassword(Get_SAB_URL(), username=Prefs['sabUser'], password=['sabPass'])
            return
    elif AUTH_TYPE == 'apikey':    
        if Prefs['sabAPI'] == None:
            return MessageContainer(NAME, L('You must enter you SABnzbd+ API key for the plugin to function properly.'))
    else:
        return

####################################################################################################
    
def ApplicationsMainMenu():
    dir = MediaContainer(viewGroup="InfoList", noCache=True)
    dir.Append(Function(DirectoryItem(SabQueue, "Queue", "View and make changes to the SABnzbd+ queue.",
        summary="View the queue.  Change the order of queued donwloads, delete items from the queue.",
        thumb=R(ICON), art=R(ART))))
    dir.Append(Function(DirectoryItem(SabHistory, "History", "View SABnzbd's download history.",
        summary="Number of items to display is set in preferences.",
        thumb=R(ICON), art=R(ART))))
    sabStatus = GetQueue()
    if sabStatus['paused'] != True:
        dir.Append(Function(PopupDirectoryItem(PauseMenu, 'Pause', 'Pause downloading for a specified time period.',
            summary = 'Choose a time period from the list and downloading will resume automatically',
            thumb=R(ICON), art = R(ART))))
    else:
        dir.Append(Function(DirectoryItem(ResumeSab, 'Resume', 'Resume downloading', thumb=R(ICON), art=R(ART))))
    dir.Append(Function(DirectoryItem(RestartSab, 'Restart', 'Restart SABnzbd+',
        summary='It may take a minute or two before SABnzbd+ is back online and functions are accessible.',
        thumb=R(ICON), art=R(ART))))
    dir.Append(Function(DirectoryItem(ShutdownSab, 'ShutDown', 'Shut down SABnzbd+',
        summary='If you shut down SABnzbd+, you will have to exit Plex to restart it manually.',
        thumb=R(ICON), art=R(ART))))
    dir.Append(PrefsItem(title="Preferences", subtitle="For SABnzbd+ plug-in",
        summary="Set plug-in preferences to allow proper communication with SABnzbd+", thumb=R(ICON)))
    return dir

####################################################################################################  

def SabQueue(sender):
    dir = MediaContainer(viewGroup='InfoList', title2='Queue', noCache=True)
    
    queue = GetQueue()
    
    for item in queue['slots']:
        dir.Append(Function(DirectoryItem(QueueMenu, title=item['filename'],
            subtitle='Size: '+item['sizeleft']+'/'+item['size'], infoLabel=item['percentage'],
            summary='Category: '+item['cat']+'\nPriority: '+item['priority']+'\nScript: '+item['script']+
            '\nTimeLeft: '+item['timeleft'], thumb=R(ICON)), nzo_id=item['nzo_id'], name=item['filename']))
    
    return dir

####################################################################################################

def SabHistory(sender):
    dir = MediaContainer(viewGroup='InfoList', title2='History', noCache=True)
    history = GetHistory()
    
    for item in history['slots']:
        dir.Append(Function(PopupDirectoryItem(HistoryMenu, title=item['name'], subtitle='Size: '+item['size'],
            infoLabel=item['status'], summary='Category: '+item['category']+'\nScript: '+item['script']+
            '\nFilePath: '+item['storage']+'\nTime to donwload: '+str(item['download_time']//3600)+' hours, '+
            str((item['download_time']%3600)//60)+' minutes, '+str((item['download_time']%3600)%60)+' seconds.',
            thumb=R(ICON)), nzo_id=item['nzo_id']))
    return dir

####################################################################################################

def Get_SAB_URL():
    url = 'http://'+Prefs['sabHost']+':'+Prefs['sabPort']
    return url

####################################################################################################

def GetQueue():
    mode = 'queue&start=0&output=json'
    url = API_QUERY_URL % (mode, Prefs['sabAPI'])
    queue = JSON.ObjectFromURL(url, cacheTime=0)
    return queue['queue']

####################################################################################################

def GetHistory():
    mode = 'history&start=0&limit=%s&output=json' % (Prefs['historyItems'])
    url = API_QUERY_URL % (mode, Prefs['sabAPI'])
    history = JSON.ObjectFromURL(url, cacheTime=0)
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
    
    url = API_QUERY_URL % (mode, Prefs['sabAPI'])
    Log(url)
    response = HTTP.Request(url, errors='ignore', cacheTime=0).content
    Log(response)
    
    return MessageContainer(NAME, L('Downloading paused.'))

####################################################################################################

def ResumeSab(sender):
    
    mode = 'resume'
    url = API_QUERY_URL % (mode, Prefs['sabAPI'])
    response = HTTP.Request(url, errors='ignore', cacheTime=0).content
    Log(response)
    
    return MessageContainer(NAME, L('Downloading resumed.'))

####################################################################################################

def RestartSab(sender):
    
    mode = 'restart'
    url = API_QUERY_URL % (mode, Prefs['sabAPI'])
    response = HTTP.Request(url, errors='ignore', cacheTime=0).content
    Log(response)
    
    return MessageContainer(NAME, L('SABnzdb+ is restarting.'))
    
####################################################################################################

def ShutdownSab(sender):
    
    mode = 'shutdown'
    url = API_QUERY_URL % (mode, Prefs['sabAPI'])
    response = HTTP.Request(url, errors='ignore', cacheTime=0).content
    Log(response)
    
    return MessageContainer(NAME, L('SABnzdb+ shutting down.'))
    
####################################################################################################

def QueueMenu(sender, nzo_id, name):
    
    dir = MediaContainer(title2=name)
    
    dir.Append(Function(PopupDirectoryItem(PriorityMenu, 'Change Priority'), nzo_id=nzo_id))
    dir.Append(Function(InputDirectoryItem(MoveItem, 'Move item to new position in queue'), nzo_id=nzo_id))
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
    url = API_QUERY_URL % (mode, Prefs['sabAPI'])
    response = HTTP.Request(url, errors='ignore', cacheTime=0).content
    Log(response)
    
    return MessageContainer(NAME, L('Item priority changed'))
    
####################################################################################################

def MoveItem(sender, query, nzo_id):
    
    mode = 'switch&value=%s&value2=%s' % (nzo_id, query)
    url = API_QUERY_URL % (mode, Prefs['sabAPI'])
    response = HTTP.Request(url, errors='ignore', cacheTime=0).content
    Log(response)
    
    return MessageContainer(NAME, L('Moving item to slot #%s' % query))

####################################################################################################

def CategoryMenu(sender, nzo_id):
    
    dir = MediaContainer(title2='Categories')
    
    mode = 'get_cats&output=json'
    url = API_QUERY_URL % (mode, Prefs['sabAPI'])
    categories = JSON.ObjectFromURL(url, cacheTime=0)
    for category in categories['categories']:
        dir.Append(Function(DirectoryItem(ChangeCategory, title=category), nzo_id=nzo_id, category=catedory))
    
    return dir

####################################################################################################

def ChangeCategory(sender, nzo_id, category):
    
    mode = 'change_cat&value=%s&value2=%s' % (nzo_id, category)
    url = API_QUERY_URL % (mode, Prefs['sabAPI'])
    response = HTTP.Request(url, errors='ignore', cacheTime=0).content
    Log(response)
    
    return MessageContainer(NAME, L('Category changed for this item.'))
    
####################################################################################################

def ScriptMenu(sender, nzo_id):
    
    dir = MediaContainer(title2='Scripts')
    
    mode = 'get_scripts&output=json'
    url = API_QUERY_URL % (mode, Prefs['sabAPI'])
    scripts = JSON.ObjectFromURL(url, cacheTime=0)
    for script in scripts['scripts']:
        dir.Append(Function(DirectoryItem(ChangeScript, title=script), nzo_id=nzo_id, script=script))
    
    return dir

####################################################################################################

def ChangeScript(sender, nzo_id, script):
    
    mode = 'change_script&value=%s&value2=%s' % (nzo_id, script)
    url = API_QUERY_URL % (mode, Prefs['sabAPI'])
    response = HTTP.Request(url, errors='ignore', cacheTime=0).content
    Log(response)
    
    return MessageContainer(NAME, L('Post-processung script changed for this item.'))
    
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
    url = API_QUERY_URL % (mode, Prefs['sabAPI'])
    response = HTTP.Request(url, errors='ignore', cacheTime=0).content
    Log(response)
    
    return MessageContainer(NAME, L('Post-processung work-flow changed for this item.'))
    
####################################################################################################

def DeleteMenu(sender, nzo_id):
    
    dir = MediaContainer(title2='Delete item?')
    
    dir.Append(Function(DirectoryItem(DeleteFromQueue, 'Delete item from Queue?'), nzo_id=nzo_id))
    
    return dir

####################################################################################################

def DeleteFromQueue(sender, nzo_id):
    
    mode = 'queue&name=delete&value=%s' % nzo_id
    url = API_QUERY_URL % (mode, Prefs['sabAPI'])
    response = HTTP.Request(url, errors='ignore', cacheTime=0).content
    Log(response)
    
    return MessageContainer(NAME, L('Deleting item from queue.'))

####################################################################################################

def RetryDownload(sender, nzo_id):
    
    mode = 'retry&value=%s' % nzo_id
    url = API_QUERY_URL % (mode, Prefs['sabAPI'])
    response = HTTP.Request(url, errors='ignore', cacheTime=0).content
    Log(response)
    
    return MessageContainer(NAME, L('Item re-added to queue.'))

####################################################################################################

def DeleteFromHistory(sender, nzo_id):
    
    mode = 'history&name=delete&value=%s' % nzo_id
    url = API_QUERY_URL % (mode, Prefs['sabAPI'])
    response = HTTP.Request(url, errors='ignore', cacheTime=0).content
    Log(response)
    
    return MessageContainer(NAME, L('Item deleted from history.'))
    
####################################################################################################

def ClearHistory(sender):
    
    mode = 'history&name=delete&value=all'
    url = API_QUERY_URL % (mode, Prefs['sabAPI'])
    response = HTTP.Request(url, errors='ignore', cacheTime=0).content
    Log(response)
    
    return MessageContainer(NAME, L('All items cleared from history.'))
    
####################################################################################################