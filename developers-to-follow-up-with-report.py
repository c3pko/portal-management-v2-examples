import json
import requests
import datetime

now = datetime.datetime.now()
timestamp = datetime.datetime.timestamp(now)
nonconsuming_developers = {}  # key on developer_id
developers_needing_consume_permissions = []

base_url = "https://us.api.konghq.com/v2"
kpat = "kpat"
portal_id = "64b4be18-8338-11ee-b962-0242ac120002"

headers = {
    "Content-Type": "application/json",
    "Authorization": kpat
}


def main():
    try:
        apps = get_all_apps()
        if len(apps) > 0:
            get_apps_no_reg(apps)

        print("The following developers need to be granted Consume permissions: ", developers_needing_consume_permissions)
        print("The following developers may be blocked in consuming our services and should be promptly followed up with: ", list(nonconsuming_developers.keys()))
    except Exception as e:
        print(f"Error: {e}")


def get_all_apps():
    try:
        url = base_url + "/portals/" + portal_id + "/applications"
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            return response.json()["data"]
        else:
            print("Error:", response.status_code)
            return []
    except Exception as e:
        print(f"Error in get_all_apps: {e}")
        return []


def check_developer_permissions(developer_id):
    try:
        # get teams for that developer
        url = base_url + "/portals/" + portal_id + "/developers/" + developer_id + "/teams"
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            team_data = response.json()["data"]
        else:
            print("Error:", response.status_code)
            return False

        # get permissions for those teams
        if len(team_data) > 0:
            for team in team_data:
                team_id = team["id"]

                url = base_url + "/portals/" + portal_id + "/teams/" + team_id + "/assigned-roles"
                response = requests.get(url, headers=headers)

                if response.status_code == 200:
                    roles = response.json()["data"]
                else:
                    print("Error:", response.status_code)

                for role in roles:
                    if role["role_name"] == "API Consumer":
                        return True
        return False
    except Exception as e:
        print(f"Error in check_developer_permissions: {e}")
        return False


def get_apps_no_reg(apps):
    for app in apps:
        try:
            application_id = app["id"]
            developer_id = app["developer"]["id"]

            if app["registration_count"] < 1:
                try:
                    has_permissions = check_developer_permissions(developer_id)
                except Exception as e:
                    print(f"Error checking permissions for developer {developer_id}: {e}")
                    continue

                if not has_permissions:
                    # Add developer to the Need Permissions Report
                    try:
                        if developer_id not in developers_needing_consume_permissions:
                            developers_needing_consume_permissions.append(developer_id)
                    except Exception as e:
                        print(f"Error adding developer {developer_id} to permissions report: {e}")
                        continue

                if has_permissions:
                    # Check if it's been 48 hours since the developer created their application
                    try:
                        hours_passed = (timestamp - convert_string_to_timestamp(app["updated_at"])) / 3600
                    except Exception as e:
                        print(f"Error calculating hours passed for application {application_id}: {e}")
                        continue

                    print("hours_passed: ", hours_passed)

                    if hours_passed > 48:
                        try:
                            if developer_id not in nonconsuming_developers:
                                nonconsuming_developers[developer_id] = [application_id]
                            else:
                                nonconsuming_developers[developer_id].append(application_id)
                        except Exception as e:
                            print(f"Error adding application {application_id} to nonconsuming developers list: {e}")
                            continue

        except Exception as e:
            print(f"Unexpected error processing application {app['id']}: {e}")
            continue

def convert_string_to_timestamp(string_timestamp):
    try:
        datetime_object = datetime.datetime.strptime(string_timestamp, "%Y-%m-%dT%H:%M:%S.%fZ")
        unix_timestamp = datetime_object.timestamp()
        return unix_timestamp
    except Exception as e:
        print(f"Error converting timestamp: {e}")
        return None

main()
