#inherit from the base container, which have all the needed script to launch tasks
ARG   VERSION=latest
ARG   REGISTRY=ghcr.io
FROM  ${REGISTRY}/inginious/env-base:${VERSION}

LABEL org.opencontainers.image.source=https://github.com/INGInious/containers
LABEL org.opencontainers.image.description="Default INGInious grading environment."

# Add gcc
RUN     dnf install -y gcc gcc-c++ gdb cpp make valgrind binutils libstdc++ clang clang-devel llvm automake check check-devel zlib-devel openssl-devel time && \
        dnf clean all
