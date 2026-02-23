FROM ghcr.io/eijebong/apwm:latest as apwm

FROM ghcr.io/eijebong/archipelago-worker:latest

# %include-run-task
# %include scripts/aplint_from_diff.py
COPY --from=apwm /usr/local/bin/apwm /usr/local/bin/apwm
COPY /topsrcdir/scripts/aplint_from_diff.py /ap/archipelago/aplint_from_diff.py
ADD --chmod=755 --checksum=sha256:c258668f5a2767e266460a4613094fa940f7dff0badeccf69bc9d5b6c03b1efa https://github.com/Eijebong/empty-apworld/releases/download/0.0.1/empty.apworld /ap
ADD --chmod=755 --checksum=sha256:ce5674e899d0303f156d43f2c8ebe026498031bf7cd3382524c1d02ee359d463 https://github.com/FarisTheAncient/Archipelago/releases/download/Tracker_v0.2.26/tracker.apworld /ap/archipelago/worlds
ADD --chmod=755 --checksum=sha256:c187ca024f40b057da7c0c44a529b51f7cee8159dc82c744e381ce91b49760c2 https://raw.githubusercontent.com/Mysteryem/Archipelago-fuzzer/8148d97ff4fe9a09b672d9c4a4fb01f06164fef1/hooks/detect_rule_variable_capture_issues.py /ap/archipelago/hooks
ADD --chmod=755 --checksum=sha256:bff42dd45bdf158bb4a5437699aae120716990abe98d2b24c673b02cecd1fc78 https://raw.githubusercontent.com/Mysteryem/Archipelago-fuzzer/7bc2dcd4367d1450cda11f0c1bc1f2edb385e218/hooks/check_placement_item_location_references.py /ap/archipelago/hooks

# UT needs that even if it doesn't use it?
RUN mkdir /ap/archipelago/Players

RUN apt update && apt install -y git jq zip

# Add worker user
RUN mkdir -p /builds && \
    useradd -d /builds/worker -s /bin/bash -m worker && \
    mkdir /builds/worker/artifacts && \
    mkdir /builds/worker/checkouts && \
    chown -R worker:worker /builds/worker /ap/archipelago

ENV SHELL=/bin/bash \
    HOME=/builds/worker \
    PATH=/builds/worker/.local/bin:$PATH

