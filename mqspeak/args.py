import argparse

def create_parser():
    parser = argparse.ArgumentParser(epilog='epilog',
                                        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-c', '--config',
                        help='path to configuration file',
                        default="/etc/mqttbridge.conf")
    return parser

def parse_args():
    parser = create_parser()
    return parser.parse_args()
