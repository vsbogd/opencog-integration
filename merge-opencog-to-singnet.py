from urllib.request import *
import argparse
import json
import subprocess
import os
import re
import sys
import datetime
import time

MINE_REMOTE = "mine"
MINE_REMOTE_HTTPS = "mine_https"

class GitHubApi:

    def __init__(self, token):
        self.token = token

    def get_repos(self, org, type="all"):
        request = self._get_request("GET", "/orgs/" + org +
                                    "/repos?per_page=1000&type=" + type)
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

def src_dst_prj(sn_to_oc):
    src_prj = "singnet" if sn_to_oc else "opencog"
    dst_prj = "opencog" if sn_to_oc else "singnet"
    return src_prj, dst_prj

def src_dst_repo(singnet_repo, opencog_repo, sn_to_oc):
    src_repo = singnet_repo if sn_to_oc else opencog_repo
    dst_repo = opencog_repo if sn_to_oc else singnet_repo
    return src_repo, dst_repo

def merge_branch_name(src_prj, dst_prj):
    return "merge-" + src_prj + "-to-" + dst_prj

def get_forks(api, repo_names=[]):
    print("looking for opencog forks")
    singnet_forks = api.get_repos("singnet", type="forks")
    if repo_names:
        singnet_forks = [repo for repo in
                         singnet_forks if repo["name"] in repo_names]
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

def clone_repos(api, forks, sn_to_oc=False):
    print("cloning repositories:")
    for singnet_repo, opencog_repo in forks:
        src_repo, dst_repo = src_dst_repo(singnet_repo, opencog_repo, sn_to_oc)
        print(dst_repo["name"], end=": ")
        folder = dst_repo["name"]
        if os.path.isdir(folder):
            print("skip - exists already")
            continue
        run(["git", "clone", dst_repo["ssh_url"], folder])
        run(["git", "remote", "add", src_prj, src_repo["ssh_url"]], cwd=folder)
        run(["git", "remote", "add", dst_prj, dst_repo["ssh_url"]], cwd=folder)
        mine = api.create_fork(dst_repo["owner"]["login"], dst_repo["name"])
        run(["git", "remote", "add", MINE_REMOTE, mine["ssh_url"]], cwd=folder)
        run(["git", "remote", "add", MINE_REMOTE_HTTPS, mine["clone_url"]], cwd=folder)
        print("cloned")

def fetch_repos(forks, sn_to_oc=False):
    print("fetching repositories:")
    for singnet_repo, opencog_repo in forks:
        src_repo, dst_repo = src_dst_repo(singnet_repo, opencog_repo, sn_to_oc)
        print(dst_repo["name"], end=": ")
        folder = dst_repo["name"]
        run(["git", "fetch", "--all"], cwd=folder)
        print("fetched")

def remove_old_merge_branches(forks, sn_to_oc=False):
    print("remove old merge branches:")
    for singnet_repo, opencog_repo in forks:
        src_repo, dst_repo = src_dst_repo(singnet_repo, opencog_repo, sn_to_oc)
        print(dst_repo["name"], end=": ")
        folder = dst_repo["name"]
        if not branch_exists(folder, MINE_REMOTE + "/" + mrg_bch):
            print("skip - doesn't exist")
            continue
        run(["git", "checkout", "origin/master"], cwd=folder)
        run(["git", "push", MINE_REMOTE, "--delete", mrg_bch], cwd=folder)
        run(["git", "branch", "-D", mrg_bch], cwd=folder)
        print("removed")

def merge_opencog_to_singnet(forks, sn_to_oc=False):
    print("merging", src_prj, "to", dst_prj + ":")
    for singnet_repo, opencog_repo in forks:
        src_repo, dst_repo = src_dst_repo(singnet_repo, opencog_repo, sn_to_oc)
        print(src_repo["name"], "->", dst_repo["name"], end=": ")
        folder = dst_repo["name"]
        if branch_exists(folder, mrg_bch):
            print("merge branch exists already")
        else:
            run(["git", "checkout", "-b", mrg_bch, dst_prj + "/master"], cwd=folder)
        process = run(["git", "pull", src_prj, "master"], cwd=folder)
        if process.returncode != 0:
            print("could not merge automatically, please merge manually,",
                  "commit results, and restart script")
            raise Exception("could not merge automatically: {} -> {}".format(
                src_repo["name"], dst_repo["name"]))
        print("merged automatically")

def push_results(forks, sn_to_oc=False):
    print("push results:")
    for singnet_repo, opencog_repo in forks:
        dst_repo = opencog_repo if sn_to_oc else singnet_repo
        print(dst_repo["name"], end=": ")
        folder = dst_repo["name"]
        process = run(["git", "push", MINE_REMOTE, mrg_bch], cwd=folder)
        if process.returncode != 0:
            print("fail")
            raise Exception("could not push: {}".format(folder))
        print("pushed")

