import json
import requests

# use the GET /portals/{portalId}/teams endpoint to dynamically get your team mappings
email_to_team_mapping = {
    "manchestercity": ["Manchester City", "41efabc2-8338-11ee-b962-0242ac120002"],
    "liverpoolfc": ["Liverpool FC", "41efb0c2-8338-11ee-b962-0242ac120002"],
    "arsenal": ["Arsenal", "41efb202-8338-11ee-b962-0242ac120002"],
    "intermilan": ["Inter Milan", "41efb310-8338-11ee-b962-0242ac120002"]
}
mapped_teams = list(email_to_team_mapping.keys())

base_url = "https://us.api.konghq.com/v2"
kpat = "$KPAT"
headers = {
    "Content-Type": "application/json",
    "Authorization": kpat
}
portal_id = "64b4be18-8338-11ee-b962-0242ac120002"


def main():
    try:
        pending_developers = get_newly_registered_developers()
        print("pending devs", pending_developers)
        if len(pending_developers) > 0:
            process_pending_devs(pending_developers)
    except Exception as e:
        print("Error occurred during processing: ", e)


def get_newly_registered_developers():
    pending_devs = {}
    try:
        url = base_url + "/portals/" + portal_id + "/developers"
        response = requests.get(url, headers=headers)
    except Exception as e:
        print("Error fetching developers: ", e)
        return pending_devs

    if response.status_code == 200:
        developers = response.json()["data"]
        for developer in developers:
            if developer["status"] == "pending":
                email_domain = get_email_domain(developer["email"])
                pending_devs[developer["id"]] = email_domain
    else:
        print("Error:", response.status_code)
    return pending_devs


def get_email_domain(email_address):
    if not email_address:
        return None

    try:
        domain = email_address.split("@")[1].replace(".com", "")
        return domain
    except IndexError:
        print("Invalid email address:", email_address)
        return None


def approve_developer(id):
    try:
        url = base_url + "/portals/" + portal_id + "/developers/" + id
        payload = {"status": "approved"}
        response = requests.request("PATCH", url, json=payload, headers=headers)
        print(response.text)
    except Exception as e:
        print("Error approving developer:", id, e)


def assign_developer_to_team(dev_id, team_id):
    try:
        url = base_url + "/portals/" + portal_id + "/teams/" + team_id + "/developers"
        payload = {"id": dev_id}
        response = requests.request("POST", url, json=payload, headers=headers)
        print(response.text)
    except Exception as e:
        print("Error assigning developer", dev_id, "to team", team_id, e)


def process_pending_devs(pending_developers):
    for developer_id in pending_developers:
        domain = pending_developers[developer_id]
        if domain in mapped_teams:
            # first approve their signup
            approve_developer(developer_id)
            #then assign them to the appropriate team (can also do this in a batch, per team)
            team_id = email_to_team_mapping[domain][1]
            assign_developer_to_team(developer_id, team_id)


main()