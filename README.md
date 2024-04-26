# COMP0239 Coursework: Data Analysis Pipeline

This README provides a detailed guide to setting up and running the necessary infrastructure for the COMP0239-CW project, which involves configuring and deploying services across multiple nodes using Ansible and other tools.

## Prerequisites

* Python installed on the host machine.
* You have the initial COMP0239 Lecture Key

## Run Ansible Playbook
The ansible-playbook commands shown on below are all running  on the playbooks directory. If you running outside the playbooks directory, you need to speficy the absolute path.

## SetUp Instructions 

Unless Specified, all commands below should run on the host node.

1. **Clone Github Repository:**
    - First clone this repository on the host node, which contains the playbooks and codes. The git should be installed in default, if not, run `sudo dnf install git-all` to install it.
    - `git clone https://github.com/RuiboZhang1/COMP0239-CW.git`

2. **Setup Inventory File:**
    - The `COMP0239-CW/playbooks` folder contains the inventory file which defines the host and clusters group.
    - Replace the contents with public ip address of your host and cluster machines.

3. **Edit The Pipeline Code (On pipeline Directory)**
    - We need to **replace the original ip address with your own client ip address** in some files to use the Redis.
    - In pipelines/app.py, 

            celery = Celery(app.name, broker='redis://10.0.6.168/0', backend='redis://10.0.6.168/1')

            r = redis.Redis(host='10.0.6.168', port=6379, db=0)

    - In pipelines/celery_task_app/tasks.py,

            r = redis.Redis(host='10.0.6.168', port=6379, db=0)

    - In pipelines/celery_task_app/worker.py,

            celery = Celery('celery_app',
                broker='redis://10.0.6.168/0',
                backend='redis://10.0.6.168/1',
                include=['celery_task_app.tasks']
                )
                
3. **Copy Lecture To Host (Run On Local Machine)** 
    - `scp -i ~/.ssh/comp0239_key ~/.ssh/comp0239_key ec2-user@ec2-18-133-220-62.eu-west-2.compute.amazonaws.com:~/.ssh/comp0239_key`
    - Replace the key name with your own defined name, and replace the address of your machine.

4. **Install Pip and Ansible**
    - Pip and Ansible are not installed in default. Run the commands to install them.
    - `python -m ensurepip --upgrade`
    - `pip3 install ansible`

5. **Generate and Distribute public key**
    - For security, we suggest to run the following command to generate a new ssh key for this coursework, it will directly add the new generated key to authorized key in all machines. Using `ANSIBLE_HOST_KEY_CHECKING=False` could avoid checking the fingerprint for the first time connection. The generated key called ansible_key, we will use it to run ansible playbooks later.
    - `ANSIBLE_HOST_KEY_CHECKING=False ansible-playbook --private-key=~/.ssh/comp0239_key -i inventory.ini distribute_public_key.yaml`

6. **Mount AWS EBS to clusters**
    - The default storage for each machine is 10 GB, which is insufficient if we need to install more packages and download files. We can mount the AWS EBS to the clusters using this playbooks.
    - `ansible-playbook --private-key=~/.ssh/ansible_key -i inventory.ini mount_file_system.yaml`
    - It is not common but might encounter error when running this playbook. The target file name is nvme1n1, but some machines may have the name nvme0n1. Double check by running `lsblk` on the machine, you will see there is a large disk not mounted, replace the name in the playbook.

7. **Command all cluster to git clone the repository**
    - Clone the Github Repository to all cluster machines.
    - `ansible-playbook --private-key=~/.ssh/ansible_key -i inventory.ini clone_repository.yaml`

8. **Set up new python virtual environment**
    - create a new virtual environment on all machines. There are some differences on the installation since host node doesn't run the model.
    - `ansible-playbook --private-key=~/.ssh/ansible_key -i inventory.ini new_venv_host.yaml`
    - `ansible-playbook --private-key=~/.ssh/ansible_key -i inventory.ini new_venv_clusters.yaml`

9. **Install Required Software (Redis, Firewalld, Node Exporter)**
    - There are some key softwares need to be installed for running the pipeline
    - `ansible-playbook --private-key=~/.ssh/ansible_key -i inventory.ini install_required_software.yaml`

10. **Open Firewall Port**
    - Some ports must be opened for us to access from local machine.
    - `ansible-playbook --private-key=~/.ssh/ansible_key -i inventory.ini firewalld_open_port.yaml`

