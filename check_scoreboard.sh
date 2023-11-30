#!/bin/bash
## NOTICE
# Dirty quick script to track the NPST2023 scoreboard. Buy me a beer :))

## CONSTANTS
BASE_URL="https://wiarnvnpsjysgqbwigrn.supabase.co"
LOGIN_URL="$BASE_URL/auth/v1/token?grant_type=password"
PROFILES_URL="$BASE_URL/rest/v1/profiles?select=*"
SCOREBOARD_URL="$BASE_URL/rest/v1/scoreboard?select=*"
SCRIPT_PATH="$( cd "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"

## GOGO
echo "Starting script..."
cd $SCRIPT_PATH # dirty
source "$SCRIPT_PATH/.env"

# Download newest scoreboard
curl -s "$SCOREBOARD_URL" -H "apikey: $DASS_APIKEY" -o "$SCRIPT_PATH/scoreboard.min.json"
# Download profiles
curl -s "$PROFILES_URL" -H "apikey: $DASS_APIKEY" -o "$SCRIPT_PATH/profiles.min.json"

# Let's "prettify" the json as well
cat "$SCRIPT_PATH/scoreboard.min.json" | jq > "$SCRIPT_PATH/scoreboard.json"
cat "$SCRIPT_PATH/profiles.min.json" | jq > "$SCRIPT_PATH/profiles.json"

if [[ `git status --porcelain` ]]; then
  echo "There are differences, updating"
  python3 ./generate_series.py
  git add -A
  git commit -m "[SCOREBOARD] update"
  git push origin main
else
  echo "No differences"
fi