def raise_prs(api, user, forks, sn_to_oc=False):
    print("raise PRs")
    no_changes = []
    for singnet_repo, opencog_repo in forks:
        src_repo, dst_repo = src_dst_repo(singnet_repo, opencog_repo, sn_to_oc)
        folder = dst_repo["name"]
        process = run(["git", "diff", "--quiet", dst_prj + "/master", mrg_bch],
                      cwd=folder)
        if process.returncode == 0:
            no_changes.append(dst_repo["name"])
            continue
        else:
            print(dst_prj + "/" + dst_repo["name"], "<-",
                  src_prj + "/" + opencog_repo["name"])
        api.raise_pr(dst_prj, dst_repo["name"],
                     "Merge " + src_prj + " -> " + dst_prj, "",
                     user["login"] + ":" + mrg_bch, "master")
    print("no changes for repos:", no_changes)

def run_ci(forks, branch, user=None, sn_to_oc=False):
    print("run CI")
    parameters = {}
    url = "https://circleci.com/api/v1.1/project/github/vsbogd/opencog-integration/envvar?circle-token=" + args.circleci_token
    request = Request(url, method="POST", headers={ "Content-Type": "application/json" })
    print("set build parameters")
    for singnet_repo, opencog_repo in forks:
        src_repo, dst_repo = src_dst_repo(singnet_repo, opencog_repo, sn_to_oc)
        if user is not None:
            repo = dst_repo["name"] if user != src_prj else src_repo["name"]
            repo_url = "https://github.com/" + user + "/" + repo + ".git"
        else:
            folder = dst_repo["name"]
            process = run(["git", "remote", "get-url", MINE_REMOTE_HTTPS],
                    stdout=subprocess.PIPE, cwd=folder)
            if process.returncode != 0:
                raise Exception("could not get name of the fork which contains the merge result")
            repo_url = process.stdout.decode("utf-8").strip()

        repo_name = src_repo["name"].upper()
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

def tag_origin_master(forks, tag, sn_to_oc=False):
    if tag is None:
        raise Exception("Tag is not specified")
    print("tagging master, tag: {}".format(tag))
    for singnet_repo, opencog_repo in forks:
        src_repo, dst_repo = src_dst_repo(singnet_repo, opencog_repo, sn_to_oc)
        print(singnet_repo["name"], end=": ")
        folder = singnet_repo["name"]
        process = subprocess.run(["git", "rev-parse", "--verify", tag],
                                 stderr=subprocess.STDOUT,
                                 stdout=subprocess.DEVNULL, cwd=folder)
        if process.returncode == 0:
            print("skip - tagged already")
            continue

        process = run(["git", "tag", tag, dst_repo + "/master"], cwd=folder)
        if process.returncode != 0:
            print("fail")
            raise Exception("could not create tag: {}".format(folder))
        process = run(["git", "push", dst_prj, tag], cwd=folder)
        if process.returncode != 0:
            print("fail, could not push")
        else:
            print("tagged")

def check_process(process, message):
    if process.returncode != 0:
        print("fail")
        raise Exception(message)

def tag_and_push_docker(image_name, origin, tags):
    for tag in tags:
        process = run(["docker", "tag", image_name + ":" + origin, image_name + ":" + tag])
        check_process(process, "could not tag " + image_name + ":" + origin)
        process = run(["docker", "push", image_name + ":" + tag])
        check_process(process, "could not push " + image_name + ":" + tag
                + ", are you logged in to the dockerhub?")
    process = run(["docker", "push", image_name + ":" + origin])
    check_process(process, "could not push " + image_name + ":" + origin
            + ", are you logged in to the dockerhub?")

