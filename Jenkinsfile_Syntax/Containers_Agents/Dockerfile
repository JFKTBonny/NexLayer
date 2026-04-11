# ci/Dockerfile.build — your custom build image
FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    openjdk-17-jdk \
    maven \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Pre-cache Maven dependencies (speeds up builds)
WORKDIR /app
COPY pom.xml .
RUN mvn dependency:go-offline

USER 1000   # Never run as root