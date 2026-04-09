#!/bin/bash
echo "========================================"
echo "  NexLayer Docker Permission Diagnosis"
echo "========================================"

echo ""
echo "--- Jenkins Host User ---"
id jenkins
groups jenkins

echo ""
echo "--- Docker Socket ---"
ls -la /var/run/docker.sock
stat -c "Owner UID: %u | Owner GID: %g" /var/run/docker.sock

echo ""
echo "--- Docker Group on Host ---"
getent group docker

echo ""
echo "--- Is Jenkins in Docker Group? ---"
if id -nG jenkins | grep -qw docker; then
    echo "✅ YES — jenkins is in docker group"
else
    echo "❌ NO  — jenkins is NOT in docker group"
    echo "   Fix: sudo usermod -aG docker jenkins"
    echo "        sudo systemctl restart jenkins"
fi

echo ""
echo "--- Test Docker Access as Jenkins ---"
if sudo -u jenkins docker ps > /dev/null 2>&1; then
    echo "✅ Jenkins can access Docker daemon"
else
    echo "❌ Jenkins cannot access Docker daemon"
fi

echo ""
echo "--- Container Default User ---"
echo "python:3.11-slim runs as:"
docker run --rm python:3.11-slim id

echo ""
echo "--- Socket GID Inside Container ---"
docker run --rm \
    -v /var/run/docker.sock:/var/run/docker.sock \
    python:3.11-slim \
    stat -c "Socket GID inside container: %g" /var/run/docker.sock

echo ""
echo "========================================"
echo "  Recommended Fix Summary"
echo "========================================"
DOCKER_GID=$(stat -c '%g' /var/run/docker.sock)
echo "Host docker GID:   ${DOCKER_GID}"
echo "Add to Jenkinsfile args:"
echo "  args '-v /var/run/docker.sock:/var/run/docker.sock"
echo "        --group-add ${DOCKER_GID}'"