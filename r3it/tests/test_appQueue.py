import io, pytest
from .testHelpers import *
from appQueue import *
from r3it import web

# -----------------------------------------------------------------------

def test_authorizedToViewUtilityRole():
    createFakeApp()
    app = appDict(fakeApp['ID'])
    authorized = authorizedToView(fakePriviledgedEmail,app)
    assert( authorized == True )
    deleteFakeApp()
    
def test_authorizedToViewOwner():
    createFakeApp()
    app = appDict(fakeApp['ID'])
    authorized = authorizedToView(fakeEmail,app)
    assert( authorized == True )
    deleteFakeApp()

def test_authorizedToViewInvalid():
    createFakeApp()
    nonOwnerEmail = 'nonowner@email.com'
    app = appDict(fakeApp['ID'])
    authorized = authorizedToView(nonOwnerEmail,app)
    assert( authorized == False )
    deleteFakeApp()

def test_userAppIDs():
    createFakeApp()
    assert( userAppIDs(fakeEmail) == [fakeApp['ID']] )
    deleteFakeApp()

def test_userAppIDsNoApps():
    createFakeApp()
    assert( userAppIDs(fakePriviledgedEmail) == [] )
    deleteFakeApp()

def test_allAppIDs():
    oldAppIDs = allAppIDs()
    createFakeApp()
    foundAppIDS = allAppIDs()
    fakeAppIDs = [ fakeApp['ID'] ]
    assert( set(foundAppIDS) == set(oldAppIDs+fakeAppIDs) )
    deleteFakeApp()

def test_appExistsTrue():
    createFakeApp()
    assert( appExists(fakeApp['ID']) == True )
    deleteFakeApp()

def test_appExistsFalse():
    assert( appExists(fakeApp['ID']) == False )

def test_allAppDirs(): 
    oldAppPaths = allAppDirs()
    fakeIDs = ['123','234','345']
    newAppPaths = []
    for id in fakeIDs: 
        createFakeApp(id=id)
        newAppPaths.append(os.path.join(APPLICATIONS_DIR,id))
    foundAppPaths = allAppDirs()
    assert( set(foundAppPaths) == set(oldAppPaths+newAppPaths) )
    for id in fakeIDs: deleteFakeApp(id)

def test_allAppUploads():

    createFakeUser()
    createFakeApp()

    uploadData = []
    fileType = 'One Line Diagram'
    files = ['img1.jpg','img2.jpg','img3.jpg']
    for fileName in files:
        uploadData.append({ 'file': (io.BytesIO(b"abcdef"), fileName) })

    web.app.config['TESTING'] = True
    with web.app.test_client() as client:
        loginFakeUser(client,fakeEmail)
        for entry in uploadData:
            response = client.post('/upload/'+fakeApp['ID']+'/'+fileType, \
                data=entry, follow_redirects=True) 
    uploads = allAppUploads(fakeApp['ID'])
    assert(uploads[fileType]==files)

    deleteFakeUser()
    deleteFakeApp()

def test_allAppPaths():

    oldAppPaths = allAppPaths()
    fakeIDs = ['123','234','345']
    newAppPaths = []
    for id in fakeIDs: 
        createFakeApp(id=id)
        newAppPaths.append(os.path.join(APPLICATIONS_DIR,id,'application.json'))
    foundAppPaths = allAppPaths()
    assert( set(foundAppPaths) == set(oldAppPaths+newAppPaths) )
    for id in fakeIDs: deleteFakeApp(id)

def test_requiresUsersActionMember():
    
    functionOutputs, desiredOutputs = [], []
    for role in actionItems.keys():
    
        if role == 'member': email = fakeEmail
        elif role == 'engineer': email = 'engineer2@electric.coop'
        elif role == 'memberServices': email = 'ms@electric.coop'
            
        for status in statuses:
            fakeApp['Status'] = status
            functionOutputs.append( requiresUsersAction(email, fakeApp) )
            if status in actionItems[role]: desiredOutputs.append(True)
            else: desiredOutputs.append(False)

    assert(functionOutputs==desiredOutputs)

def test_appDir():
    assert(appDir(fakeApp['ID'])==os.path.join(APPLICATIONS_DIR,fakeApp['ID']))

def test_appPath():
    assert( appPath(fakeApp['ID']) == \
        os.path.join( APPLICATIONS_DIR, fakeApp['ID'],'application.json' )
    )

def test_appFileReadNonExistant():
    with pytest.raises(FileNotFoundError):
        file = appFile(fakeApp['ID'])
    
def test_appFileWriteNonExistant(): 
    with pytest.raises(FileNotFoundError):
        file = appFile(fakeApp['ID'],'w')

def test_appFileReadExistant(): 
    createFakeApp()
    with appFile(fakeApp['ID']) as file:
        assert( file.name == appPath(fakeApp['ID']) )
    deleteFakeApp()

def test_appFileWriteExistant(): 
    createFakeApp()
    with appFile(fakeApp['ID'],'w') as file:
        assert( file.name == appPath(fakeApp['ID']) )
    deleteFakeApp()

def test_appDict():
    createFakeApp()
    app = appDict(fakeApp['ID'])
    assert( app == fakeApp )
    deleteFakeApp()

def test_appEditsPath():
    assert( appEditsPath(fakeApp['ID']) == \
        os.path.join( APPLICATIONS_DIR, fakeApp['ID'],'edits.json' )
    )

def test_appEditsFileReadNonExistant():
    with pytest.raises(FileNotFoundError):
        file = appEditsFile(fakeApp['ID'])
    
def test_appEditsFileWriteNonExistant(): 
    with pytest.raises(FileNotFoundError):
        file = appEditsFile(fakeApp['ID'],'w')

def test_appEditsFileReadExistant(): 
    createFakeApp()
    with appEditsFile(fakeApp['ID'],'w') as newFile: pass
    with appEditsFile(fakeApp['ID']) as readFile:
        assert( readFile.name == appEditsPath(fakeApp['ID']) )
    deleteFakeApp()

def test_appEditsFileWriteExistant(): 
    createFakeApp()
    with appEditsFile(fakeApp['ID'],'w') as newFile: pass
    with appEditsFile(fakeApp['ID'],'w') as writeFile:
        assert( writeFile.name == appEditsPath(fakeApp['ID']) )
    deleteFakeApp()

def test_appEditsDict():
    createFakeApp()
    editDict = {'Status': 'Edited Status'}
    with appEditsFile(fakeApp['ID'],'w') as newFile: 
        json.dump(editDict,newFile)
    appEdits = appEditsDict(fakeApp['ID'])
    assert( appEdits == editDict )
    deleteFakeApp()

def test_appQueue():
    
    oldAppIDs = allAppIDs()
    
    fakeIDs = ['123','9999999999999999999','345','234']    
    sortedFakeIDs = sorted(fakeIDs)
    for id in fakeIDs: createFakeApp(id=id)
    
    foundApps = appQueue()

    index = 0
    allMatch = True
    for app in foundApps:
        if app['ID'] not in oldAppIDs:
            if app != appDict(sortedFakeIDs[index]):
                allMatch = False
                break
            index += 1

    assert( allMatch )
    for id in fakeIDs: deleteFakeApp(id)
