FROM ghcr.io/eijebong/apwm:ci-554 as apwm

FROM ghcr.io/eijebong/archipelago-worker:ci-554

# %include-run-task
COPY --from=apwm /usr/local/bin/apwm /usr/local/bin/apwm

RUN apt update && apt install -y git jq

# Add worker user
RUN mkdir -p /builds && \
    useradd -d /builds/worker -s /bin/bash -m worker && \
    mkdir /builds/worker/artifacts && \
    chown -R worker:worker /builds/worker

ENV SHELL=/bin/bash \
    HOME=/builds/worker \
    PATH=/builds/worker/.local/bin:$PATH
