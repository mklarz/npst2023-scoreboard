import json
import bleach
import collections
from datetime import datetime, timezone
from git import Repo

# Quick, dirty and very inefficent script to generate formatted data for the line graph
LIMIT = 10
START_DATETIME = datetime(2023, 12, 1, 12, tzinfo=timezone.utc)
START_TIMESTAMP = START_DATETIME.isoformat()

def format_item(timestamp, value):
    return [timestamp, value]

repo = Repo(".")
master = repo.heads.main
commits = list(repo.iter_commits(master))[::-1]

last_scoreboard = None
users = {}
users_currently_maxed_count_series = []
print("Parsing {} commits and creating series.json".format(len(commits)))
last_users_currently_maxed_count = 0
for commit in commits:
    commit_datetime = datetime.utcfromtimestamp(commit.committed_date).replace(tzinfo=timezone.utc)

    if START_DATETIME > commit_datetime:
        continue

    print("Parsing: {} - {}".format(commit.hexsha, commit_datetime))
    try:
        content = repo.git.show('{}:{}'.format(commit.hexsha, "scoreboard_test.min.json")).strip()
        try:
            scoreboard = json.loads(content)
        except Exception as e:
            # print(scoreboard)
            # print("Error for scoreboard ", e)
            continue
    except Exception as e2:
        content = repo.git.show('{}:{}'.format(commit.hexsha, "scoreboard.min.json")).strip()
        try:
            scoreboard = json.loads(content)
        except Exception as e:
            # print(scoreboard)
            # print("Error for scoreboard ", e)
            continue
        continue

    # Which day in the calendar are we on?
    current_advent_day = ((commit_datetime - START_DATETIME).days) + 1

    max_possible_solves = current_advent_day
    # Remove mondays
    max_possible_solves -= current_advent_day // 6

    last_scoreboard = scoreboard
    users_currently_maxed_count = 0
    for scoreboard_user in scoreboard:
        current_score = int(scoreboard_user["score"])
        current_solves = int(scoreboard_user["num_solves"])
        user_id = scoreboard_user["user_id"]
        last_solve = scoreboard_user["latest_solve_time"]

        if current_solves >= max_possible_solves:
            users_currently_maxed_count += 1

        if user_id not in users:
            users[user_id] = {
                "name": scoreboard_user["username"],
                "last_solve": last_solve,
                "solves": [format_item(START_TIMESTAMP, 0), format_item(last_solve, current_solves)],
                "score": [format_item(START_TIMESTAMP, 0), format_item(last_solve, current_score)],
            }
            continue

        user = users[user_id]

        if len(user["solves"]) > 0:
            last_challenge = user["solves"][-1]
            if current_solves != last_challenge[1]:
                user["solves"].append(format_item(last_solve, current_solves))
                user["score"].append(format_item(last_solve, current_score))

        users[user_id] = user
    print("Users with max solves:", users_currently_maxed_count)
    users_currently_maxed_count_series.append([commit_datetime.isoformat(), users_currently_maxed_count])
    last_users_currently_maxed_count = users_currently_maxed_count

series = {
    "users": [],
}

# Only extract topp <LIMIT> users
for index, scoreboard_user in enumerate(last_scoreboard[:LIMIT]):
    user_id = scoreboard_user["user_id"]
    user = users[user_id]
    last_challenge = scoreboard_user["num_solves"]
    base = {
        "name": bleach.clean(user["name"]), # there's a xss in the legend tooltip
        "type": "line",
        "step": "end",
        "emphasis":{
            "lineStyle": {
                "width": 6,
            }
        }
    } 
    series["users"].append({**base, **{"data": user["score"]}});

# Extract users from profiles
info = {
    "registered_users": 0,
    "hidden_users": 0,
    "organizations": collections.defaultdict(int),
    "users": [],
}
with open("profiles.min.json") as fd:
    profiles = json.load(fd)
    info["registered_users"] = len(profiles)
    for profile in profiles:
        profile["username"] = bleach.clean(profile["username"]) if profile["username"] else None
        if not profile["username"]:
            info["hidden_users"] += 1
        if profile["organization_id"] is not None:
            info["organizations"][profile["organization_id"]] += 1
        info["users"].append(profile)
info["users"] = sorted(info["users"], key=lambda d: d["valid_from"]) 

with open("info.json", "w") as fd:
    json.dump(info, fd)

with open("series.json", "w") as fd:
    json.dump(series, fd)

with open("users.json", "w") as fd:
    json.dump(users, fd)

with open("currently_maxed_users.json", "w") as fd:
    json.dump(users_currently_maxed_count_series, fd)

print("Done!")
