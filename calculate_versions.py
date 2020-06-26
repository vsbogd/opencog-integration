import os
import sys
import subprocess
import hashlib

def log(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

opencog_dependencies={
    'opencogdeps': [ 'repo/ocpkg', 'repo/docker' ],
    'relex': [ 'repo/relex', 'repo/docker' ],
    'postgres': [ 'repo/atomspace', 'repo/docker' ],
    'cogutil': [ 'repo/cogutil', 'opencogdeps' ],
    'atomspace': [ 'repo/atomspace', 'opencogdeps', 'postgres', 'cogutil' ],
    'opencog': [ 'repo/opencog', 'opencogdeps', 'relex', 'cogutil', 'atomspace', 'ure', 'pln', 'cogserver', 'attention' ],
    'moses': [ 'repo/moses', 'opencogdeps', 'cogutil' ],
    'asmoses': [ 'repo/asmoses', 'opencogdeps', 'cogutil', 'atomspace' ],
    'ure': [ 'repo/ure', 'opencogdeps', 'cogutil', 'atomspace' ],
    'miner': [ 'repo/miner', 'opencogdeps', 'cogutil', 'atomspace', 'ure' ],
    'learn': [ 'repo/learn', 'opencogdeps', 'postgres', 'cogutil', 'atomspace', 'cogserver', 'opencog' ],
    'attention': [ 'repo/attention', 'opencogdeps', 'cogutil', 'atomspace', 'cogserver' ],
    'cogserver': [ 'repo/cogserver', 'opencogdeps', 'cogutil', 'atomspace' ],
    'pln': [ 'repo/pln', 'opencogdeps', 'cogutil', 'atomspace', 'ure' ],
    'visualization': [ 'repo/visualization', 'opencogdeps', 'cogutil', 'atomspace', 'cogserver' ],
    'patternindex': [ 'repo/patternindex', 'opencogdeps', 'cogutil', 'atomspace' ],
    'spacetime': [ 'repo/spacetime', 'opencogdeps', 'cogutil', 'atomspace' ]
}

def get_env_prefix(project):
    return project.upper()

def get_repo(project):
    return os.environ[get_env_prefix(project) + '_REPO']

def get_branch(project):
    return os.environ[get_env_prefix(project) + '_BRANCH']

def get_head_commit_id(project):
    repo = get_repo(project)
    branch = get_branch(project)
    result = subprocess.run(['git', 'ls-remote', repo, branch],
            stdout=subprocess.PIPE)
    if len(result.stdout) == 0:
        raise Exception('Unknown repo/branch for a project: {}, repo: {},' +
                'branch: {}'.format(project, repo, branch))
    return result.stdout.decode('utf-8').split()[0]

class Versions:

    def __init__(self, dependencies):
        self.dependencies = dependencies
        self.cache = {}

    def _get_version(self, project):
        if project.startswith('repo/'):
            return get_head_commit_id(project[5:]), ''

        deps = ''
        for dep in self.dependencies[project]:
            dep_version = self.get_version(dep)
            deps = deps + dep + ':' + dep_version + '\n'

        version = hashlib.sha1(deps.encode('utf-8')).hexdigest()
        return version, deps

    def get_version(self, project):
        if project in self.cache:
            return self.cache[project]
        else:
            version, deps = self._get_version(project)
            log("project:", project)
            log("deps:", deps)
            log("version:", version)
            self.cache[project] = version
            return version

def main():
    versions = Versions(opencog_dependencies)
    for project in opencog_dependencies.keys():
        version = versions.get_version(project)
        print(project.upper() + '_VERSION=' + version)

if __name__ == '__main__':
    main()
