import requests
import csv
from datetime import datetime


GITHUB_TOKEN = ''   ## add token
REPO_OWNER = 'amittelus'  # e.g., 'amittelus'
REPO_NAME = 'k8s'

# Define the API URL for issues (fetching only closed issues)
issues_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/issues"

# Set up headers for authentication
headers = {
    'Authorization': f'token {GITHUB_TOKEN}'
}

def get_issues(state='closed', per_page=100):
    """Fetch issues from GitHub repository, paginated."""
    all_issues = []
    page = 1

    while True:
        # Make request for each page of issues
        response = requests.get(
            issues_url,
            headers=headers,
            params={'state': state, 'per_page': per_page, 'page': page}  # Filter for closed issues
        )
        if response.status_code != 200:
            break  # Stop if there's an error

        issues = response.json()
        if not issues:
            break  # Stop if no more issues are returned

        all_issues.extend(issues)
        page += 1  # Move to the next page

    return all_issues

def calculate_mttr(label_filter):
    """Fetch issues with both created_at and closed_at dates and calculate MTTR."""
    issues = get_issues()
    total_time_to_resolution = 0
    resolved_issue_count = 0
    mttr_data = []

    for issue in issues:
        if 'pull_request' in issue:  # Skip pull requests
            continue

        created_at = issue.get('created_at')
        closed_at = issue.get('closed_at')

        # Fetch issues where created_at exists and closed_at is not None
        if created_at and closed_at:
            # Fetch issue labels
            labels = [label['name'] for label in issue.get('labels', [])]

            # Filter based on specific label(s)
            if label_filter in labels:
                created_at_dt = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ")
                closed_at_dt = datetime.strptime(closed_at, "%Y-%m-%dT%H:%M:%SZ")

                # Calculate time to resolution (closed_at - created_at)
                time_to_resolution = closed_at_dt - created_at_dt
                total_time_to_resolution += time_to_resolution.total_seconds()
                resolved_issue_count += 1

                mttr_data.append({
                    'issue_number': issue['number'],
                    'title': issue['title'],
                    'created_at': created_at,
                    'closed_at': closed_at,
                    'time_to_resolution': time_to_resolution
                })

    # Calculate MTTR
    if resolved_issue_count > 0:
        avg_time_to_resolution = total_time_to_resolution / resolved_issue_count
        mttr_in_hours = avg_time_to_resolution / 3600  # Convert seconds to hours

        # Save MTTR data to CSV
        with open('mttr_data.csv', 'w', newline='') as csvfile:
            fieldnames = ['issue_number', 'title', 'created_at', 'closed_at', 'time_to_resolution']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for data in mttr_data:
                writer.writerow({
                    'issue_number': data['issue_number'],
                    'title': data['title'],
                    'created_at': data['created_at'],
                    'closed_at': data['closed_at'],
                    'time_to_resolution': str(data['time_to_resolution'])  # Convert timedelta to string
                })

        # Save MTTR summary to a separate CSV file
        with open('mttr_summary.csv', 'w', newline='') as summaryfile:
            summary_writer = csv.writer(summaryfile)
            summary_writer.writerow(['Label', 'MTTR (hours)'])
            summary_writer.writerow([label_filter, mttr_in_hours])

    else:
        with open('mttr_summary.csv', 'w', newline='') as summaryfile:
            summary_writer = csv.writer(summaryfile)
            summary_writer.writerow(['Label', 'MTTR (hours)'])
            summary_writer.writerow([label_filter, 'No issues found'])

if __name__ == "__main__":
    specific_label = 'outage'              #### Change this to the desired label
    calculate_mttr(specific_label)
