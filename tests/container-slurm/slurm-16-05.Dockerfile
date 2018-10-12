FROM cerulean-test-base

USER root

# Install munge (needed by slurm)
RUN apt-get update && apt-get install -y munge libmunge2
RUN chmod 0700 /etc/munge /var/log/munge && \
chmod 0711 /var/lib/munge && \
mkdir /var/run/munge && \
chmod 0755 /var/run/munge && \
chmod 0400 /etc/munge/munge.key

RUN chown -R munge:munge /etc/munge /var/lib/munge /var/log/munge /var/run/munge


# Install slurm
RUN groupadd --system slurm && useradd --system --gid slurm --create-home slurm
RUN echo slurm:slurm | chpasswd

RUN mkdir -p /var/spool/slurmctld/state
RUN chown -R slurm:slurm /var/spool/slurmctld

RUN mkdir -p /usr/local/etc/slurm

RUN mkdir -p /var/log/slurm
RUN chown -R slurm:slurm /var/log/slurm

ADD slurm.cert /usr/local/etc/slurm/slurm.cert
ADD slurm.key /usr/local/etc/slurm/slurm.key
RUN chmod 600 /usr/local/etc/slurm/slurm.key

ADD install_slurm.sh /usr/local/bin/
ADD slurm_timeout.diff /usr/local/etc/
WORKDIR /usr/local
RUN apt-get update && apt-get --no-install-recommends install -y gcc make libssl-dev libmunge-dev tar wget patch
RUN /bin/bash /usr/local/bin/install_slurm.sh slurm-16-05-11-1.tar.gz

ADD slurm.conf /usr/local/etc/slurm/slurm.conf

# Add start-up scripts
ADD start-services.sh /etc/start-services.sh
RUN chmod +x /etc/start-services.sh
CMD /etc/start-services.sh

