FROM ghcr.io/naturalhpc/cerulean-test-docker-images/cerulean-fake-base:latest

USER root
RUN apt-get update && apt-get install -y --no-install-recommends python3 \
    python3-dev cython3 python3-setuptools python3-wheel build-essential \
    python3-pip openssl python3-openssl libffi-dev libssl-dev openssh-client && \
    pip3 install --upgrade pip

RUN add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update && \
    apt-get install -y --no-install-recommends python3.7 python3.7-dev python3.7-venv \
    python3.8 python3.8-dev python3.8-venv python3.9 python3.9-dev python3.9-venv \
    python3-venv python3.11 python3.11-dev python3.11-venv python3.12 python3.12-dev \
    python3.12-venv

COPY tests/test_requirements.txt /home/cerulean/test_requirements.txt

COPY . /home/cerulean/cerulean
RUN find /home/cerulean -path '*__pycache__*' -delete && \
    chown -R cerulean:cerulean /home/cerulean && \
    chmod +x /home/cerulean/cerulean/tests/container-test/run_tests.sh && \
    mv /home/cerulean/cerulean/tests/container-test/pytest.ini /home/cerulean/cerulean/pytest.ini && \
    mv /home/cerulean/cerulean/tests/container-test/mypy.ini /home/cerulean/cerulean/mypy.ini

USER cerulean
WORKDIR /home/cerulean/cerulean
CMD /home/cerulean/cerulean/tests/container-test/run_tests.sh
