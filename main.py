import argparse
import boto3
import logging
import os
import time

from prometheus_client import start_http_server, Gauge

# Parameters init

profiles_list = boto3.Session().available_profiles

# Period between refreshing data from AWS, in seconds
PERIOD = int(os.environ.get('AWS_QUERY_PERIOD', 15 * 60))

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

def args_parse():
    parser = argparse.ArgumentParser(description='AWS instances exporter')
    parser.add_argument('-d', '--debug', action='store_true', help='Enable debug output')
    return parser.parse_args()


def describe_instances(aws_client, profile):
    logging.debug('Describe instances for {}'.format(profile))
    try:
        for reservation in aws_client.describe_instances().get('Reservations', []):
            for instance in reservation.get('Instances', []):
                yield instance
    except Exception as e:
        logging.error('Profile "{}" exception: "{}"'.format(profile, e))


def describe_reserved_instances(aws_client, profile):
    logging.debug('Describe reserved instances for {}'.format(profile))
    try:
        for reserved in aws_client.describe_reserved_instances().get('ReservedInstances', []):
            yield reserved
    except Exception as e:
        logging.error('Profile "{}" exception: "{}"'.format(profile, e))


# Main business logic

def main():
    """Main business method, gather data and set metrics accordingly.
    """
    ec2_instances = {}
    ec2_reserved = {}

    for profile in profiles_list:
        aws_session = boto3.Session(profile_name=profile)
        aws_client = aws_session.client('ec2')

        # Instances
        for instance in describe_instances(aws_client, profile):
            availability_zone = instance.get('Placement', {}).get('AvailabilityZone', 'undefined')
            type = instance.get('InstanceType')
            state = instance.get('State', {}).get('Name', 'undefined')

            labels = ','.join((profile, aws_session.region_name, availability_zone, type, state))

            ec2_instances[labels] = ec2_instances.get(labels, 0) + 1
            ec2_instances_metric.labels(profile, aws_session.region_name, availability_zone, type, state).set(ec2_instances[labels])

        # Reserved
        for reserved in describe_reserved_instances(aws_client, profile):
            availability_zone = reserved.get('AvailabilityZone', 'undefined')
            type = reserved.get('InstanceType')
            state = reserved.get('State')

            labels = ','.join((profile, aws_session.region_name, availability_zone, type, state))

            ec2_reserved[labels] = ec2_reserved.get(labels, 0) + 1
            ec2_reserved_metric.labels(profile, aws_session.region_name, availability_zone, type, state).set(ec2_reserved[labels])


if __name__ == '__main__':
    args = args_parse()

    # Configure logging
    logging.basicConfig(
        format='%(asctime)s %(name)s %(levelname)s %(message)s',
        level=logging.DEBUG if args.debug else logging.INFO
    )
    for module_name in ('urllib3', 'botocore'):
        logging_ = logging.getLogger(module_name)
        logging_.setLevel(logging.ERROR)

    logging.critical('Starting AWS reservist exporter ...')
    logging.critical('Refresh period is {} sec'.format(PERIOD))
    logging.critical('Profiles: {}'.format(','.join(profiles_list)))

    start_http_server(8000)

    # Business logic
    iter = 0
    # FIXME catch SIGINT and others to evade ugly exit messages
    while True:
        t_start = time.time()
        main()
        logging.debug('iter {} done, took {} sec'.format(iter, int(time.time() - t_start)))
        time.sleep(PERIOD)
        iter += 1
