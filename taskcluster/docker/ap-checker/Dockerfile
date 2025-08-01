FROM ghcr.io/eijebong/apwm:latest as apwm

FROM ghcr.io/eijebong/archipelago-worker:latest

# %include-run-task
# %include scripts/aplint_from_diff.py
COPY --from=apwm /usr/local/bin/apwm /usr/local/bin/apwm
COPY /topsrcdir/scripts/aplint_from_diff.py /ap/archipelago/aplint_from_diff.py

RUN apt update && apt install -y git jq zip

# Add worker user
RUN mkdir -p /builds && \
    useradd -d /builds/worker -s /bin/bash -m worker && \
    mkdir /builds/worker/artifacts && \
    chown -R worker:worker /builds/worker /ap/archipelago

ENV SHELL=/bin/bash \
    HOME=/builds/worker \
    PATH=/builds/worker/.local/bin:$PATH
