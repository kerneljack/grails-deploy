# grails-deploy

This is a tool to manage remote, unattended deployments of a Grails app. It uses the following tools to provide this functionality:

* Git (using tags)
* Python
* JSON
* Cron

We use 2 separate Git repositories and a **control** application written in Python to accomplish this. So altogether we have:

* Grails app repository
* Deployment control app repository
* Deployment Control Python app

### 1. Grails App Repository

The developers who work on the Grails app will check in their changes as normal into the **Grails App Repository** where all the code resides. They will use the **tags** feature of Git to tag the repository at a certain point when they are ready to do a release. For example:

`$ git tag -a 1.0`

Other developers who wish to checkout the exact same version of the app can do so using:

`$ git checkout tags/1.0`

To see the current tags on a repo, use the `--decorate` option to `git log`:

`$ git log --decorate`

The **Grails app repository** is what holds the actual application while 

### 2. Deployment Control Repository

The **Deployment control repository (DCR)** is what determines which *version* of the app gets deployed. This repository simply contains a `deploy.json` file and a deployment control app. The `deploy.json` file has the following format:

```
{ "deploy": "(YES|NO)", "version": "version number" }
```

The **Deployment control repository (DCR)** will have restricted access to a small group of people who are allowed to control the deployment process. You can use the Collaborators feature to control the list of people who can push/pull from the repo.

### 3. Deployment Control Python app

The deployment control app (`deploy.py`) reads the `deploy.json` file and checks to see if the value of the `deploy` field is **YES** (upper case only). If so, it goes ahead and deploys the **version** specified by the `version` field.

We run the python app periodically using Cron (every minute) in my case.

Using these 3 things in combination we achieve SSH-less remote deployment of our app. Note that this deployment is further restricted to authorised users only.

## How do we test it? 

I used the following **Vagrantfile** to create a simple **Ubuntu** VM to test this:

```
#!/usr/bin/env ruby
# Creates an Ubuntu 16.04 VM
#   * Run using 'vagrant up'
#   * SSH using vagrant@192.168.10.10, password 'vagrant'

Vagrant.configure("2") do |config|
  config.vm.box = "bento/ubuntu-16.04"
  config.vm.network "private_network", ip: "192.168.10.10"

    config.vm.provider "virtualbox" do |vb|
     vb.memory = "1024"
     vb.customize ["modifyvm", :id, "--cableconnected1", "on"]
    end
end
```

Once logged on to the **vagrant** account using `vagrant ssh`, I installed OpenJDK and Tomcat 8:

`$ sudo apt-get install openjdk-8-jdk tomcat8`

I created 2 separate directories: one for the app repository itself, and another for the Deployment control repository. I named these directories **dev** and **dcr** respectively.

I checked out a version of the app into the `dev` repo and then I modified the following file slightly to make it more obvious which version we were looking at in the browser:

`grails-petclinic-master/grails-app/views/clinic/index.gsp`

I inserted the following text into the file:

`    <h2><g:message code="Welcome to version 1.0"/></h2>`

I then committed this change to the repository, and tagged it using a `1.0` version number. Remember that you need to push the tags separately in git:

```
$ git tag -a 1.0
$ git commit index.gsp
$ git push
$ git push --tags
```

Now we have a version 1.0 of our app in the repo. I proceeded to change the `index.gsp` file again, and tagged it with `2.0` this time for `Welcome to version 2.0`.

I then proceeded to checkout the Deployment Control app into the `dcr` directory. I modified the `deploy.json` as follows:

```
{"version": "1.0", "deploy": "YES"}
```

I ran the `deploy.py` manually at first to make sure that it would work. The python app copies the `war` file into the Tomcat `webapps/` directory, making it available at `http://<VM IP>/petclinic`. 

The index page displayed showed the correct version of my app (in this case it was upgraded to Version 2.0). Once I confirmed this was working, I proceeded to install a cronjob which ran every minute as follows:

`*  *  *  *  *  cd ~/dcr/grails-deploy && ./deploy.py >> deploy.log 2>&1`

I could see in the `deploy.log` file that things were working as expected:

```
Previous HEAD position was e763555... version 2.0
HEAD is now at 08fa9a8... committing version 1.0
[master d138476] "disabling deploys"
 1 file changed, 1 insertion(+), 1 deletion(-)
To git@github.com:kerneljack/grails-deploy.git
   45485a2..d138476  master -> master
creating lock file
Deploy: YES
Version: 1.0
```

The `deploy.json` file is modified as soon as the deploy is done so that it doesn’t keep trying to deploy it continuously. It’s also pushed back into the repository so that anyone using the repository will have to do a `pull`. This lets them know that the deploy was completed as well. I also use a `lockfile` to make sure that multiple instances of the deployment python script don’t try to run at the same time.


