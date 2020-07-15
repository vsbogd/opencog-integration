node {

    ocpkg_code = code().repo(params.OCPKG_REPO).branch(params.OCPKG_BRANCH)
    atomspace_code = code().repo(params.ATOMSPACE_REPO).branch(params.ATOMSPACE_BRANCH)
    
    opencog_deps = docker().job("opencog_deps").repo(params.DOCKER_REPO).branch(params.DOCKER_BRANCH)
        .requires(ocpkg_code)
    postgres = docker().job("postgres").repo(params.DOCKER_REPO).branch(params.DOCKER_BRANCH)
        .requires(atomspace_code)
    
    cogutil = deb().job("cogutil").repo(params.COGUTIL_REPO).branch(params.COGUTIL_BRANCH)
        .requires(opencog_deps)
    atomspace = deb().job("atomspace").repo(params.ATOMSPACE_REPO).branch(params.ATOMSPACE_BRANCH)
        .requires(opencog_deps, postgres, cogutil)
    cogserver = deb().job("cogserver").repo(params.COGSERVER_REPO).branch(params.COGSERVER_BRANCH)
        .requires(opencog_deps, cogutil, atomspace)
    attention = deb().job("attention").repo(params.ATTENTION_REPO).branch(params.ATTENTION_BRANCH)
        .requires(opencog_deps, cogutil, atomspace, cogserver)
    ure = deb().job("ure").repo(params.URE_REPO).branch(params.URE_BRANCH)
        .requires(opencog_deps, cogutil, atomspace)
    pln = deb().job("pln").repo(params.PLN_REPO).branch(params.PLN_BRANCH)
        .requires(opencog_deps, cogutil, atomspace, ure)
    opencog = deb().job("opencog").repo(params.OPENCOG_REPO).branch(params.OPENCOG_BRANCH)
        .requires(opencog_deps, cogutil, atomspace, cogserver, attention, ure, pln)
    
   def mvnHome
   stage('Preparation') { // for display purposes
      // Get some code from a GitHub repository
      git 'https://github.com/jglick/simple-maven-project-with-tests.git'
      // Get the Maven tool.
      // ** NOTE: This 'M3' Maven tool must be configured
      // **       in the global configuration.           
      mvnHome = tool 'M3'
   }
   stage('Build') {
      // Run the maven build
      withEnv(["MVN_HOME=$mvnHome"]) {
         if (isUnix()) {
            sh '"$MVN_HOME/bin/mvn" -Dmaven.test.failure.ignore clean package'
         } else {
            bat(/"%MVN_HOME%\bin\mvn" -Dmaven.test.failure.ignore clean package/)
         }
      }
   }
   stage('Results') {
      junit '**/target/surefire-reports/TEST-*.xml'
      archiveArtifacts 'target/*.jar'
   }
}
