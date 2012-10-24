#### Use this file as a template when adding support for a new NZB Provider ####
##### Save modified version with filename <provider>.py, eg. NZBMatrix.py ######

PROVIDER = 'NZBMatrix' 

# URL used for API-based search #
API_SEARCH_URL      =  'http://api.nzbmatrix.com/v1.1/search.php?search=%s&catid=%s&num=%s&maxage=%s&username=%s&apikey=%s'
                        # (query, category='', max_results='', max_age='', user, api_key)

# URL used for API-based NZB downloads #
API_DOWNLOAD_URL    =   'http://api.nzbmatrix.com/v1.1/download.php?id=%s&username=%s&apikey=%s'
                        # (nzb_id, user, api_key)

### DEFAULT SETTINGS ###
USE_HTTPS = False   # Takes a bool
MAX_RESULTS = ''    # Takes an integer (as a string) to a maximum of 50
MAX_AGE = ''        # Takes an integer (as a string)

# NZB Categories #
CATEGORIES = [] ### TODO:: figure out how to handle categories

def Search(query='', category=''): ###TODO:: What other global-type parameters should be added? ###
    '''
        should return a list of JSON objects with the following fields:
        {
            "title"     :   "the title of the nzb",
            "nzb_id"    :   "the unqiue id of the nzb used by the provider",
            "provider"  :   "same as the filename (without '.py')",
            "summary"   :   "Build a summary string with as much detail as can
                                be gathered just from the search response.",
            "thumb:     :   "an image URL is available"
        }
    '''
    
    url = NZBMatrixURL(API_SEARCH_URL % (query, CATEGORIES[category], GetMaxResults(), GetMaxAge(), Dict['NZB_PROVIDERS'][PROVIDER]['username'], Dict['NZB_PROVIDERS'][PROVIDER]['api_key']))
    return

def Add(nzb_id):
    ''' should return a URL for the NZB to be added which can then be passed via
        the SABnzbd API function "addurl" '''
    add_url = API_DOWNLOAD_URL % (nzb_id, Dict['NZB_PROVIDERS'][PROVIDER]['username'], Dict['NZB_PROVIDERS'][PROVIDER]['api_key'])
    return add_url

def GetNZBDetails(nzb_id):
    ''' return a JSON object with as much detail about the NZB as possible '''
    return

def NZBMatrixURL(url):
    try:
        if Dict[PROVIDER]['use_https']:
            return url.replace('http://', 'https://')
        else:
            return url
    except:
        return url

def GetMaxResults():
    if PROVIDER in Dict:
        try:
            return Dict[PROVIDER]['max_results']
        except:
            return ''

def GetMaxAge():
    if PROVIDER in Dict:
        try:
            return Dict[PROVIDER]['max_age']
        except:
            return ''

def ResultsToJSON(result_string):
    ''' take the result string from NZBMatrix and convert it to valid JSON '''
    step1 = result_string.replace(':', '":"')
    step2 = step1.replace('|', '},{')
    step3 = step2.replace(';', '","')
    step4 = '[{"' + step3 + '}]'
    return JSON.ObjectFromString(step4)

################################################################################
######## Add methods for setting provider-specific defaults below here #########
################################################################################

def SetDefaults(sender):
    ''' return a MediaContainer with a list of DirectoryItem function callbacks
     for setting defaults specific to this NZB Provider '''
    
    if PROVIDER in Dict:
        ''' check to see if defaults already exist for this provider '''
        pass
    else:
        ''' otherwise create a set of defaults settings '''
        Dict[PROVIDER] = {}
        ''' Add basic default settings here '''
        Dict[PROVIDER]['use_https']     =   USE_HTTPS
        Dict[PROVIDER]['max_results']   =   MAX_RESULTS
        Dict[PROVIDER]['max_age']       =   MAX_AGE
    
    dir = MediaContainer(title1=PROVIDER, title2="Set Defaults")
    if Dict[PROVIDER]['use_https']:
        dir.Append(Function(DirectoryObject(UseHTTPS, title="Use SSL Encryption: TRUE"), https=False))
    else:
        dir.Append(Function(DirectoryObject(UseHTTPS, title="Use SSL Encryption: FALSE"), https=True))
    dir.Append(Function(InputDirectoryObject(MaxResults, title="Maximum # of results to return: %s" % Dict[PROVIDER]['max_results'],
        prompt="Set max number of search results to:")))
    dir.Append(Function(InputDirectoryObject(MaxAge, title="Maximum age of results to return: %s days" % Dict[PROVIDER]['max_age'],
        prompt="Set max age (in days) of search results to:")))
    
    return dir
    
def UseHTTPS(sender, https):
    Dict[PROVIDER]['use_https'] = https
    return MessageContainer(PROVIDER, "Use SSL Encryption set to %s" % Dict[PROVIDER]['use_https'])
    
def MaxResults(sender, max_results):
    Dict[PROVIDER]['max_results'] = max_results
    return MessageContainer(PROVIDER, "Max results set to %s" % Dict[PROVIDER]['max_results'])
    
def MaxAge(sender, max_age):
    Dict[PROVIDER]['max_age'] = max_age
    return MessageContainer(PROVIDER, "Max age set to %s" % Dict[PROVIDER]['max_age'])
