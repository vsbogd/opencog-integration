# Overview

Opencog components dependency graph:

![opencog components dependency graph](https://www.plantuml.com/plantuml/svg/XPDBJiCm48RtFeKlODWZ5fNW0EmHYqaok5Ry2FO4LKBSdQcTjkC8H3Qsltav_vyS2a6cDNYbo957_GBZ31QBDlefXIL5ZAIV7TWCGQdnYjAup5QSNpLX8JC1GK4g-ar3gUX2H6v6ZoUrj4bwIkECMNyfpOzic1QCOxBtsse6xjFwRkGC_gogGxhqDlQl_2KLufJIbLpWltURyBChvBFw5g_CQ2Nd1Gcfe1G5A8N2cg1WQyPEOh3E32wrINpWVHylfhRT4if-ni1tEmR8ipIoNLWGZv1ZrnTFX3c2DvIIv-vTq1vP93DaDx6PVSX3j2jxR6fB5ot7LVrozACndOtoKv71iv3DIW6RawAy1cyQrxKogUgDDbrs7k_ohpiv-9hxq3BloeVNxpa57Q2mHhzNxUZPrPviLkxWPbzFRnPABRffsrfPyr8TC4xya_y0)

[source code](https://www.planttext.com/?text=XPDBJiCm48RtFeKlODWZ5fNW0EmHYqaok5Ry2FO4LKBSdQcTjkC8H3Qsltav_vyS2a6cDNYbo957_GBZ31QBDlefXIL5ZAIV7TWCGQdnYjAup5QSNpLX8JC1GK4g-ar3gUX2H6v6ZoUrj4bwIkECMNyfpOzic1QCOxBtsse6xjFwRkGC_gogGxhqDlQl_2KLufJIbLpWltURyBChvBFw5g_CQ2Nd1Gcfe1G5A8N2cg1WQyPEOh3E32wrINpWVHylfhRT4if-ni1tEmR8ipIoNLWGZv1ZrnTFX3c2DvIIv-vTq1vP93DaDx6PVSX3j2jxR6fB5ot7LVrozACndOtoKv71iv3DIW6RawAy1cyQrxKogUgDDbrs7k_ohpiv-9hxq3BloeVNxpa57Q2mHhzNxUZPrPviLkxWPbzFRnPABRffsrfPyr8TC4xya_y0)

# Merging script

Script automatically merges `opencog` repos to `singnet` forks.

In empty directory execute:
```sh
python merge-opencog-to-singnet.py --github-token <github-token> \
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
