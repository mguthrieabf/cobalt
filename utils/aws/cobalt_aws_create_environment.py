#!/bin/env python
import boto3
import json
import sys
import argparse
import subprocess
import time
from cobalt_aws_add_to_dns import add_to_aws_dns

# build environment

# 1. get base config - test, uat, prod, standalone
# 2. run eb create
# eb create cobalt-uat-2 --keyname cobalt --envvars `cat /tmp/cobalt-uat.env | tr "\n" ","`USE_SQLITE=False

# 3. update dns
# 4. update LB (manually for now or ignore errors)
# 5. For standalone:
#    a) run test build
#    b) change perms on db.sqlite3
# 6. For test and UAT install cron job
# eb ssh cobalt-uat-1 --command "sudo id"


def build_environment(env_name, env_type, varfile, eb_dns_name):

    print("\nConfirmation")
    print("============\n")
    print("Environment: %s" % env_name)
    print("Type: %s" % env_type)
    print("Input file: %s" % varfile)
    print("DNS: %s.abftech.com.au" % eb_dns_name)
    print("\nEnsure you have committed your git changes.\n")
    print(
        "\nIf ssh is required to complete installation you will need to type YES in about 5 minutes.\n"
    )
    input("Press Enter to continue...")

    # create environment variable string
    envs = ""
    with varfile as infile:
        for line in infile:
            envs += line.strip() + ","
    envs = envs[:-1]
    if env_type == "standalone":
        envs += ",USE_SQLITE=True"

    print("Creating environment. This will take several minutes.")
    #    result = subprocess.run(["eb", "create", "--keyname", "cobalt", "--envvars", envs], stdout=subprocess.PIPE)
    process = subprocess.Popen(
        ["eb", "create", env_name, "--keyname", "cobalt", "--envvars", envs]
    )
    #    process = subprocess.Popen(['sleep', '4'])
    result, errs = process.communicate()

    # We don't get a return code so use API to check if environment was built
    ebclient = boto3.client("elasticbeanstalk")
    response = ebclient.describe_environments(EnvironmentNames=[env_name])

    print("Checking environment.")
    if len(response["Environments"]) > 0:
        print("Environment exists.")
    else:
        print("Environment not found. Error creating environment.")
        sys.exit(1)

    # Add DNS
    print("Adding DNS")
    rc, ret = add_to_aws_dns(eb_dns_name, env_name)
    print(ret)

    # Run commands for local database environments
    if env_type == "standalone":
        subprocess.run(
            [
                "eb",
                "ssh",
                env_name,
                "--command",
                "-f sudo /var/app/current/utils/aws/rebuild_test_data_sqlite3.sh",
            ],
            stdout=subprocess.PIPE,
        )
        subprocess.run(
            [
                "eb",
                "ssh",
                env_name,
                "--command",
                "-f sudo crontab /var/app/current/utial/aws/rebuild_test_data_sqlite3_crontab.txt",
            ],
            stdout=subprocess.PIPE,
        )


def main():

    ENVS = ["test", "uat", "production", "standalone"]

    parser = argparse.ArgumentParser()
    parser.add_argument("env_name", type=str, help="Environment name")
    parser.add_argument(
        "varfile", type=argparse.FileType("r"), help="File with environment variable"
    )
    parser.add_argument(
        "-t",
        "--env_type",
        choices=ENVS,
        help="Environment. Options are: " + ", ".join(ENVS),
        required=True,
        metavar="",
    )
    parser.add_argument("-d", "--dns_name", help="DNS sub-domain. Defaults to env_name")

    args = parser.parse_args()

    if args.dns_name:
        dns = args.dns_name
    else:
        dns = args.env_name

    build_environment(args.env_name, args.env_type, args.varfile, dns)


if __name__ == "__main__":
    main()
