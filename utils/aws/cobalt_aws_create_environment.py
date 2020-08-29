#!/bin/env python
import boto3
import json
import sys
import argparse
import subprocess

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


def build_environment(env_name, env_type, varfile, localdb):

    # create environment variable string
    envs = ""
    with varfile as infile:
        for line in infile:
            envs += line.strip() + ","
    envs = envs[:-1]
    if localdb:
        envs += ",USE_SQLITE=True"

    print(envs)
    print(env_name)
    print(env_type)
    print(localdb)

    result = subprocess.run(
        ["eb", "create", "--keyname", "cobalt", "--envvars", envs],
        stdout=subprocess.PIPE,
    )
    data = result.stdout.decode("utf-8").split("\n")
    print(data)


def main():
    # this env_name filename --localdb

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
    parser.add_argument(
        "-l",
        "--localdb",
        action="store_true",
        default=False,
        help="Use a local database. Otherwise use values from varfile to connect to database.",
    )

    args = parser.parse_args()

    build_environment(args.env_name, args.env_type, args.varfile, args.localdb)


if __name__ == "__main__":
    main()
