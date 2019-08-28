# Overview

Opencog components dependency graph:

![opencog components dependency graph](https://www.plantuml.com/plantuml/svg/XLJBJiGm3BpdA_83WJlYi19y07V4mMrDDceU9N7HIeX_nvjqTvqAH2-9nsCxcObwA0IPrk2L8aSUzGkCCrWiskYd59OKCP9-Tc0p1AN6AvJ6PROYVjM4XSm410Mfw3SDfK8NH70pUZoffKtIKnfdpFfBQVvamxHW79EztrOpS9_MTqFEm9zLTKX7RsF_uY-f45DALt81_ptRX9zT8SVgMroPePMS5qX81QKeG2aKrWG5jcOP1HSnTvA3TMPmgKtcWFTzlfWwPYEK_So1pteCa6TfRBk0G3n2ZbrVF17c2DvGIfwxTqbxPD7CaDt4vlOf3z6kxBcfBLsqd5Vr9Ub7OpfRvTEHoREmpLe1DcT5UKtUDAzhnQJADxJfilDynx_kvE0hzw4nxyg7r-yv1HsWi4QxghEVFRAPjWCtethqPjQlHr7Sl5scFXEfJ4VRreerPzK1uyI_W1y0)

[source code](https://www.planttext.com/?text=XLJBJiGm3BpdA_83WJlYi19y07V4mMrDDceU9N7HIeX_nvjqTvqAH2-9nsCxcObwA0IPrk2L8aSUzGkCCrWiskYd59OKCP9-Tc0p1AN6AvJ6PROYVjM4XSm410Mfw3SDfK8NH70pUZoffKtIKnfdpFfBQVvamxHW79EztrOpS9_MTqFEm9zLTKX7RsF_uY-f45DALt81_ptRX9zT8SVgMroPePMS5qX81QKeG2aKrWG5jcOP1HSnTvA3TMPmgKtcWFTzlfWwPYEK_So1pteCa6TfRBk0G3n2ZbrVF17c2DvGIfwxTqbxPD7CaDt4vlOf3z6kxBcfBLsqd5Vr9Ub7OpfRvTEHoREmpLe1DcT5UKtUDAzhnQJADxJfilDynx_kvE0hzw4nxyg7r-yv1HsWi4QxghEVFRAPjWCtethqPjQlHr7Sl5scFXEfJ4VRreerPzK1uyI_W1y0)

# Merging script

Script automatically merges `opencog` repos to `singnet` forks.

In empty directory execute:
```sh
python merge-opencog-to-singnet.py \
	--github-token <github-token> \
	--circleci-token <circleci-token>
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

TODO
