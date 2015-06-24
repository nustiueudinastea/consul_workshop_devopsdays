
from consul import Check, Consul
import logging
import argparse
import time
import sys

NAME = 'ClusterManager'

sh = logging.StreamHandler(sys.stdout)
logger = logging.getLogger(NAME)
logger.addHandler(sh)
logger.setLevel(logging.INFO)

class ClusterManager:
    def __init__(self, id, ttl):
        self.name = NAME
        self.id = self.name + str(id)
        self.ttl = ttl
        self.client = Consul(host='172.17.42.1')

    def register(self):
        logger.info('Registering service {} with id {}'.format(self.name, self.id))
        self.client.agent.service.register(name=self.name, service_id=self.id, check=Check.ttl('10s'))

    def deregister(self):
        logger.info('Deregistering service {}'.format(self.id))
        self.client.agent.service.deregister(service_id=self.id)

    def pass_check(self):
        check_id = 'service:' + self.id
        logger.info('Starting service check loop for {}'.format(check_id))
        while True:
            try:
                logger.debug('Updating service check ttl for {}'.format(check_id))
                self.client.agent.check.ttl_pass(check_id=check_id)
                time.sleep(8)
            except KeyboardInterrupt:
                self.deregister()
                sys.exit()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Starts {} service'.format(NAME))
    parser.add_argument('--id', help='Service ID', type=int, required=True)
    args = parser.parse_args()
    cm = ClusterManager(args.id, 10)
    cm.register()
    cm.pass_check()
