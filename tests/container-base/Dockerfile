FROM phusion/baseimage:0.9.22
# build as cerulean-test-base

USER root

# Add cerulean user
RUN groupadd --system cerulean && useradd --system --gid cerulean --create-home cerulean --shell /bin/bash
RUN echo cerulean:kingfisher | chpasswd

WORKDIR /home/cerulean
ADD .ssh .ssh
RUN chmod 700 .ssh && \
chmod 600 .ssh/id1_rsa .ssh/id2_rsa && \
chmod 644 .ssh/authorized_keys .ssh/id1_rsa.pub .ssh/id2_rsa.pub && \
chown -R cerulean:cerulean .ssh

# Create test files
ADD create-test-files.sh /home/cerulean/create-test-files.sh
RUN chmod +x /home/cerulean/create-test-files.sh && \
    /home/cerulean/create-test-files.sh && \
    chown -R cerulean:cerulean /home/cerulean/test_files
RUN rm /home/cerulean/create-test-files.sh
ADD endless-job.sh /usr/local/bin/endless-job.sh
RUN chmod +x /usr/local/bin/endless-job.sh

# Install SSH server
RUN apt-get update && apt-get install -y openssh-server
ADD ssh_host_dsa_key /etc/ssh/ssh_host_dsa_key
ADD ssh_host_dsa_key.pub /etc/ssh/ssh_host_dsa_key.pub
ADD ssh_host_ecdsa_key /etc/ssh/ssh_host_ecdsa_key
ADD ssh_host_ecdsa_key.pub /etc/ssh/ssh_host_ecdsa_key.pub
ADD ssh_host_ed25519_key /etc/ssh/ssh_host_ed25519_key
ADD ssh_host_ed25519_key.pub /etc/ssh/ssh_host_ed25519_key.pub
ADD ssh_host_rsa_key /etc/ssh/ssh_host_rsa_key
ADD ssh_host_rsa_key.pub /etc/ssh/ssh_host_rsa_key.pub
RUN chmod 600 /etc/ssh/*_key
EXPOSE 22

# Enable server side debug output
RUN echo "LogLevel DEBUG3" >>/etc/ssh/sshd_config
RUN sed -i -e 's^Subsystem[[:space:]]*sftp[[:space:]]*/usr/lib/openssh/sftp-server^Subsystem sftp /usr/lib/openssh/sftp-server -l DEBUG3^' /etc/ssh/sshd_config


# Add OpenMPI
RUN apt-get update && apt-get install -y openmpi-bin

# Add start-up scripts
ADD start-services.sh /etc/start-services.sh
RUN chmod +x /etc/start-services.sh
CMD /etc/start-services.sh

