import requests
import csv
from datetime import datetime
from collections import defaultdict

# Replace with your GitHub token and repository details
GITHUB_TOKEN = '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'
REPO_OWNER = 'dyrector-io'  
REPO_NAME = 'dyrectorio'    

# Define the API URLs for releases and issues
releases_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases"
issues_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/issues"

# Set up headers for authentication
headers = {
    'Authorization': f'token {GITHUB_TOKEN}'
}

def get_releases():
    response = requests.get(releases_url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch releases. Status code: {response.status_code}")
        return []

def get_issues():
    response = requests.get(issues_url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch issues. Status code: {response.status_code}")
        return []

def calculate_incidents_after_release():
    releases = get_releases()
    issues = get_issues()

    # Data structures to store incidents and releases by month
    incidents_per_month = defaultdict(int)
    releases_per_month = defaultdict(int)
    release_incident_data = []
    
    for release in releases:
        tag_name = release.get('tag_name', 'No Tag')
        published_at = release.get('published_at')

        # Parse the release date
        release_date = datetime.strptime(published_at, "%Y-%m-%dT%H:%M:%SZ") if published_at else None
        incident_month = release_date.strftime("%Y-%m") if release_date else "Unknown"

        if not release_date:
            continue

        # Increment the count of releases for the corresponding month
        releases_per_month[incident_month] += 1

        # Find incidents (issues) created after this release
        incidents_count = 0
        for issue in issues:
            issue_created_at = issue.get('created_at')
            if issue_created_at:
                issue_date = datetime.strptime(issue_created_at, "%Y-%m-%dT%H:%M:%SZ")
                
                # Count the issue if it was created after the release date
                if issue_date > release_date:
                    incidents_count += 1

        # Increment the count of incidents for the corresponding month
        incidents_per_month[incident_month] += incidents_count

    # Calculate total deployments for each month
    total_deployments_per_month = {month: count for month, count in releases_per_month.items()}

    # Prepare release incident data with total deployments for each month
    for release in releases:
        tag_name = release.get('tag_name', 'No Tag')
        published_at = release.get('published_at')

        # Parse the release date
        release_date = datetime.strptime(published_at, "%Y-%m-%dT%H:%M:%SZ") if published_at else None
        incident_month = release_date.strftime("%Y-%m") if release_date else "Unknown"

        if not release_date:
            continue

        # Get incidents count for the month
        incidents_count = incidents_per_month[incident_month]

        # Get the total deployments for that month
        total_deployments = total_deployments_per_month[incident_month]

        # Calculate CFR (Change Failure Rate)
        cfr = (total_deployments / incidents_count * 100) if incidents_count > 0 else 0

        # Split release date into separate date and time
        release_date_only = release_date.strftime("%Y-%m-%d") if release_date else ''
        release_time_only = release_date.strftime("%H:%M:%S") if release_date else ''

        release_incident_data.append({
            'tag_name': tag_name,
            'release_date': release_date_only,
            'release_time': release_time_only,
            'incidents_count': incidents_count,
            'incident_month': incident_month,
            'total_deployments': total_deployments,
            'cfr in percentage(%)': cfr  # Updated column name
        })

    # Write the release incident data to a CSV file
    with open('release_incidents.csv', 'w', newline='') as csvfile:
        fieldnames = [
            'tag_name', 'release_date', 'release_time', 'incidents_count', 
            'incident_month', 'total_deployments', 'cfr in percentage(%)'  # Updated column name
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        writer.writerows(release_incident_data)

    print("Release incident data saved to release_incidents.csv")

if __name__ == "__main__":
    calculate_incidents_after_release()

##########################

import csv

def create_unique_incident_month_cfr():
    unique_values = set()

    # Read the release incidents data
    with open('release_incidents.csv', 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            incident_month = row['incident_month']
            cfr = row['cfr in percentage(%)']  # Use the updated column name
            unique_values.add((incident_month, cfr))  # Add tuple of (incident_month, cfr)

    # Write unique values to a new CSV file
    with open('unique_incident_month_cfr.csv', 'w', newline='') as csvfile:
        fieldnames = ['incident_month', 'cfr in percentage(%)']  # Updated field names
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for month, cfr_value in unique_values:
            writer.writerow({'incident_month': month, 'cfr in percentage(%)': cfr_value})  # Updated column name

    print("Unique incident month and CFR values saved to unique_incident_month_cfr.csv")

if __name__ == "__main__":
    create_unique_incident_month_cfr()
