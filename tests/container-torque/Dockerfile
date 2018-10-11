FROM cerulean-test-base

RUN apt-get update && \
    apt-get -y install tar gcc g++ make \
        pkg-config libssl-dev libxml2-dev libboost-dev
RUN apt-get -y install wget

RUN mkdir /build
WORKDIR /build
RUN wget http://www.adaptivecomputing.com/index.php?wpfb_dl=3244 -O torque-6.1.2.tar.gz && \
    tar xf torque-6.1.2.tar.gz

WORKDIR /build/torque-6.1.2
RUN ./configure && \
    make && \
    make install

ADD start-services.sh /etc/start-services.sh
RUN chmod +x /etc/start-services.sh
CMD /etc/start-services.sh

HEALTHCHECK --interval=1s CMD ssh -o NoHostAuthenticationForLocalhost=yes -i /home/cerulean/.ssh/id1_rsa cerulean@localhost /bin/true && pbsnodes -l free $(hostname) || exit 1
