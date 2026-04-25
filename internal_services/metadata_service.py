"""
Cloud Metadata Service — SSRF Target (port 1337)
Simulates AWS EC2 Instance Metadata Service (IMDSv1).
"""
from flask import Flask, jsonify, Response

app = Flask(__name__)

METADATA = {
    'ami-id': 'ami-0abcdef1234567890',
    'ami-launch-index': '0',
    'ami-manifest-path': '(unknown)',
    'hostname': 'ip-172-31-42-8.ec2.internal',
    'instance-id': 'i-0a1b2c3d4e5f67890',
    'instance-type': 't3.medium',
    'local-hostname': 'ip-172-31-42-8.ec2.internal',
    'local-ipv4': '172.31.42.8',
    'public-hostname': 'ec2-54-123-45-67.compute-1.amazonaws.com',
    'public-ipv4': '54.123.45.67',
    'security-groups': 'pawshaven-prod-sg',
    'mac': '02:ef:2a:b1:c0:99',
    'placement/availability-zone': 'us-east-1d',
    'placement/region': 'us-east-1',
    'tags/instance/Environment': 'Production',
    'tags/instance/Project': 'PawsHaven',
    'events/maintenance/history': '[]'
}

IAM_ROLE = 'PawsHaven-Prod-EC2-Role'

IAM_CREDENTIALS = {
    'Code': 'Success',
    'LastUpdated': '2024-04-14T08:30:00Z',
    'Type': 'AWS-HMAC',
    'AccessKeyId': 'ASIAZ3EXAMPLE7PAWSKEY',
    'SecretAccessKey': 'wJalrXUtnFEMI/PawsH4v3n/bPxRfiCYSECRETKEY',
    'Token': 'IQoJb3JpZ2luX2VjEPawsHavenTokenExampleLongStringHere...',
    'Expiration': '2024-04-14T14:30:00Z'
}

@app.route('/')
def root():
    return Response('latest\n', mimetype='text/plain')

@app.route('/latest')
def latest():
    return Response('meta-data\nuser-data\n', mimetype='text/plain')

@app.route('/latest/meta-data/')
@app.route('/latest/meta-data')
def metadata_root():
    entries = list(METADATA.keys()) + ['iam/']
    return Response('\n'.join(entries) + '\n', mimetype='text/plain')

@app.route('/latest/meta-data/<key>')
def metadata_entry(key):
    if key in METADATA:
        return Response(METADATA[key] + '\n', mimetype='text/plain')
    return Response('Not Found\n', mimetype='text/plain', status=404)

@app.route('/latest/meta-data/iam/')
@app.route('/latest/meta-data/iam')
def iam_root():
    return Response('info\nsecurity-credentials/\n', mimetype='text/plain')

@app.route('/latest/meta-data/iam/info')
def iam_info():
    return jsonify({
        'Code': 'Success',
        'InstanceProfileArn': f'arn:aws:iam::123456789012:instance-profile/{IAM_ROLE}',
        'InstanceProfileId': 'AIPAZ3EXAMPLEPROFILEID'
    })

@app.route('/latest/meta-data/iam/security-credentials/')
@app.route('/latest/meta-data/iam/security-credentials')
def iam_roles():
    return Response(IAM_ROLE + '\n', mimetype='text/plain')

@app.route('/latest/meta-data/iam/security-credentials/<role>')
def iam_creds(role):
    return jsonify(IAM_CREDENTIALS)

@app.route('/latest/user-data')
def user_data():
    return Response('''#!/bin/bash
# PawsHaven EC2 User Data Script
export DB_HOST="pawshaven-db.c9ak27s.us-east-1.rds.amazonaws.com"
export DB_USER="pawshaven_admin"
export DB_PASS="V3t_Pr0d_P@ss!2024"
export REDIS_URL="redis://pawshaven-cache.abc123.use1.cache.amazonaws.com:6379"
export STRIPE_KEY="sk_live_paws_4eC39HqLyjWDarjtT1zdp7dc"
export FLAG="PAWSHAVEN{cl0ud_m3t4d4t4_cr3ds_st0l3n}"
''', mimetype='text/plain')

@app.route('/latest/meta-data/flag')
def flag():
    return Response('PAWSHAVEN{cl0ud_m3t4d4t4_cr3ds_st0l3n}\n', mimetype='text/plain')

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=1337)
