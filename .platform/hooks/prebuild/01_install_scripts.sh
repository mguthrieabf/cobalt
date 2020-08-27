#!/bin/bash

###########################
# Install utility scripts #
###########################

cp /root/.bashrc /root/.bashrc.old

# ec2-user bash login script
cat << EOF > /home/ec2-user/.bashrc
#!/bin/bash
# Source global definitions
if [ -f /etc/bashrc ]; then
	. /etc/bashrc
fi
# Pretty much everything requires root so su immediately
alias x='exit'
sudo -s
EOF

# root bash login script
cat << EOF > /root/.bashrc
#!/bin/bash
# root now so do stuff
alias x='exit'

# activate virtualenv
. /var/app/venv/staging-LQM1lest/bin/activate

# set environment variables
`cat /opt/elasticbeanstalk/deployment/env | awk '{print "export",$1}'`

# change to app directory
cd /var/app/current

clear
echo $COBALT_HOSTNAME
cat /cobalt-media/admin/env.txt
EOF

# tlog command
cat << EOF > /usr/local/bin/tlog
#!/bin/bash

clear
echo
echo Logs live in /var/log
echo
PS3='Select a log file: '
options=("cfn-init.log (install file)" "cfn-init-cmd.log (install file details)" "web.stdout.log (print and errors from app)" "nginx/access.log (web access log)" "nginx/error.log (web error log)" "Quit")
select opt in "\${options[@]}"
do
    case \$opt in
        "cfn-init.log (install file)")
            tail -100f /var/log/cfn-init.log
            break
            ;;
        "cfn-init-cmd.log (install file details)")
            tail -100f /var/log/cfn-init-cmd.log
            break
          ;;
        "web.stdout.log (print and errors from app)")
            tail -100f /var/log/web.stdout.log | grep -v "Invalid HTTP_HOST"
            break
            ;;
        "nginx/access.log (web access log)")
            tail -1000f /var/log/nginx/access.log | grep -v health
            break
            ;;
        "nginx/error.log (web error log)")
            tail -1000f /var/log/nginx/error.log
            break
            ;;
        "Quit")
            break
            ;;
        *) echo "invalid option $REPLY";;
    esac
done
EOF
chmod 755 /usr/local/bin/tlog

# help file
cat << EOF > /usr/local/bin/h
echo
echo files
echo /opt/elasticbeanstalk/deploy/env - environment vars
echo /etc/nginx     \t\t\t                  - nginx config
echo
echo Commands
echo nginx -t                         - test config

EOF
chmod 755 /usr/local/bin/h
