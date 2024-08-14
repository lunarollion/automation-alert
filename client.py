import boto3
import logging


def build_arn(account_number):
    return f"arn:aws:iam::{account_number}:role/assume_role_Training"

def aws_session(account_number=None, region="ap-southeast-3"):
    session_name = f"{account_number}_session"
    if account_number:
        role_arn = build_arn(account_number)
        client = boto3.client('sts', region_name=region)
        response = client.assume_role(RoleArn=role_arn, RoleSessionName=session_name)
        session = boto3.Session(
            aws_access_key_id=response['Credentials']['AccessKeyId'],
            aws_secret_access_key=response['Credentials']['SecretAccessKey'],
            aws_session_token=response['Credentials']['SessionToken'],
            region_name=region)
        logging.info(response)
        return session
    else:
        return boto3.Session()
