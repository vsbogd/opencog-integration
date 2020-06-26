import os
import unittest

from calculate_versions import *

class CalculateVersionsTest(unittest.TestCase):

    def setUp(self):
        for prefix in ['docker', 'ocpkg'] + list(opencog_dependencies.keys()):
            project = prefix
            if prefix == 'docker':
                project = 'opencog-docker'
            os.environ[get_env_prefix(prefix) + '_REPO'] = (
                    'https://github.com/singnet/' + project + '.git')
            os.environ[get_env_prefix(prefix) + '_BRANCH'] = 'master'

    def test_get_head_commit_id(self):
        os.environ['OPENCOG_REPO']='https://github.com/singnet/opencog.git'
        os.environ['OPENCOG_BRANCH']='release-20200616'

        actual = get_head_commit_id('opencog')

        self.assertEqual(actual,
                '0ccff9dec5a614fcea04ca82f4d475a437564a61')

    def test_get_version(self):
        Versions(opencog_dependencies).get_version('opencog')

if __name__ == '__main__':
    unittest.main()
