FROM python:3.14-bookworm

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        ca-certificates \
        curl \
        gcc \
        git \
        less \
        libsqlite3-dev \
        procps \
        ripgrep \
        sqlite3 \
        sudo \
        vim \
        bash-completion \
    && rm -rf /var/lib/apt/lists/*

ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=${USER_UID}

ENV PATH="/home/${USERNAME}/.local/bin:${PATH}"

RUN if ! id -u ${USERNAME} >/dev/null 2>&1; then \
        groupadd --gid ${USER_GID} ${USERNAME} \
        && useradd --uid ${USER_UID} --gid ${USER_GID} -m -s /bin/bash ${USERNAME} \
        && echo "${USERNAME} ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/${USERNAME} \
        && chmod 0440 /etc/sudoers.d/${USERNAME}; \
    fi

RUN python -m pip install --no-cache-dir --upgrade \
        pip \
        'setuptools>=77,<80' \
        wheel \
        build \
        cython \
        pdbpp \
        pytest \
        pytest-cov \
        tox \
        uv

WORKDIR /workspaces/workhours

EXPOSE 6543

USER ${USERNAME}
