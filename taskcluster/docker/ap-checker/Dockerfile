FROM ghcr.io/eijebong/apwm:latest as apwm

FROM ghcr.io/eijebong/archipelago-worker:latest

# %include-run-task
# %include scripts/aplint_from_diff.py
COPY --from=apwm /usr/local/bin/apwm /usr/local/bin/apwm
COPY /topsrcdir/scripts/aplint_from_diff.py /ap/archipelago/aplint_from_diff.py
ADD --chmod=755 --checksum=sha256:c258668f5a2767e266460a4613094fa940f7dff0badeccf69bc9d5b6c03b1efa https://github.com/Eijebong/empty-apworld/releases/download/0.0.1/empty.apworld /ap

RUN apt update && apt install -y git jq zip

# Add worker user
RUN mkdir -p /builds && \
    useradd -d /builds/worker -s /bin/bash -m worker && \
    mkdir /builds/worker/artifacts && \
    mkdir /builds/worker/checkouts && \
    chown -R worker:worker /builds/worker /ap/archipelago

# Add UT to worlds
ADD --chmod=755 --checksum=sha256:279128ceb716e9954b38ea8e246276adb133411cec31157eed6b0a3fcabb572b https://github.com/FarisTheAncient/Archipelago/releases/download/Tracker_v0.2.23/tracker.apworld /ap/archipelago/worlds

# UT needs that even if it doesn't use it?
RUN mkdir /ap/archipelago/Players

ENV SHELL=/bin/bash \
    HOME=/builds/worker \
    PATH=/builds/worker/.local/bin:$PATH

