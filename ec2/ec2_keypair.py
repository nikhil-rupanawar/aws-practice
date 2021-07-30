import os
import sys
import boto3
import pathlib
import tempfile
import enum

from botocore.exceptions import ClientError
    
EC2_KEY_NAME = 'ec2-key-pair3'
EC2_KEY_DIR = pathlib.Path(pathlib.Path.home()) / '.keys'
EC2_KEY_FILE = EC2_KEY_DIR / EC2_KEY_NAME / '.pem'

ec2_provider = boto3.client('ec2')

class KeyStatus:
    OK = 'ok'
    EXIST_REMOTE_NOT_LOCAL = 'EXIST_REMOTE_NOT_LOCAL'
    DOES_NOT_EXIST = 'DOES_NOT_EXIST'
    FINGER_INCORRECT = 'FINGER_INCORRECT'


def check_key_insync(key_name):
    key_local_path = (EC2_KEY_DIR / EC2_KEY_NAME).with_suffix('.pem')
    key_verify_local_path = (EC2_KEY_DIR / EC2_KEY_NAME).with_suffix('.verify')

    key_pairs = ec2_provider.describe_key_pairs()

    target_key = [ 
        k for k in key_pairs['KeyPairs'] if k['KeyName'] == key_name
    ]
    print(target_key, "ghfhgfgh")

    target_key = target_key and target_key[0]
    if not target_key:
        return KeyStatus.DOES_NOT_EXIST
    if target_key and not key_local_path.exists():
        return KeyStatus.EXIST_REMOTE_NOT_LOCAL

    fp = None
    try:
        with open(key_verify_local_path) as handle:
            fp = handle.read()
    except IOError:
        pass
    print(f"Check? {fp} == {target_key['KeyFingerprint']}")
    if fp == target_key['KeyFingerprint']:
        print(f"Key {key_name} [OK]...")
        return KeyStatus.OK
    return KeyStatus.FINGER_INCORRECT


def recreate_key_pair(key_name):
    try:
        ec2_provider.delete_key_pair(KeyName=key_name)
    except ClientError:
        pass

    key_local_path = (EC2_KEY_DIR / EC2_KEY_NAME).with_suffix('.pem')
    key_verify_local_path = (EC2_KEY_DIR / EC2_KEY_NAME).with_suffix('.verify')

    key_pair = ec2_provider.create_key_pair(KeyName=key_name)
    print(key_pair)
    with os.fdopen(
        os.open(
            key_local_path,
            os.O_WRONLY | os.O_CREAT,
            0o400
        ),
        "w+"
    ) as handle:
        handle.write(key_pair["KeyMaterial"])
    print(f"Key {key_name} stored -> {key_local_path}")
    with os.fdopen(
        os.open(
            key_verify_local_path,
            os.O_WRONLY | os.O_CREAT,
            0o400
        ),
        "w+"
    ) as handle:
        handle.write(key_pair["KeyFingerprint"])
    print(f"Key fingerprint of {key_name} stored -> {key_verify_local_path}")


def list_instances():
    for instance in ec2_provider:
        print(instance)


if __name__ == '__main__':
    result = check_key_insync(EC2_KEY_NAME)
    print(result)
    if result != KeyStatus.OK:
        sys.exit(result)
