### Welcome to ItemCatalog project
This is a project made for the Udacity course.
The point of this exercise is to showcase skill in creating application with
python combined with flask, SQLalchemy. This app will have full CRUD functionality
for authenticated (via google+ account) users.

### Requirements
To fully utilize this app you will need a google+ account.

### Installation
The easyest way to get this project working is to run it in the prepared virtual
machine.
* Download [Vagrant](https://github.com/udacity/fullstack-nanodegree-vm)
* then copy this repository into the catalog folder.
* Navigate within your terminal into the folder containing "Vagrantfile"
* run the following commands:
* `vagrant up`
* `vagrant ssh`
* `cd /vagrant/catalog`
* `python application.py`

Open the browser and paste the following address: `<http://localhost:5000/>`

### JSON endpoints
JSON endpoints are provided for accessing a single category with its items
or a particular item itself.
