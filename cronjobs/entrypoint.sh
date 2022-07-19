#!/bin/bash

usermod -u ${OWNER_UID} cronworker
chown cronworker:cronworker /home/cronworker -R
cat >> /tmp/entrypoint.sh <<'EOF'
#!/bin/bash
PATH="$PATH:/home/cronworker/.local/bin"
echo $PATH
/usr/bin/python3 /usr/local/bin/run.py "$@"

EOF
chmod a+x /tmp/entrypoint.sh
gosu cronworker /tmp/entrypoint.sh "$@"