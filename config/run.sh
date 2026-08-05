#!/bin/sh
set -e

# Run httpd as whoever owns the mounted tasks directory -- the user that ran
# docker compose up -- so task-editor writes come out host-owned.
uid=$(stat -c %u /inginious/tasks)
gid=$(stat -c %g /inginious/tasks)
if [ "$uid" -gt 0 ] && [ "$uid" != "$(id -u www-data)" ]; then
    groupmod -o -g "$gid" www-data
    usermod -o -u "$uid" -g "$gid" www-data
    chown -R www-data:www-data /inginious/logs /inginious/uploads /inginious/agent_tmp
fi

/ingivenv/bin/python3 /inginious/seed_admin.py || echo "seed_admin failed, continuing"
exec httpd -DFOREGROUND
