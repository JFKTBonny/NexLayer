# ci/Dockerfile.python-docker
FROM python:3.11-slim

ARG DOCKER_GID=137     # matches host docker group GID

# Install Docker CLI
RUN apt-get update -qq && \
    apt-get install -y --no-install-recommends \
    ca-certificates curl gnupg && \
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
    apt-get install -y --no-install-recommends docker-ce-cli && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create jenkins user matching host UID/GID
RUN groupadd -g ${DOCKER_GID} docker && \
    groupadd -g 1000 jenkins && \
    useradd -m -u 1000 -g jenkins -G docker jenkins

# Pre-install Python CI tools
RUN pip install --no-cache-dir \
    flake8    \
    bandit    \
    safety    \
    pytest    \
    pytest-flask \
    pytest-cov

# Switch to jenkins user — not root
USER jenkins

WORKDIR /home/jenkins