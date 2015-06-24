#!/usr/bin/env python2.7

from consul import Check, Consul
import logging
import argparse
import time
import sys

NAME = 'ClusterManager'
STATUS_PASSING = 'passing'

sh = logging.StreamHandler(sys.stdout)
logger = logging.getLogger(NAME)
logger.addHandler(sh)
logger.setLevel(logging.INFO)

class ClusterManager:
    def __init__(self, id, ttl, election=False):
        self.name = NAME
        self.id = self.name + str(id)
        self.ttl = ttl
        self.check_id = 'service:' + self.id
        self.master = None
        self.election = election
        self.client = Consul(host='172.17.42.1')

    def register(self):
        logger.info('Registering service {} with id {}'.format(self.name, self.id))
        self.client.agent.service.register(name=self.name, service_id=self.id, check=Check.ttl('10s'))
        self.client.agent.check.ttl_pass(check_id=self.check_id)
        self.session = self.client.session.create(behavior='delete', checks=[self.check_id])

    def deregister(self):
        logger.info('Deregistering service {}'.format(self.id))
        self.client.agent.service.deregister(service_id=self.id)
        logger.info('Destroying session {}'.format(self.session))
        self.client.session.destroy(self.session)

    def set_mode(self):

        logger.info('Trying to become master')
        if self.client.kv.put('master', str(self.id), acquire=self.session):
            self.master = None
            logger.info('Became master')
        else:
            key = self.client.kv.get('master')
            if key[1]:
                self.master = key[1]['Value']
                logger.info('Became secondary, master is {}'.format(self.master))
            else:
                logger.warning('Could not acquire master lock and no master available')

    def check_master(self):
        sub_services = self.client.health.service(self.name)[1]
        sub_service = next((item for item in sub_services if item['Service']['ID'] == self.master), None)
        if sub_service:
            service_check = next((item for item in sub_service['Checks'] if item['CheckID'] == 'service:{}'.format(self.master)), None)
            if service_check and service_check.get('Status', '') == STATUS_PASSING:
                logger.info('Master {} is alive'.format(self.master))
                return
        self.set_mode()

    def pass_check(self):
        logger.info('Starting service check loop for {}'.format(self.check_id))
        while True:
            try:
                logger.debug('Updating service check ttl for {}'.format(self.check_id))
                self.client.agent.check.ttl_pass(check_id=self.check_id)
                if self.election:
                    if self.master:
                        self.check_master()
                time.sleep(5)
            except KeyboardInterrupt:
                self.deregister()
                sys.exit()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Starts {} service'.format(NAME))
    parser.add_argument('--id', help='Service ID', type=int, required=True)
    parser.add_argument('--election', help='Option to enable leader elect', default=False, type=bool)
    args = parser.parse_args()
    cm = ClusterManager(args.id, 10, election=args.election)
    cm.register()
    if args.election:
        cm.set_mode()
    cm.pass_check()
