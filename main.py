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
    repo = url.split('/')[-1].replace('.git', '')
    group = url.split('/')[-2] 
    project = group + '%2F' + repo
    return project

def _get_local_url():
    git_remote = subprocess.Popen(['git', 'remote', '-v'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    git_remote = git_remote.communicate()
    url = git_remote[0].split(' ')[0]
    local_url = url.split('/')[-3]
    return local_url

def main(options):
    #Vars
    if options.envirioment:
        try:
            api_key = os.environ[options.envirioment]
        except Exception as e:
            raise Exception("Please specify a valid custom envirioment variable.")
    else:
        try:
            api_key = os.environ['GITLAB_API_KEY']    
        except Exception as e:
            raise Exception("GITLAB_API_KEY envirioment variable not found.")

    source_branch = options.source_branch
    target_branch = options.target_branch
    commit_message = options.commit_message
    remove_source_branch = options.remove_source_branch
    project = _get_project()
    local_url = _get_local_url()

    #Commit, checkout and push
    commit = 'git commit -m "%s"' %(commit_message)
    checkout = 'git checkout -b %s' %(source_branch)
    push = 'git push origin %s' %(source_branch)
    os.system(checkout)
    os.system(commit)
    os.system(push)
    
    #Create merge request
    url = "https://%s/api/v4/projects/%s/merge_requests" %(local_url, project)
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
    mr_id = merge_request.json()['iid']
    url = "https://%s/api/v4/projects/%s/merge_requests/%s/merge" %(local_url, project, mr_id)
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
        os.system(remove_branch)

def check_options(options):
    while not options.source_branch:
        options.source_branch = raw_input("Specify the source branch: ")
    while not options.target_branch:
        current_branch = subprocess.Popen(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        current_branch = current_branch.communicate()[0].split('\n')[0]
        tb = raw_input('Specify the target branch[%s]: ' %(current_branch))
        if not tb:
            options.target_branch = current_branch
    while not options.commit_message:
        options.commit_message = raw_input("Specify the commit message: ")
    return options

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
    parser.add_option("-e", "--envirioment-variable", dest="envirioment",
                      default="", type="string",
                      help="Custom envirioment varible. By default: [GITLAB_API_KEY]")
    parser.add_option("-r", "--remove-source-branch", dest="remove_source_branch",
                      default=False, action="store_true",
                      help="Specify this argument if you want to delete the source branch after merge")
    (options, args) = parser.parse_args()
    return options

if __name__ == "__main__":
   options = parser(sys.argv)
   options = check_options(options)
   main(options)
