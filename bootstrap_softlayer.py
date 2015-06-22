__author__ = 'al3x'

import logging
import sys
import time
import pprint
import socket
import SoftLayer
from ansible import inventory, runner, constants, playbook, callbacks, utils

logging.basicConfig(stream=sys.stdout, level=logging.INFO)

SL_USERNAME = ''
SL_API_KEY = ''
USER = ''
DATACENTER = 'ams01'
SSH_KEY = ''
hosts = ['host1', 'host2', 'host3']

class PrettyLog():
    def __init__(self, obj):
        self.obj = obj
    def __repr__(self):
        return pprint.pformat(self.obj)


client = SoftLayer.create_client_from_env(username=SL_USERNAME, api_key=SL_API_KEY)
vs = SoftLayer.VSManager(client)
km = SoftLayer.SshKeyManager(client)

def add_key(sshkey, user):
    logging.info('Adding sshkey for user {}'.format(user))
    try:
        key = km.add_key(key=sshkey, label=user)
        logging.info(key)
        return key
    except SoftLayer.SoftLayerAPIError as e:
        logging.warning(e)
        keys = km.list_keys(label=user)
        if len(keys) > 0:
            return keys[0]
    return None

def create_instances(hosts, user, key):
    logging.info('Creating instances')
    logging.info(key)
    for host in hosts:
        instance_name = '{}-{}'.format(user, host)
        logging.info('Creating instance {}'.format(instance_name))
        vs.create_instance(
            hostname=instance_name,
            domain='workshop.giurgiu.io',
            cpus=1,
            memory=1024,
            hourly=True,
            os_code='UBUNTU_LATEST',
            local_disk=False,
            datacenter='ams01',
            ssh_keys=[key['id']])

def delete_instances(instances):
    logging.info('Deleting instances')
    for instance in instances:
        logging.info('Deleting instance with id {} and hostname {}'.format(instance['id'], instance['hostname']))
        vs.cancel_instance(instance['id'])

def get_instances(user):
    logging.info('Retrieving instances for {}'.format(user))
    return vs.list_instances(hostname='{}-*'.format(user))

def wait_for_instances(instances):
    all_running = False
    while not all_running:
        logging.info('Waiting for instances to be running')
        status = {}
        for inst in instances:
            id = inst['id']
            instance = vs.get_instance(id)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            ip = instance.get('primaryIpAddress', None)
            if ip:
                result = sock.connect_ex((instance['primaryIpAddress'], 22))
                status[id] = True if result == 0 else False
            else:
                status[id] = False
        all_running = all(status.values())
        time.sleep(10)

def provision_machines(instances, extra_vars={}):
    vs_ips = [instance['primaryIpAddress'] for instance in instances]
    ansible_inventory = inventory.Inventory(vs_ips)
    constants.HOST_KEY_CHECKING = False
    stats = callbacks.AggregateStats()
    playbook_cb = callbacks.PlaybookCallbacks(verbose=utils.VERBOSITY)
    runner_cb = callbacks.PlaybookRunnerCallbacks(stats, verbose=utils.VERBOSITY)
    ansible_playbook = playbook.PlayBook(
        playbook='ansible-provision/consul_workshop.yml',
        stats=stats, callbacks=playbook_cb, runner_callbacks=runner_cb,
        remote_user='root', forks=3,
        inventory=ansible_inventory, extra_vars=extra_vars)
    logging.info(PrettyLog(ansible_playbook.run()))

def join_consul_cluster(instances):
    logging.info(instances)
    vs_ips = [instance['primaryIpAddress'] for instance in instances]
    ansible_inventory = inventory.Inventory(vs_ips)
    constants.HOST_KEY_CHECKING = False
    ansible_runner = runner.Runner(
        remote_user='root', pattern='*', forks=3,
        inventory=ansible_inventory,
        module_name='command', module_args='/opt/consul/bin/consul join -rpc-addr=172.17.42.1:8400 {}'.format(vs_ips[0])
    )
    logging.info(PrettyLog(ansible_runner.run()))

key = add_key(SSH_KEY, USER)
# create_instances(hosts, USER, key)
# while len(get_instances(USER)) != len(hosts):
#    logging.info('Waiting for instances to be provisioned')
#    time.sleep(10)

instances = get_instances(USER)

logging.info(PrettyLog(instances))
# wait_for_instances(instances)
# instances = get_instances(USER)
# provision_machines(instances[:1], extra_vars={'consul_bootstrap': True})
#provision_machines(instances[1:])
#join_consul_cluster(instances)

delete_instances(instances)