def publish_dockers(tag):
    if tag is None:
        raise Exception("Tag is not specified")

    print("building singularitynet/opencog-deps image, tag: {}".format(tag));
    ocpkg_url = "https://raw.githubusercontent.com/singnet/ocpkg/" + tag + "/ocpkg"
    print("ocpkg URL: {}".format(ocpkg_url))
    process = run(["./docker-build.sh", "-b"], cwd="opencog-docker/opencog",
                  env={ "OCPKG_URL": ocpkg_url }, stdout=sys.stdout)
    check_process(process, "could not build singularitynet/opencog-deps docker image")
    tag_and_push_docker("singularitynet/opencog-deps", "latest", [tag])

    print("building singularitynet/cogutil image, tag: {}".format(tag));
    process = run(["./docker-build.sh", "-c"], cwd="opencog-docker/opencog",
                  stdout=sys.stdout)
    check_process(process, "could not build singularitynet/cogutil docker image")
    tag_and_push_docker("singularitynet/cogutil", "latest", [tag])

    print("building singularitynet/relex image, tag: {}".format(tag));
    print("relex tag: {}".format(tag))
    process = run(["./docker-build.sh", "-r"], cwd="opencog-docker/opencog",
                  env={ "RELEX_REPO": "https://github.com/singnet/relex",
                       "RELEX_BRANCH": tag }, stdout=sys.stdout)
    check_process(process, "could not build singularitynet/relex docker image")
    tag_and_push_docker("singularitynet/relex", "latest", [tag])

    print("building singularitynet/postgres image, tag: {}".format(tag));
    atom_sql_url = ("https://raw.githubusercontent.com/singnet/atomspace/" + tag
                    + "/opencog/persist/sql/multi-driver/atom.sql")
    print("atomspace SQL URL: {}".format(atom_sql_url))
    process = run(["./docker-build.sh", "-p"], cwd="opencog-docker/opencog",
                  env={ "ATOM_SQL_URL": atom_sql_url },
                  stdout=sys.stdout)
    check_process(process, "could not build singularitynet/postgres docker image")
    tag_and_push_docker("singularitynet/postgres", "latest", [tag])

    print("building singularitynet/opencog-dev image, tag: {}".format(tag));
    process = run(["./docker-build.sh", "-t"], cwd="opencog-docker/opencog",
                  stdout=sys.stdout)
    check_process(process, "could not build singularitynet/opencog-dev docker image")
    tag_and_push_docker("singularitynet/opencog-dev", "cli", [tag, "latest"])


parser = argparse.ArgumentParser(description="Merge opencog to singnet")
parser.add_argument("--github-token", type=str)
parser.add_argument("--circleci-token", type=str)
parser.add_argument("--action", type=str, required=False, default="merge",
                    choices=["merge", "release", "fetch", "ci", "pr", "clean",
                        "tag", "docker"])
parser.add_argument("--ci-fork", type=str, required=False)
parser.add_argument("--ci-branch", type=str, required=False)
parser.add_argument("--tag", type=str, required=False)
parser.add_argument("--forks", type=str, required=False)
parser.add_argument("--singnet-to-opencog", action="store_true")
parser.set_defaults(singnet_to_opencog=False)
args = parser.parse_args()

api = GitHubApi(args.github_token)

repo_names = args.forks.split(',') if args.forks else None

user = api.get_user()
print("current git user:", user["login"])

src_prj, dst_prj = src_dst_prj(args.singnet_to_opencog)
mrg_bch = merge_branch_name(src_prj, dst_prj)

if args.ci_branch is None:
    args.ci_branch = mrg_bch
if args.ci_fork is None:
    args.ci_fork = user["login"]

if args.action == "merge":
    forks = get_forks(api, repo_names)
    clone_repos(api, forks, args.singnet_to_opencog)
    fetch_repos(forks, args.singnet_to_opencog)
    merge_opencog_to_singnet(forks, args.singnet_to_opencog)
    push_results(forks, args.singnet_to_opencog)
    run_ci(forks, mrg_bch, sn_to_oc=args.singnet_to_opencog)
elif args.action == "release":
    tag = args.tag
    if tag is None:
        tag = "release-" + datetime.date.today().strftime("%Y%m%d")
    print("releasing {} tag".format(tag))
    print("last chance to exit, waiting for 10 seconds...")
    time.sleep(10)
    forks = get_forks(api, repo_names)
    if not args.singnet_to_opencog:
        tag_origin_master(forks, tag, args.singnet_to_opencog)
    publish_dockers(tag)
elif args.action == "fetch":
    forks = get_forks(api, repo_names)
    clone_repos(api, forks, args.singnet_to_opencog)
    fetch_repos(forks, args.singnet_to_opencog)
elif args.action == "ci":
    forks = get_forks(api, repo_names)
    run_ci(forks, args.ci_branch, user=args.ci_fork,
           sn_to_oc=args.singnet_to_opencog)
elif args.action == "pr":
    forks = get_forks(api, repo_names)
    raise_prs(api, user, forks, args.singnet_to_opencog)
elif args.action == "clean":
    forks = get_forks(api)
    remove_old_merge_branches(forks, args.singnet_to_opencog)
elif args.action == "tag":
    forks = get_forks(api, repo_names)
    tag_origin_master(forks, args.tag, args.singnet_to_opencog)
elif args.action == "docker":
    publish_dockers(args.tag)
