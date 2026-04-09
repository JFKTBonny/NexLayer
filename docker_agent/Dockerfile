
# ci/Dockerfile.python-docker
FROM python:3.11-slim

ARG JENKINS_UID=125
ARG JENKINS_GID=132
ARG DOCKER_GID=135

# Install system dependencies + Docker CLI
RUN apt-get update -qq && \
    apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    gnupg && \
    install -m 0755 -d /etc/apt/keyrings && \
    curl -fsSL https://download.docker.com/linux/debian/gpg \
    -o /etc/apt/keyrings/docker.asc && \
    chmod a+r /etc/apt/keyrings/docker.asc && \
    echo \
    "deb [arch=$(dpkg --print-architecture) \
    signed-by=/etc/apt/keyrings/docker.asc] \
    https://download.docker.com/linux/debian \
    $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
    | tee /etc/apt/sources.list.d/docker.list > /dev/null && \
    apt-get update -qq && \
    apt-get install -y --no-install-recommends \
    docker-ce-cli && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create groups and user matching Jenkins host exactly
RUN groupadd -f -g ${JENKINS_GID} jenkins && \
    groupadd -f -g ${DOCKER_GID} docker && \
    useradd -m \
    -u ${JENKINS_UID} \
    -g ${JENKINS_GID} \
    -G docker \
    -s /bin/bash \
    jenkins

# Create pip directories owned by jenkins
RUN mkdir -p /home/jenkins/.cache/pip && \
    mkdir -p /home/jenkins/.local/lib && \
    chown -R jenkins:jenkins /home/jenkins

# Switch to jenkins user
USER jenkins

# Set pip cache to jenkins home
ENV HOME=/home/jenkins
ENV PIP_CACHE_DIR=/home/jenkins/.cache/pip
ENV PATH="/home/jenkins/.local/bin:${PATH}"

# Pre-install Python CI tools as jenkins user
# No permission issues — jenkins owns home dir
RUN pip install --no-cache-dir \
    black==24.3.0 \
    flake8==7.0.0 \
    bandit \
    safety \
    pytest \
    pytest-flask \
    pytest-cov

WORKDIR /home/jenkins