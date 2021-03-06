from datetime import datetime

from pymongo.collation import Collation

from phase1.extractTermsFrom import extractTermsFrom
from phase2.getValidInput import getValidInput
from bcolor.bcolor import warning, green, pink


def postQ(db, maxIdDict, uid) -> bool:
    '''
    Prompts the user for a question post with title, body, tags(optional)
    Inserts the post info into "posts" collection, with a unique pid generated by the system
    If there is at least one tag, inserts the tag info into "tags" collection, with a unique tagId

    Inputs:
        db -- pymongo.database.Database
        maxIdDict -- dict
        uid -- str
    Return:
        bool
    '''
    print(pink('\n< Post a Question >'))

    postsColl = db['posts']
    tagsColl = db['tags']
    pid = str(maxIdDict['posts'] + 1)
    maxIdDict['posts'] += 1

    posted = None
    while posted is None:
        
        title = input("Enter your title: ")
        body = input("Enter your body text: ")
        tagSet = getTags()
        crdate = str(datetime.now()).replace(' ', 'T')[:-3]

        if confirmInfo(title, body, tagSet):

            post = createQDict(pid, crdate, body, title, uid)

            # delete OwnerUserId field if user is anonymous
            if uid == '':
                del post['OwnerUserId'] 
            
            terms = extractTermsFrom(post)
            if len(terms) > 0:
                post['terms'] = terms

            # add Tags if the user enters at least one tag
            if tagSet:
                post['Tags'] = '<' + '><'.join(tagSet) + '>'
                insertTags(tagsColl, tagSet, maxIdDict)
                
            postsColl.insert_one(post)

            print(green("\nQuestion Posted!"))

            posted = True
        
        else:
            prompt = warning("Do you still want to post a question? [y/n] ")
            if getValidInput(prompt, ['y', 'n']) == 'n':
                posted = False

    return posted
        

def postAns(posts, maxIdDict, uid, targetPid) -> bool:
    '''
    Prompts the user for a answer post with body for the selected question post
    Inserts the post info into "posts" collection, with a unique pid generated by the system

    Inputs:
        posts -- pymongo.collection.Collection
        maxIdDict -- dict
        uid -- str
        targetPid -- str
    Return:
        bool
    '''
    print(pink('\n< Post an Answer >'))

    pid = str(maxIdDict['posts'] + 1) 
    maxIdDict['posts'] += 1

    posted = None
    while posted is None:
        
        body = input("Enter your body text: ")
        crdate = str(datetime.now()).replace(' ', 'T')[:-3]

        prompt = warning('Do you want to post this answer to the selected post? [y/n] ')
        
        if getValidInput(prompt, ['y','n']) == 'y':

            post = createAnsDict(pid, targetPid, crdate, body, uid)

            # delete OwnerUserId field if user is anonymous
            if uid == '':
                del post['OwnerUserId'] 

            terms = extractTermsFrom(post)
            if len(terms) > 0:
                post["terms"] = terms
                
            posts.insert_one(post)

            # increments AnswerCount of the question post
            incAnswerCount(posts, targetPid)

            print(green("\nAnswer Posted!"))
            posted = True

        else:
            prompt = warning("Do you still want to post an answer? [y/n] ")
            if getValidInput(prompt, ['y', 'n']) == 'n':
                posted = False

    return posted



def getTags() -> set:
    '''
    Prompts the user to enter zero or more tags and creates a tag set
    Return:
        tagSet -- set
    '''

    tags = input("Enter zero or more tags, each separated by a comma: ")

    tagSet = {
                tag.strip().lower()
                for tag in tags.split(',')
                if tag != ''
             }

    return tagSet


def createQDict(pid, crdate, body, title, uid):
    '''
    Returns a question dict which contains the fields that all of the question posts need.
    '''
    return {
                "Id": pid,
                "PostTypeId": "1",
                "CreationDate": crdate,
                "LastActivityDate": crdate,
                "OwnerUserId": uid,
                "Score": 0,
                "ViewCount": 0,
                "Body": body,
                "Title": title,
                "AnswerCount": 0,
                "CommentCount": 0,
                "FavoriteCount": 0,
                "ContentLicense": "CC BY-SA 2.5"
            }


def createAnsDict(pid, targetPid, crdate, body, uid):
    '''
    Returns an answer dict which contains the fields that all of the answer posts need.
    '''
    return {
                "Id": pid,
                "PostTypeId": "2",
                "OwnerUserId": uid,
                "ParentId": targetPid,
                "CreationDate": crdate,
                "LastActivityDate": crdate,
                "Body": body,
                "Score": 0,
                "CommentCount": 0,
                "ContentLicense": "CC BY-SA 2.5"
            }
    

def insertTags(tagsColl, tags, maxIdDict):
    '''
    Checks if the tags the user has entered already exists in tags collection
    Increments its count by one if exists; otherwise inserts a new doc with the tagName provided in the collection
    '''
    for tagName in tags:
        cursor = tagsColl.find({"TagName": tagName}).collation(Collation(locale='en', strength=2))

        if len(list(cursor)) > 0:
            tagsColl.update({"TagName": tagName},{"$inc": {"Count": 1}})
        else:
            tagId = str(maxIdDict['tags'] + 1)
            maxIdDict['tags'] += 1
            tag = {
                "Id": tagId,
                "TagName": tagName,
                "Count": 1
            }
            tagsColl.insert_one(tag)


def incAnswerCount(posts, targetPid):
    '''
    Increments AnswerCount of the selected question post by one when an answer post is made.
    Inputs:
        posts -- pymongo.collection.Collection
        targetPid -- str
    '''
    posts.update({"Id": targetPid}, {"$inc": {"AnswerCount": 1}})


def confirmInfo(title, body, tags) -> bool:
    '''
    Confirms the user if the entered info is correct

    Inputs:
        title -- str
        body -- str
        tags -- str
    Return:
        bool
    '''
    tags = 'N/A' if len(tags) == 0 else ', '.join(tags)

    print(warning("\nPlease double check your information:"))
    print()
    print("     Title: {}".format(title))
    print("     Body: {}".format(body))
    print("     Tags: {}".format(tags))
    print()

    prompt = "Is this correct? [y/n] "
    uin = getValidInput(prompt, ['y','n'])

    return True if uin == 'y' else False
