FROM ghcr.io/naturalhpc/cerulean-test-docker-images/cerulean-fake-base:latest

USER root
RUN apt-get update && apt-get install -y --no-install-recommends python3 \
    python3-dev cython3 python3-setuptools python3-wheel build-essential \
    python3-pip openssl python3-openssl libffi-dev libssl-dev openssh-client && \
    pip3 install --upgrade pip

COPY tests/test_requirements.txt /home/cerulean/test_requirements.txt

RUN pip3 install -r /home/cerulean/test_requirements.txt

COPY . /home/cerulean/cerulean
RUN find /home/cerulean -path '*__pycache__*' -delete && \
    chown -R cerulean:cerulean /home/cerulean && \
    chmod +x /home/cerulean/cerulean/tests/container-test/run_tests.sh && \
    mv /home/cerulean/cerulean/tests/container-test/pytest.ini /home/cerulean/cerulean/pytest.ini && \
    mv /home/cerulean/cerulean/tests/container-test/mypy.ini /home/cerulean/cerulean/mypy.ini

USER cerulean
WORKDIR /home/cerulean/cerulean
CMD /home/cerulean/cerulean/tests/container-test/run_tests.sh
