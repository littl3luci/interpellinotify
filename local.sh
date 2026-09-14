#!/bin/bash
# Fa localmente il lavoro del cron GitHub (check.yml).
#   ./local.sh         spegne il workflow su GitHub, poi ogni 10 min: pull, interpelli.py, commit+push seen
#   Ctrl-C             riaccende il workflow e esce
#   ./local.sh once    un solo giro (pull, interpelli.py, commit+push seen), non tocca il workflow
#   ./local.sh github  riaccende solo il workflow (se il loop è morto senza Ctrl-C)
# Richiede: ~/.config/interpellinotify-token (PAT con actions:write) e ~/.config/interpellinotify-ntfy (URL topic ntfy)
set -u
cd "$(dirname "$0")"
API=https://api.github.com/repos/littl3luci/interpellinotify/actions/workflows/check.yml
gh() { curl -sf -o /dev/null -X PUT -H "Authorization: Bearer $(cat ~/.config/interpellinotify-token)" "$API/$1" && echo "workflow github: $1"; }
run() {
    git pull -q --rebase
    python3 interpelli.py
    git add interpelli.seen.json && git diff --cached --quiet || git commit -qm seen && git push -q
}

[ "${1-}" = github ] && { gh enable; exit; }
export NTFY=$(cat ~/.config/interpellinotify-ntfy)
[ "${1-}" = once ] && { run; exit; }
gh disable || exit 1
trap 'gh enable; exit' INT TERM
while :; do run; sleep 600; done
