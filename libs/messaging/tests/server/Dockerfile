FROM rabbitmq:4.1.1
COPY rabbitmq.conf /etc/rabbitmq
RUN mkdir /etc/rabbitmq/certs
COPY docker-entrypoint.sh /docker-entrypoint.sh
ENTRYPOINT ["/docker-entrypoint.sh"]
