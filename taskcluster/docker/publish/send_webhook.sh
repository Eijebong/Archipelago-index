#!/bin/sh

SECRET_URL="http://taskcluster/secrets/v1/secret/ap-lobby"
SECRET=$(curl ${SECRET_URL})

KEY=$(echo "${SECRET}" | jq -r '.secret.admin_key_staging')
curl -H "X-Api-Key: ${KEY}" https://ap-lobby-stg.bananium.fr/worlds/refresh

KEY=$(echo "${SECRET}" | jq -r '.secret.admin_key_prod')
curl -H "X-Api-Key: ${KEY}" https://ap-lobby.bananium.fr/worlds/refresh

