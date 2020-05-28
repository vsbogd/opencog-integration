from urllib.request import *
import argparse
import json
import subprocess
import os
import re

MERGE_BRANCH = "merge-opencog-to-singnet"
MINE_REMOTE = "mine"
MINE_REMOTE_HTTPS = "mine_https"

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

def branch_exists(folder, branch):
    process = subprocess.run(["git", "rev-parse", "--verify", branch],
                              stderr=subprocess.STDOUT,
                              stdout=subprocess.DEVNULL, cwd=folder)
    return process.returncode == 0

def run(cmd, stdout=subprocess.DEVNULL, **kargs):
    return subprocess.run(cmd, stderr=subprocess.STDOUT,
                          stdout=stdout, **kargs)

def get_forks(api):
    print("looking for opencog forks")
    singnet_forks = api.get_repos("singnet", type="forks")
    fork_and_parent = [(repo, api.get_url(repo["url"])["parent"]) for repo in
                   singnet_forks]
    opencog_forks = filter(lambda repo : repo[1]["owner"]["login"] == "opencog",
                        fork_and_parent)
    opencog_forks = list(opencog_forks)
    print("forks found:", [repo[0]["name"] + ("(archived)" if repo[0]["archived"]
                           or repo[1]["archived"] else "") for repo in
                           opencog_forks])
    opencog_forks = list(filter(lambda repo : not repo[0]["archived"] and not
                           repo[1]["archived"], opencog_forks))
    return opencog_forks

def clone_repos(api, forks):
    print("cloning repositories:")
    for singnet_repo, opencog_repo in forks:
        print(singnet_repo["name"], end=": ")
        folder = singnet_repo["name"]
        if os.path.isdir(folder):
            print("skip - exists already")
            continue
        run(["git", "clone", singnet_repo["ssh_url"], folder])
        run(["git", "remote", "add", "opencog", opencog_repo["ssh_url"]], cwd=folder)
        mine = api.create_fork(singnet_repo["owner"]["login"], singnet_repo["name"])
        run(["git", "remote", "add", MINE_REMOTE, mine["ssh_url"]], cwd=folder)
        run(["git", "remote", "add", MINE_REMOTE_HTTPS, mine["clone_url"]], cwd=folder)
        print("cloned")

def fetch_repos(forks):
    print("fetching repositories:")
    for singnet_repo, _ in forks:
        print(singnet_repo["name"], end=": ")
        folder = singnet_repo["name"]
        run(["git", "fetch", "-all"], cwd=folder)
        print("fetched")

def remove_old_merge_branches(forks):
    print("remove old merge branches:")
    for singnet_repo, _ in forks:
        print(singnet_repo["name"], end=": ")
        folder = singnet_repo["name"]
        if not branch_exists(folder, MINE_REMOTE + "/" + MERGE_BRANCH):
            print("skip - doesn't exist")
            continue
        run(["git", "checkout", "origin/master"], cwd=folder)
        run(["git", "push", MINE_REMOTE, "--delete", MERGE_BRANCH], cwd=folder)
        run(["git", "branch", "-D", MERGE_BRANCH], cwd=folder)
        print("removed")

def merge_opencog_to_singnet(forks):
    print("merging opencog to singnet:")
    for singnet_repo, opencog_repo in forks:
        print(opencog_repo["name"], "->", singnet_repo["name"], end=": ")
        folder = singnet_repo["name"]
        if branch_exists(folder, MERGE_BRANCH):
            print("merge branch exists already")
        else:
            run(["git", "checkout", "-b", MERGE_BRANCH, "origin/master"], cwd=folder)
        process = run(["git", "pull", "opencog", "master"], cwd=folder)
        if process.returncode != 0:
            print("could not merge automatically, please merge manually,",
                  "commit results, and restart script")
            raise Exception("could not merge automatically: {} -> {}".format(
                opencog_repo["name"], singnet_repo["name"]))
        print("merged automatically")

def push_results(forks):
    print("push results:")
    for singnet_repo, opencog_repo in forks:
        print(singnet_repo["name"], end=": ")
        folder = singnet_repo["name"]
        if branch_exists(folder, MINE_REMOTE + "/" + MERGE_BRANCH):
            print("skip - pushed already")
            continue

        process = run(["git", "push", MINE_REMOTE, MERGE_BRANCH], cwd=folder)
        if process.returncode != 0:
            print("fail")
            raise Exception("could not push: {}".format(folder))
        print("pushed")

