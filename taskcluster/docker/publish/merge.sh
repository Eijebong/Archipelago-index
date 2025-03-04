#!/bin/sh -e

SECRET_URL="http://taskcluster/secrets/v1/secret/Archipelago-index"
SECRET=$(curl -f ${SECRET_URL})

TOKEN=$(echo "${SECRET}" | jq -r '.secret.gh_token')

curl -X PUT -f \
    -H "Accept: application/vnd.github+json" \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "X-GitHub-Api-Version: 2022-11-28" \
    https://api.github.com/repos/Eijebong/Archipelago-index/pulls/${GITHUB_PR}/merge \
    -d "{\"merge_method\": \"squash\", \"commit_message\": \"\", \"sha\": \"$ARCHIPELAGO_INDEX_HEAD_REV\"}" || exit 1
