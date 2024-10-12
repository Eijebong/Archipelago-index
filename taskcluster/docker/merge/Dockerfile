FROM alpine:latest

RUN apk update && apk add bash coreutils python3 openssh-client git curl jq
COPY merge.sh /usr/local/bin/merge.sh
RUN chmod +x /usr/local/bin/merge.sh

# %include-run-task

# Add worker user
RUN mkdir -p /builds && \
    adduser -h /builds/worker -s /bin/ash -D worker && \
    mkdir -p /builds/worker/artifacts && \
    chown worker:worker /builds/worker/artifacts /builds/worker

ENV SHELL=/bin/ash \
    HOME=/builds/worker \
    PATH=/builds/worker/.local/bin:$PATH

VOLUME /builds/worker/checkouts
VOLUME /builds/worker/.cache

