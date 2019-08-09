from urllib.request import *
import argparse
import json
import subprocess
import os
import re

class GitHubApi:

    def __init__(self, token):
        self.token = token

    def get_repos(self, org, type="all"):
        request = self._get_request("GET", "/orgs/" + org + "/repos?type=" + type)
        response = json.loads(urlopen(request).read())
        return response

    def get_url(self, url):
        return json.loads(urlopen(self._get_full_request("GET", url)).read())

    def create_fork(self, owner, repo):
        request = self._get_request("POST", "/repos/" + owner + "/" + repo + "/forks")
        response = json.loads(urlopen(request).read())
        return response

    def raise_pr(self, owner, repo, title, body, head, base, draft=False,
                 maintainer_can_modify=True):
        headers = { "Accept": "application/vnd.github.shadow-cat-preview+json" }
        request = self._get_request("POST", "/repos/" + owner + "/" + repo +
                                    "/pulls", headers)
        data = { "title": title, "body": body, "head": head, "base": base,
                "draft": draft, "maintainer_can_modify": maintainer_can_modify }
        data = json.dumps(data).encode("utf-8")
        print("data:", data)
        return self._urlopen(request, data=data)

    def get_user(self):
        request = self._get_request("GET", "/user")
        response = json.loads(urlopen(request).read())
        return response

    def _urlopen(self, *args, **kwargs):
        return json.loads(urlopen(*args, **kwargs).read())

    def _get_request(self, method, uri, headers={}):
        return self._get_full_request(method, "https://api.github.com" + uri,
                                      headers)

    def _get_full_request(self, method, url, headers={}):
        if self.token is not None:
            headers["Authorization"] = "token " + self.token
        return Request(url, headers=headers, method=method)

def get_forks(api):
    print("reading")
    singnet_forks = api.get_repos("singnet", type="forks")
    fork_and_parent = [(repo, api.get_url(repo["url"])["parent"]) for repo in
                   singnet_forks]
    opencog_forks = filter(lambda repo : repo[1]["owner"]["login"] == "opencog",
                        fork_and_parent)
    return list(opencog_forks)

def clone_repos(api, forks):
    print("cloning")
    for singnet_repo, opencog_repo in forks:
        print(singnet_repo["name"], opencog_repo["name"])
        folder = singnet_repo["name"]
        if os.path.isdir(folder):
            print("folder exists already:", folder)
            continue
        subprocess.run(["git", "clone", singnet_repo["ssh_url"], folder])
        subprocess.run(["git", "remote", "add", "opencog",
                        opencog_repo["ssh_url"]], cwd=folder)
        mine = api.create_fork(singnet_repo["owner"]["login"],
                                singnet_repo["name"])
        subprocess.run(["git", "remote", "add", "mine", mine["ssh_url"]],
                       cwd=folder)

def fetch_repos(forks):
    print("fetching")
    for singnet_repo, opencog_repo in forks:
        print(singnet_repo["name"], opencog_repo["name"])
        folder = singnet_repo["name"]
        subprocess.run(["git", "fetch", "-p", "origin"], cwd=folder)
        subprocess.run(["git", "fetch", "-p", "opencog"], cwd=folder)
        subprocess.run(["git", "fetch", "-p", "mine"], cwd=folder)

def merge_opencog_to_singnet(forks):
    print("merging")
    for singnet_repo, opencog_repo in forks:
        print(singnet_repo["name"], opencog_repo["name"])
        folder = singnet_repo["name"]
        process = subprocess.run(["git", "rev-parse", "--verify",
                                  "merge-opencog-to-singnet"], cwd=folder)
        if process.returncode == 0:
            print("merge branch exists already")
            continue
        subprocess.run(["git", "checkout", "-b", "merge-opencog-to-singnet",
                        "origin/master"], cwd=folder)
        process = subprocess.run(["git", "pull", "opencog", "master"], cwd=folder)
        if process.returncode != 0:
            raise Exception("could not merge automatically: {} -> {}".format(
                opencog_repo["name"], singnet_repo["name"]))

def push_results(forks):
    print("push results")
    for singnet_repo, opencog_repo in forks:
        print(singnet_repo["name"], opencog_repo["name"])
        folder = singnet_repo["name"]
        process = subprocess.run(["git", "rev-parse", "--verify",
                                  "mine/merge-opencog-to-singnet"], cwd=folder)
        if process.returncode == 0:
            print("branch is pushed already")
            continue

        process = subprocess.run(["git", "push", "mine",
                                  "merge-opencog-to-singnet"], cwd=folder)
        if process.returncode != 0:
            raise Exception("could not push: {}".format(folder))

def raise_prs(api, user, forks):
    print("raise prs")
    for singnet_repo, opencog_repo in forks:
        print(singnet_repo["name"], opencog_repo["name"])
        folder = singnet_repo["name"]
        api.raise_pr("singnet", singnet_repo["name"],
                     "Merge opencog -> singnet", "",
                     user["login"] + ":merge-opencog-to-singnet", "master")

def run_ci(user, forks, args):
    print("run ci")
    parameters = {}
    url = "https://circleci.com/api/v1.1/project/github/vsbogd/opencog-integration/envvar?circle-token=" + args.circleci_token
    request = Request(url, method="POST", headers={ "Content-Type": "application/json" })
    for singnet_repo, opencog_repo in forks:
        print(singnet_repo["name"], opencog_repo["name"])
        repo_url = "https://github.com/" + user["login"] + "/" + singnet_repo["name"] + ".git"
        repo_name = opencog_repo["name"].upper()
        repo_name = re.sub(r"[^\w]", "", repo_name)
        #parameters[repo_name + "_REPO"] = repo_url
        #parameters[repo_name + "_BRANCH"] = "merge-opencog-to-singnet"
        data = json.dumps({ "name": repo_name + "_REPO",
                           "value": repo_url }).encode("utf-8")
        urlopen(request, data=data)
        data = json.dumps({ "name": repo_name + "_BRANCH",
                           "value": "merge-opencog-to-singnet" }).encode("utf-8")
        urlopen(request, data=data)
    url = "https://circleci.com/api/v1.1/project/github/vsbogd/opencog-integration/build?circle-token=" + args.circleci_token
    request = Request(url, method="POST")
    data = { "build_parameters": parameters }
    data = json.dumps(data).encode("utf-8")
    urlopen(request, data=data)

parser = argparse.ArgumentParser(description="Merge opencog to singnet")
parser.add_argument("--github-token", type=str)
parser.add_argument("--circleci-token", type=str)
parser.add_argument("--action", type=str, required=False, choices=["ci", "raise"])
args = parser.parse_args()

api = GitHubApi(args.github_token)

forks = get_forks(api)
user = api.get_user()

if args.action is None:
    clone_repos(api, forks)
    fetch_repos(forks)
    merge_opencog_to_singnet(forks)
    push_results(forks)
    run_ci(user, forks, args)
elif args.action == "ci":
    run_ci(user, forks, args)
elif args.action == "raise":
    raise_prs(api, user, forks)
    
