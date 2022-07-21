#!/bin/bash

usermod -u ${OWNER_UID} cronworker
chown cronworker:cronworker /home/cronworker -R

cat >> /tmp/entrypoint.sh <<'EOF'
#!/bin/bash
# pipx install -e /opt/wodoo --force
PATH="$PATH:/home/cronworker/.local/bin"
echo $PATH
/usr/bin/python3 /usr/local/bin/run.py "$@"

EOF
chmod a+x /tmp/entrypoint.sh
gosu cronworker sudo -E /tmp/entrypoint.sh "$@"