11. **Run Prometheus**
    
    - Install Prometheus
        
            sudo dnf golang
            sudo dnf install https://dl.fedoraproject.org/pub/epel/epel-release-latest-9.noarch.rpm
            sudo rpm --import /etc/pki/rpm-gpg/RPM-GPG-KEY-EPEL-9
            sudo dnf --nogpgcheck install golang-github-prometheus golang-github-prometheus-node-exporter
    - Config Prometheus
        
        - On bash run `sudo vi /etc/prometheus/prometheus.yml`
        - ![Prometheus Config](https://github.com/RuiboZhang1/COMP0239-CW/blob/main/images/Prometheus_config.png?raw=true)
        - On `job_name: node`, keep the localhost, replace other targets with your clusters inner ip address.


    - Run Prometheus as service
        - On bash run `sudo nano /etc/systemd/system/prometheus.service`, add the following:
  
                [Unit]
                Description=Prometheus Server
                Documentation=https://prometheus.io/docs/introduction/overview/
                After=network-online.target

                [Service]
                User=prometheus
                Group=prometheus
                Type=simple
                ExecStart=/usr/bin/prometheus \
                  --config.file=/etc/prometheus/prometheus.yml \
                  --storage.tsdb.path=/var/lib/prometheus/ \
                  --web.console.templates=/etc/prometheus/consoles \
                  --web.console.libraries=/etc/prometheus/console_libraries
                Restart=on-failure

                [Install]
                WantedBy=multi-user.target

        - Then run on bash

                sudo systemctl daemon-reload
                sudo systemctl enable prometheus
                sudo systemctl start prometheus

12. **Run Grafana**

    - Install Grafana

            sudo dnf install grafana
            sudo systemctl daemon-reload
            sudo systemctl start grafana-server
            sudo systemctl status grafana-server
            sudo systemctl enable grafana-server.service
    
    - Access Grafana
        - access through local machine `public_ip_of_host:3000/login`. 
        - Default user and password is admin/admin, then set a new password if need

    - Add Prometheus as Data Source in Grafana:
        - On left menu, Configuration -> Data Sources -> Add data source -> Prometheus. 
        - Set URL to `http://localhost:9090` and add a timeout value. 
        - Save it and should show data source is working if prometheus is running.

    - Add Dashboard
        - Celery provides a template for monitoring, can download from: https://github.com/mher/flower/blob/master/examples/celery-monitoring-grafana-dashboard.json
        - On the left menu Dashboard -> Import -> Upload JSON file, choose the template. Then in the dashboards, you now can see a dashboard called celery monitoring.
        - On the top right, can add more panels:

                - CPU usage: `100 - (avg by (instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)`
                - RAM usage: `(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100`
                - Load Average - 1 min: `node_load1`
                - Load Average - 5 mins: `node_load5`
                - Network throughput - receive - 15 mins: `rate(node_network_receive_bytes_total[15m])`
                - Network throughput - transmit - 15 mins: `rate(node_network_transmit_bytes_total[15m])`
                - Default Disk Usage: `100 - (node_filesystem_avail_bytes{device="/dev/nvme0n1p4"} / node_filesystem_size_bytes{device="/dev/nvme0n1p4"} * 100)`
                - Total tasks ran by workers: `flower_events_total{type=~"task-failed|task-succeeded", task="celery_task_app.tasks.fetch_and_process_image"}`
        - Then Run queries. Apply -> Save Dashboard


13. **Run Redis (on Client Node)**
    - On Bash run: `sudo vi /etc/redis/redis.conf`
    - Find `bind 127.0.0.1` on the config file,  replace the bracket with inner ip of client node `bind 127.0.0.1 []`. E.g. `bind 127.0.0.1 10.0.6.168`
    - Then On Bash run: `sudo systemctl start redis.service`
    - `sudo systemctl status redis.service` to check if it is open

14. **Run Celery Flower (On pipelines Directory)**
    - Flower provide an interface to monitor the Celery workers and export some metrics to Prometheus.
    - Run `nohup celery -A app.celery flower --port=4505 &> celery_flower_log.txt 2>&1 &`, this comment allows the flower run on background and will not be killed after log out the remote server. The log will be written into celery_flower_log.txt file.
    - On local machine, access to the Flower interface: `public_ip_of_host:4505`

15. **Initialize Celery Workers (On playbooks Directory)**
    - Command all cluster nodes to join as Celery workers.
    - Run on Bash:`ansible-playbook --private-key=~/.ssh/ansible_key -i inventory.ini initialize_celery_workers.yaml`.
    - Check the Flower interface, now you show see five machines are Online. ![Flower Interface](https://github.com/RuiboZhang1/COMP0239-CW/blob/main/images/flower_interface.png?raw=true)
    
1.  **Run Flask Server (On pipelines Directory)**
    - Run on Bash:`nohup python app.py > flask_log.txt 2>&1 &`
    - This will run the Flask Server on background, you can access to the Front-end and upload your own image to generate the caption from local machine: `public_ip_of_host:4506`.

2.  **Run Test Pipeline (On pipelines Directory)**
    - Run on Bash:`nohup python test_pipeline.py > test_pipeline_log.txt 2>&1 &`
    - This file will run on background, read the coco_image_urls.txt file, which contains more than 150k image urls. It will continuously send the url to the Flask server and let the pipeline to generate the caption.


## Completion
Congratulations! The analysis pipeline using distributed clusters is now complete. You can monitor the process through Grafana and Flower.



