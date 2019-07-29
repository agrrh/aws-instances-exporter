import boto3
import logging
import os
import time

from prometheus_client import start_http_server, Gauge

# TODO use Vault
from credentials import CREDENTIALS

# Parameters init

# TODO use Vault
profiles_list = boto3.Session().available_profiles

# List of regions to process
regions_list = os.environ.get('AWS_INSTANCES_REGIONS', 'us-east-1,eu-central-1').split(',')

# Period between refreshing data from AWS, in seconds
PERIOD = int(os.environ.get('AWS_INSTANCES_PERIOD', 15 * 60))

# Define metrics

ec2_instances_metric = Gauge(
    'ec2_instances',
    'Number of existing instances',
    [
        'profile',
        'region',
        'availability_zone',
        'type',
        'state'
    ]
)

ec2_reserved_metric = Gauge(
    'ec2_reserved',
    'Number of reserved instances',
    [
        'profile',
        'region',
        'availability_zone',
        'type',
        'state'
    ]
)


# Helper methods

def describe_instances(aws_client):
    try:
        for reservation in aws_client.describe_instances().get('Reservations', []):
            for instance in reservation.get('Instances', []):
                yield instance
    except Exception as e:
        logging.error(e)


def describe_reserved_instances(aws_client):
    try:
        for reserved in aws_client.describe_reserved_instances().get('ReservedInstances', []):
            yield reserved
    except Exception as e:
        logging.error(e)


# Main business logic

def main(credentials):
    """Main business method, gather data and set metrics accordingly.
    """
    ec2_instances = {}
    ec2_reserved = {}

    for profile in profiles_list:
        aws_session = boto3.Session(profile_name=profile)

        for region in regions_list:
            aws_client = aws_session.client('ec2', region_name=region)

            # Instances
            for instance in describe_instances(aws_client):
                availability_zone = instance.get('Placement', {}).get('AvailabilityZone', 'undefined')
                type = instance.get('InstanceType')
                state = instance.get('State', {}).get('Name', 'undefined')

                labels = ','.join((profile, region, availability_zone, type, state))

                ec2_instances[labels] = ec2_instances.get(labels, 0) + 1
                ec2_instances_metric.labels(profile, region, availability_zone, type, state).set(ec2_instances[labels])

            # Reserved
            for reserved in describe_reserved_instances(aws_client):
                availability_zone = reserved.get('AvailabilityZone', 'undefined')
                type = reserved.get('InstanceType')
                state = reserved.get('State')

                labels = ','.join((profile, region, availability_zone, type, state))

                ec2_reserved[labels] = ec2_reserved.get(labels, 0) + 1
                ec2_reserved_metric.labels(profile, region, availability_zone, type, state).set(ec2_reserved[labels])


if __name__ == '__main__':
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    for module_name in ('urllib3', 'botocore'):
        logging_ = logging.getLogger(module_name)
        logging_.setLevel(logging.ERROR)

    logging.critical('Starting AWS reservist exporter ...')
    logging.critical('Refresh period is {} sec'.format(PERIOD))
    logging.critical('Regions: {}'.format(','.join(regions_list)))
    logging.critical('Profiles: {}'.format(','.join(profiles_list)))

    start_http_server(8000)

    # Business logic
    iter = 0
    while True:
        t_start = time.time()
        main(CREDENTIALS)
        logging.debug('iter {} done, took {} sec'.format(iter, int(time.time() - t_start)))
        time.sleep(PERIOD)
        iter += 1
