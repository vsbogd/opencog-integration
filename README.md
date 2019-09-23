# Overview

Opencog components dependency graph:

![opencog components dependency graph](https://www.plantuml.com/plantuml/svg/XLJBJiGm3BpdA_83WJlYi19y07V4mMrDDceU9N7HIeX_nvjqTvqAH2-9nsCxcObwA0IPrk2L8aSUzGkCCrWiskYd59OKCP9-Tc0p1AN6AvJ6PROYVjM4XSm410Mfw3SDfK8NH70pUZoffKtIKnfdpFfBQVvamxHW79EztrOpS9_MTqFEm9zLTKX7RsF_uY-f45DALt81_ptRX9zT8SVgMroPePMS5qX81QKeG2aKrWG5jcOP1HSnTvA3TMPmgKtcWFTzlfWwPYEK_So1pteCa6TfRBk0G3n2ZbrVF17c2DvGIfwxTqbxPD7CaDt4vlOf3z6kxBcfBLsqd5Vr9Ub7OpfRvTEHoREmpLe1DcT5UKtUDAzhnQJADxJfilDynx_kvE0hzw4nxyg7r-yv1HsWi4QxghEVFRAPjWCtethqPjQlHr7Sl5scFXEfJ4VRreerPzK1uyI_W1y0)

[source code](https://www.planttext.com/?text=XLJBJiGm3BpdA_83WJlYi19y07V4mMrDDceU9N7HIeX_nvjqTvqAH2-9nsCxcObwA0IPrk2L8aSUzGkCCrWiskYd59OKCP9-Tc0p1AN6AvJ6PROYVjM4XSm410Mfw3SDfK8NH70pUZoffKtIKnfdpFfBQVvamxHW79EztrOpS9_MTqFEm9zLTKX7RsF_uY-f45DALt81_ptRX9zT8SVgMroPePMS5qX81QKeG2aKrWG5jcOP1HSnTvA3TMPmgKtcWFTzlfWwPYEK_So1pteCa6TfRBk0G3n2ZbrVF17c2DvGIfwxTqbxPD7CaDt4vlOf3z6kxBcfBLsqd5Vr9Ub7OpfRvTEHoREmpLe1DcT5UKtUDAzhnQJADxJfilDynx_kvE0hzw4nxyg7r-yv1HsWi4QxghEVFRAPjWCtethqPjQlHr7Sl5scFXEfJ4VRreerPzK1uyI_W1y0)

# Integration CircleCI job

CircleCI integration job is aimed to test all OpenCog related repositories
front-to-back using set of repos and branches. Thus it can be used to build
`singnet` fork or `opencog` fork or get part of repos from `singnet` and part
from user's own forks.

Job starts from building docker containers and publishing them into private
DockerHub repo. Then it uses fresh containers to build and test all components
in a way similar to `cogutil` CircleCI workflow. Green status means that one
can use provided set of branches to build and run all OpenCog tests from the
scratch.

## Restrictions

### Only single workflow instance can be running at the same time.

Because of CircleCI API restrictions workflow cannot be started via API with
parameters passed. It is workarounded by setting build properties before build
started. It may mean that one cannot run few builds in parallel with different
parameters, though I am not sure about it.

More serious restriction is using private DockerHub to keep fresh docker
images. Right now workflow uses hardcoded tags to push images. This means that
two jobs in parallel will push two images using same tag and finally will use
the same docker image.

### CircleCI job used is private CircleCI job

Before making this infrastructure publically available few things should be
addressed ([see below](#items-to-address)).

# Merging script

## Merge opencog to singnet

Script automatically merges `opencog` repos to `singnet` forks.

In empty directory execute:
```sh
python merge-opencog-to-singnet.py \
	--github-token <github-token> \
	--circleci-token <circleci-token> \
	--action merge
```

This command clones all forked `singnet` repos, creates new branches, merges
latest opencog code to them. In case of merge conflict in some repo script
stops. User should resolve conflict and make merge commit for the repo. Then
script can be started again. It continues merging from next repo. After
doing merge script pushes branches into user's github repo forks, starts CI on
the set of branches and stops.

User should check CI status manually and execute:
```sh
python merge-opencog-to-singnet.py \
	--github-token <github-token> \
	--circleci-token <circleci-token> \
	--action pr
```
This command raises PRs from merge branches to the `singnet` repos.

## Run CI

One can use `--action ci` to run Circle CI integration job. This action has two
parameters `--ci-fork` to set fork which should be used, and `--ci-branch` to
set name of the branch. For example to rerun CI after merge one can execute:

```sh
python merge-opencog-to-singnet.py \
	--github-token <github-token> \
	--circleci-token <circleci-token> \
	--action ci \
	--ci-fork singnet \
	--ci-branch master
```

## Cleanup

Following command removes all merge branches from local and remote
repositories:
```sh
python merge-opencog-to-singnet.py \
	--github-token <github-token> \
	--circleci-token <circleci-token> \
	--action clean
```

## Github API token

Github token is used to:
- read public repositories;
- create forks to keep new branches;
- push merge results;
- raise PRs.

You can create one using your Github account.
Use `Settings/Developer settings/Personal access tokens` menu.
Press `Generate New Token` button.
Set following permissions:
- `repo/public_repo`
- `admin:org/read`
Generate new token.

## CircleCI token

Is required to configure and start `CircleCI` integration build.

To generate new token:
- open CircleCI app
- open `User settings/Personal API Tokens`
- press `Generate New Token`
- enter token name
- press `Add API Token`
Copy generated token.

# Items to address

TODO:
- find a way to start integration build passing list of branches and repos
  using CircleCI API
- find a way to run several integration builds simultaneously if required
- add a check to not try raising PRs which are already raised
- how to add privileges for adding new `ref` to repo (`tag` for instance)
- remove previous merge branches
- create repository for integration CircleCI and merge script and move code
  there
- add `singularitynet` private dockerhub repos to keep intermediate dockers for
  integration build
- create dockerhub user which has permissions to write in intermediate docker
  repos
- create CircleCI user which has permissions to start builds for all `singnet`
  fork repos