def raise_prs(api, user, forks):
    print("raise PRs")
    no_changes = []
    for singnet_repo, opencog_repo in forks:
        folder = singnet_repo["name"]
        process = run(["git", "diff", "--quiet", "origin/master",
                       MERGE_BRANCH], cwd=folder)
        if process.returncode == 0:
            no_changes.append(singnet_repo["name"])
            continue
        else:
            print("singnet/" + singnet_repo["name"], "<-", "opencog/" +
                  opencog_repo["name"])
        api.raise_pr("singnet", singnet_repo["name"],
                     "Merge opencog -> singnet", "",
                     user["login"] + ":merge-opencog-to-singnet", "master")
    print("no changes for repos:", no_changes)

def run_ci(forks, branch, user=None):
    print("run CI")
    parameters = {}
    url = "https://circleci.com/api/v1.1/project/github/vsbogd/opencog-integration/envvar?circle-token=" + args.circleci_token
    request = Request(url, method="POST", headers={ "Content-Type": "application/json" })
    print("set build parameters")
    for singnet_repo, opencog_repo in forks:
        if user is not None:
            repo = singnet_repo["name"] if user != "opencog" else opencog_repo["name"]
            repo_url = "https://github.com/" + user + "/" + repo + ".git"
        else:
            folder = singnet_repo["name"]
            process = run(["git", "remote", "get-url", MINE_REMOTE_HTTPS],
                    stdout=subprocess.PIPE, cwd=folder)
            if process.returncode != 0:
                raise Exception("could not get name of the fork which contains the merge result")
            repo_url = process.stdout.decode("utf-8").strip()

        repo_name = opencog_repo["name"].upper()
        repo_name = re.sub(r"[^\w]", "", repo_name)
        #parameters[repo_name + "_REPO"] = repo_url
        #parameters[repo_name + "_BRANCH"] = branch
        data = json.dumps({ "name": repo_name + "_REPO",
                           "value": repo_url }).encode("utf-8")
        urlopen(request, data=data)
        data = json.dumps({ "name": repo_name + "_BRANCH",
                           "value": branch }).encode("utf-8")
        urlopen(request, data=data)
        print(repo_name + "_REPO:", repo_url)
        print(repo_name + "_BRANCH:", branch)
    url = "https://circleci.com/api/v1.1/project/github/vsbogd/opencog-integration/build?circle-token=" + args.circleci_token
    request = Request(url, method="POST")
    #data = { "build_parameters": parameters }
    #data = json.dumps(data).encode("utf-8")
    print("trigger build using CircleCI API: POST", url)
    urlopen(request, data=data)

def tag_origin_master(forks, tag):
    if tag is None:
        raise Exception("Tag is not specified")
    print("tagging master, tag: {}".format(tag))
    for singnet_repo, opencog_repo in forks:
        print(singnet_repo["name"], end=": ")
        folder = singnet_repo["name"]
        process = subprocess.run(["git", "rev-parse", "--verify", tag],
                                 stderr=subprocess.STDOUT,
                                 stdout=subprocess.DEVNULL, cwd=folder)
        if process.returncode == 0:
            print("skip - tagged already")
            continue

        process = run(["git", "tag", tag, "origin/master"], cwd=folder)
        if process.returncode != 0:
            print("fail")
            raise Exception("could not create tag: {}".format(folder))
        process = run(["git", "push", "origin", tag], cwd=folder)
        if process.returncode != 0:
            print("fail, could not push")
        else:
            print("tagged")

parser = argparse.ArgumentParser(description="Merge opencog to singnet")
parser.add_argument("--github-token", type=str)
parser.add_argument("--circleci-token", type=str)
parser.add_argument("--action", type=str, required=False, default="merge",
                    choices=["fetch", "merge", "ci", "pr", "clean", "tag"])
parser.add_argument("--ci-fork", type=str, required=False)
parser.add_argument("--ci-branch", type=str, required=False, default=MERGE_BRANCH)
parser.add_argument("--tag", type=str, required=False)
args = parser.parse_args()

api = GitHubApi(args.github_token)

forks = get_forks(api)
user = api.get_user()
print("current git user:", user["login"])
if args.ci_fork is None:
    args.ci_fork = user["login"]

if args.action == "merge":
    clone_repos(api, forks)
    fetch_repos(forks)
    merge_opencog_to_singnet(forks)
    push_results(forks)
    run_ci(forks, MERGE_BRANCH)
elif args.action == "fetch":
    clone_repos(api, forks)
    fetch_repos(forks)
elif args.action == "ci":
    run_ci(forks, args.ci_branch, user=args.ci_fork)
elif args.action == "pr":
    raise_prs(api, user, forks)
elif args.action == "clean":
    remove_old_merge_branches(forks)
elif args.action == "tag":
    tag_origin_master(forks, args.tag)
