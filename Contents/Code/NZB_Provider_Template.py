### Use this file as a template when adding support for a new NZB Provider ###

# URL used for API-based search #
API_SEARCH_URL      =   '' 

# URL used for API-based NZB downloads #
API_DOWNLOAD_URL    =   ''

def Search(sender, user='', api_key='', query=''): ###TODO:: What other global-type parameters should be added? ###
    return

def Add(sender, nzb_id, user='', api_key=''):
    return

def GetNZBDetails(sender, nzb_id, user='', api_key=''):
    return

################################################################################
######## Add methods for setting provider-specific defaults below here #########
################################################################################

def SetDefaults(sender):
    return