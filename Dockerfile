# syntax=docker/dockerfile:1

FROM rockylinux/rockylinux:10 AS core

ARG PYTHON_VERSION=3.14
ARG INGI_REPO
ARG INGI_REF

RUN dnf update -y && \
    dnf install -y python${PYTHON_VERSION} python${PYTHON_VERSION}-pip git && \
    dnf clean all

WORKDIR /inginious
RUN git clone --filter=blob:none ${INGI_REPO} . && git checkout ${INGI_REF}
RUN pip${PYTHON_VERSION} install --no-cache-dir -e .
RUN rm -f /bin/python3 && ln -s /bin/python${PYTHON_VERSION} /bin/python3


FROM core AS frontend

ARG PYVER=3.12
ENV VENV=/ingivenv

# dnf runs on the platform interpreter, which core repointed at ${PYTHON_VERSION}
RUN ln -sf /usr/bin/python${PYVER} /usr/bin/python3

# No mod_ssl: TLS terminates at Traefik in production, and its stock ssl.conf
# wants a certificate this image has no reason to carry.
RUN dnf install -y gcc python${PYVER} python${PYVER}-devel epel-release httpd httpd-devel \
    make redhat-rpm-config which procps-ng && dnf clean all

RUN python${PYVER} -m venv ${VENV}

RUN curl -L https://github.com/GrahamDumpleton/mod_wsgi/archive/refs/tags/5.0.2.tar.gz -o /tmp/mod_wsgi.tar.gz && \
    tar -xzf /tmp/mod_wsgi.tar.gz -C /tmp && cd /tmp/mod_wsgi-5.0.2 && \
    ./configure --with-python=${VENV}/bin/python3 && make && make install && \
    rm -rf /tmp/mod_wsgi*

RUN ${VENV}/bin/python3 -m pip install --no-cache-dir -e ".[ldap]"

COPY plugs/ /inginious/plugs
RUN cp -r /inginious/plugs/inginious_katex /inginious/plugs/ntnu_inginious \
          /inginious/plugs/ntnu_problem_types /inginious/inginious/frontend/plugins/ && \
    ${VENV}/bin/python3 -m pip install --no-cache-dir \
        /inginious/plugs/ntnu_inginious /inginious/plugs/inginious_katex /inginious/plugs/ntnu_problem_types

# Placeholder ids; run.sh remaps them to the owner of the tasks mount at startup
RUN groupadd -r www-data && useradd -r -g www-data -M www-data

COPY config/httpd/ /etc/httpd/
COPY config/webapp-wrapper config/seed_admin.py /inginious/
COPY --chmod=0755 config/run.sh /inginious/run.sh

RUN mkdir -p /inginious/logs /inginious/tasks /inginious/backups /inginious/uploads /inginious/agent_tmp && \
    chown -R www-data:www-data /inginious

ENV TZ=Europe/Oslo
CMD ["/inginious/run.sh"]
