FROM cerulean-test-base

USER root
RUN apt-get update && apt-get install -y python3 python3-dev \
    build-essential python3-pip openssl python-openssl libffi-dev \
    libssl-dev openssh-client

COPY tests/test_requirements.txt /home/cerulean/test_requirements.txt

RUN pip3 install -r /home/cerulean/test_requirements.txt

COPY . /home/cerulean/cerulean
RUN find /home/cerulean -path '*__pycache__*' -delete
RUN chown -R cerulean:cerulean /home/cerulean
RUN chmod +x /home/cerulean/cerulean/tests/container-test/run_tests.sh
RUN mv /home/cerulean/cerulean/tests/container-test/pytest.ini \
    /home/cerulean/cerulean/pytest.ini

USER cerulean
WORKDIR /home/cerulean/cerulean
CMD /home/cerulean/cerulean/tests/container-test/run_tests.sh
