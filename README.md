# ingi-task-dev

Local INGInious matching the ansible deployment, minus Traefik/TLS/oauth2-proxy/LDAP.
Plain http on `:8080`.

```sh
docker compose up -d          # first run builds the frontend image (~10 min)
```

Log in at http://localhost:8080 as `superadmin` / `superadmin` (seeded on every
frontend start, `ADMIN_USER`/`ADMIN_PASSWORD` in `.env`; changing the username
means changing `superadmins:` in `configuration.yaml` too).

Courses live in `TASKS_DIR` (`./data/tasks`). Point it at a taskset checkout:

```sh
TASKS_DIR=~/Dev/INGI-FIX/taskset-test/tasks docker compose up -d
```

or use a `.env` file, as shown below. The frontend and both agents will see the same tasks.

## .env

`docker compose` reads `.env` from this directory automatically; `env.example` is
a template you can use (`cp env.example .env`). Edit it in place, or override per
invocation (`HTTP_PORT=9000 docker compose up -d`).

| Variable | Default | Effect |
| --- | --- | --- |
| `INGI_REPO` | `https://github.com/INGInious/INGInious` | Cloned in the image build |
| `INGI_REF` | `37f4438…` | Commit to check out |
| `HTTP_PORT` | `8080` | Host port mapped to the frontend's 8000 |
| `TASKS_DIR` | `./data/tasks` | Bind-mounted at `/inginious/tasks` in the frontend and both agents |
| `ADMIN_USER`/`ADMIN_PASSWORD` | `superadmin` | Seeded into Mongo on every frontend start |

## Rebuild after changing INGI_REF or plugins

```sh
docker compose up -d --build
```
