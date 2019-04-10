#!/usr/bin/python
import os
import sys
from optparse import OptionParser
import subprocess
import requests

def _get_project():
    git_remote = subprocess.Popen(['git', 'remote', '-v'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    git_remote = git_remote.communicate()
    url = git_remote[0].split(' ')[0]
    project = url.split('.com/')[-1]
    project = project.replace('/', '%2F').replace('.git', '')
    return project 

def main(options):
    #Vars
    api_key = os.environ['GITLAB_API_KEY']    
    source_branch = options.source_branch
    target_branch = options.target_branch
    commit_message = options.commit_message
    remove_source_branch = options.remove_source_branch

    #Commit, checkout and push
    commit = 'git commit -m "%s"' %(commit_message)
    checkout = 'git checkout -b %s' %(source_branch)
    push = 'git push origin %s' %(source_branch)
    os.system(checkout)
    os.system(commit)
    os.system(push)
    
    #Create merge request
    project = _get_project()
    url = "https://gitlab.com/api/v4/projects/%s/merge_requests" %(project)
    headers = {
        'PRIVATE-TOKEN': api_key,
    }
    data = {
        'source_branch': source_branch,
        'target_branch': target_branch,
        'title': commit_message,
        'remove_source_branch': remove_source_branch,
    }
    merge_request = requests.post(url=url, data=data, headers=headers)
    if not merge_request.ok:
        raise Exception("Error creating merge request")

    #Accept mr
    url = "https://gitlab.com/api/v4/projects/%s/merge_requests/%s/merge" %(project, mr_id)
    data = {
        'should_remove_source_branch': remove_source_branch,
    } 
    merge_request_accept = requests.put(url=url, data=data, headers=headers)
    if not merge_request.ok:
        raise Exception("Error accepting merge request")

    #Checkout again and pull
    checkout = "git checkout %s" %(target_branch)
    pull = "git pull origin %s" %(target_branch)
    os.system(checkout)
    os.system(pull)
    if remove_source_branch:
        remove_branch = "git branch -d %s" %(source_branch)

def parser(args):
    parser = OptionParser("usage: python main.py -b <source branch> -t <target branch> -c <commit message>")
    parser.add_option("-b", "--source-branch", dest="source_branch",
                      default="", type="string",
                      help="Specify the source branch")
    parser.add_option("-t", "--target-branch", dest="target_branch",
                      default="", type="string",
                      help="Specify the target branch")
    parser.add_option("-c", "--commit-message", dest="commit_message",
                      default="", type="string",
                      help="Specify the commit message")
    parser.add_option("-r", "--remove-source-branch", dest="remove_source_branch",
                      default=False, action="store_true",
                      help="Specify this argument if you want to delete the source branch after merge")
    (options, args) = parser.parse_args()
    if not options.target_branch or not options.commit_message or not options.source_branch:
        parser.error("Incorrect arguments") 
    return options

if __name__ == "__main__":
   options = parser(sys.argv)
   main(options)
