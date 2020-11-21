from datetime import datetime

from bcolor import bcolor
from phase2.getValidInput import getValidInput
from phase2.postQA import genID

def votePost(votes, uid, targetPid):
	print(bcolor.pink('\n< Vote on a Post >'))
	
	cursor = votes.find_one({"$and": [{"UserId": uid}, {"PostId": targetPid}]})
	
	if cursor:
		print(bcolor.errmsg("error: you've already voted on this post."))
	else:
		prompt = '\nConfirmation: Do you want to vote on this post? [y/n] '
		
		uin = getValidInput(prompt, ['y', 'n'])
		
		if uin == 'y':
			
			vid = genID(votes)
			crdate = str(datetime.now())
			
			vote = {
				"Id"          : vid,
				"PostId"      : targetPid,
				"VoteTypeId"  : 2,
				"CreationDate": crdate
			}
			
			if uid:
				vote['UserId'] = uid
			
			votes.insert_one(vote)
			print(bcolor.green('\nVoting Completed!'))
	
	print()