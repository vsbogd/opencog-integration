from urllib.request import *
import argparse
import json
import subprocess
import os

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

    def raise_pr(self, owner, repo, title, body, head, base):
        request - self._get_request("POST", "/repos/" + owner + "/" + repo + "/pulls")
        data = { "title": title, "body": body, "head": head, "base": base }
        return self._urlopen(request, data=data)

    def _urlopen(self, *args, **kwargs):
        return json.loads(urlopen(*args, **kwargs).read())

    def _get_request(self, method, uri):
        return self._get_full_request(method, "https://api.github.com" + uri)

    def _get_full_request(self, method, url):
        headers = {}
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
        subprocess.run(["git", "fetch", "origin"], cwd=folder)
        subprocess.run(["git", "fetch", "opencog"], cwd=folder)
        subprocess.run(["git", "fetch", "mine"], cwd=folder)

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
            print("Could not merge automatically:", opencog_repo["name"] + " -> " +
                  singnet_repo["name"])
            return

parser = argparse.ArgumentParser(description="Merge opencog to singnet")
parser.add_argument("--token", type=str)
args = parser.parse_args()

api = GitHubApi(args.token)

forks = get_forks(api)
clone_repos(api, forks)
fetch_repos(forks)
merge_opencog_to_singnet(forks)
