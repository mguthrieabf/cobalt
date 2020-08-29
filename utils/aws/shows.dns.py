#!/bin/env python
import boto3
import json
import sys

COBALT_ZONE = "abftech.com.au."


def format_json(response):
    print(json.dumps(response, sort_keys=True, indent=4))
    return json.dumps(response)


client = boto3.client("route53")

# Get all hosted zones
response = client.list_hosted_zones()
zones = response["HostedZones"]

# Get our zone
cobalt_zone_id = None
for zone in zones:

    if zone["Name"] == COBALT_ZONE:
        cobalt_zone_id = zone["Id"]

if not cobalt_zone_id:
    print("Zone not found: %s" % COBALT_ZONE)
    sys.exit(1)

# Get DNS
response = client.list_resource_record_sets(HostedZoneId=cobalt_zone_id)
format_json(response)
record_sets = response["ResourceRecordSets"]
for record_set in record_sets:
    if record_set["Type"] == "CNAME":
        resource_records = record_set["ResourceRecords"]
        for resource_record in resource_records:
            print(resource_record["Value"])

response = client.change_resource_record_sets(
    ChangeBatch={
        "Changes": [
            {
                "Action": "CREATE",
                #                'Action': 'DELETE',
                "ResourceRecordSet": {
                    "Name": "uat4.abftech.com.au",
                    "ResourceRecords": [
                        {
                            "Value": "cobalt-uat-4.eba-4ngvp62w.ap-southeast-2.elasticbeanstalk.com",
                        },
                    ],
                    "TTL": 300,
                    "Type": "CNAME",
                },
            },
        ],
        "Comment": "Added cobalt-uat-4",
    },
    HostedZoneId=cobalt_zone_id,
)

print(response)
