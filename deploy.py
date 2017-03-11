#!/usr/bin/python

import json
import os
import subprocess
import traceback

def doDeploy():
    # check for lock file
    # if it does not exist, create it and do the rest
    lockFile = 'deploy_lockfile'
    if os.path.exists(lockFile) == False:
        try:
            cwd = os.getcwd()
            print ('creating lock file')
            with open (lockFile, 'w') as f:
                f.close()

            # do a git pull to get latest version of deploy.json
            subprocess.call(["git", "pull"])

            # get values of deploy and version
            with open("deploy.json") as deployFile:
                data = json.load(deployFile)
            deployFile.close()
        
            deploy = data['deploy']
            version = data['version']
            print('Deploy: ' + deploy)
            print('Version: ' + version)

            devPath = '/home/vagrant/dev/grails-petclinic-master'
            if deploy == 'YES':
                # cd to dev directory, pull correct version from repo
                os.chdir(devPath)
                subprocess.call(['git', 'checkout', 'tags/' + version])
                subprocess.call(['sh', './grailsw', 'war'])
                subprocess.call(['sudo', 'rm', '-rf', '/var/lib/tomcat8/webapps/petclinic*'])
                subprocess.call(['sudo', 'cp', devPath + '/target/petclinic-' + version + '.war', '/var/lib/tomcat8/webapps/petclinic.war'])
                subprocess.call(['sudo', 'systemctl', 'restart', 'tomcat8'])

            os.chdir(cwd)

            # disable deployments so we don't keep re-deploying endlessly! 
            data['deploy'] = 'NO'
            with open("deploy.json", "w") as outfile:
                json.dump(data, outfile)
            outfile.close()

            os.remove(lockFile)
        except: 
            os.chdir(cwd)
            os.remove(lockFile)
            raise

def main():
    doDeploy()

if __name__ == "__main__":
    try:
        main()
    except:
        traceback.print_exc()

