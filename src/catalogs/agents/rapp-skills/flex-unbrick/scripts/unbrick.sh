#!/bin/bash
# unbrick.sh — Flex Consumption storage-PNA unbrick runbook (from a 2026-07-09
# outage: 169 az calls re-derived by hand — never again).
#
# A management-group security policy can silently flip the function app's
# storage account to publicNetworkAccess=Disabled, which kills Flex apps.
#
# Usage: unbrick.sh check|fix <app> <rg> <storage>
#   check  read-only: subscription, storage PNA state, app state, health probe
#   fix    the mutation sequence: tag SecurityControl=Ignore -> enable PNA ->
#          full stop/start -> bounded health poll
set -euo pipefail
MODE="${1:?usage: unbrick.sh check|fix <app> <rg> <storage>}"
APP="${2:?app name required}"
RG="${3:?resource group required}"
ST="${4:?storage account required}"

SUB=$(az account show --query name -o tsv)
echo "subscription: $SUB (verify this is the subscription that owns $APP)"

PNA=$(az storage account show -n "$ST" -g "$RG" --query publicNetworkAccess -o tsv)
STATE=$(az functionapp show -n "$APP" -g "$RG" --query state -o tsv 2>/dev/null); STATE=${STATE:-?}
HTTP=$(curl -s -o /dev/null -m 15 -w '%{http_code}' "https://$APP.azurewebsites.net" || echo 000)
echo "storage $ST publicNetworkAccess: $PNA"
echo "app $APP state: $STATE | https probe: HTTP $HTTP"

if [ "$MODE" = "check" ]; then
  # The live probe is the truth. PNA=Disabled with a healthy probe is the
  # private-endpoint deployment shape, not an outage.
  case "$HTTP" in
    2??|3??|401|404)
      echo "FLEX-UNBRICK: HEALTHY (app answers HTTP $HTTP; PNA=$PNA$( [ "$PNA" = "Disabled" ] && echo ' — private-endpoint shape, expected'))";;
    *)
      if [ "$PNA" = "Disabled" ]; then
        echo "FLEX-UNBRICK: DEGRADED — classic PNA policy outage (run: unbrick.sh fix $APP $RG $ST)"
      else
        echo "FLEX-UNBRICK: DOWN-OTHER-CAUSE — probe failed (HTTP $HTTP) but PNA already Enabled; this runbook will NOT fix it, read the Function App logs"
      fi;;
  esac
  exit 0
fi

[ "$MODE" = "fix" ] || { echo "unknown mode: $MODE"; exit 1; }

STORAGE_ID=$(az storage account show -n "$ST" -g "$RG" --query id -o tsv)
echo "# 1/4 tag SecurityControl=Ignore (stops the MG policy re-disabling PNA)"
az tag update --resource-id "$STORAGE_ID" --operation Merge --tags SecurityControl=Ignore -o none
echo "# 2/4 enable public network access on $ST"
az storage account update -n "$ST" -g "$RG" --public-network-access Enabled -o none
echo "# 3/4 FULL stop/start of $APP (restart is not enough for Flex)"
az functionapp stop -n "$APP" -g "$RG" -o none
az functionapp start -n "$APP" -g "$RG" -o none
echo "# 4/4 health poll (max ~5 min)"
for i in $(seq 1 20); do
  HTTP=$(curl -s -o /dev/null -m 15 -w '%{http_code}' "https://$APP.azurewebsites.net" || echo 000)
  echo "  attempt $i: HTTP $HTTP"
  case "$HTTP" in 2??|3??|401|404) echo "FLEX-UNBRICK: RECOVERED (HTTP $HTTP)"; exit 0;; esac
  sleep 15
done
echo "FLEX-UNBRICK: STILL DOWN after 5 min — check your alert rules and the Function App logs"
exit 1
