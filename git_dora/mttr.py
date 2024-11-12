import requests
import csv
from datetime import datetime
from collections import defaultdict

# Replace with your GitHub personal access token
GITHUB_TOKEN = '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'
REPO_OWNER = 'amittelus'  # e.g., 'amittelus'
REPO_NAME = 'k8s'    # e.g., 'k8s'

# Define the API URLs for issues
issues_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/issues"

# Set up headers for authentication
headers = {
    'Authorization': f'token {GITHUB_TOKEN}'
}

def get_all_issues():
    all_issues = []
    page = 1

    while True:
        # Fetch a page of issues
        response = requests.get(f"{issues_url}?state=closed&page={page}&per_page=100", headers=headers)
        if response.status_code == 200:
            issues = response.json()
            if not issues:
                break  # Exit the loop if no more issues are returned
            all_issues.extend(issues)
            page += 1
        else:
            print(f"Failed to fetch issues on page {page}. Status code: {response.status_code}")
            break

    return all_issues

def collect_closed_issue_data():
    issues = get_all_issues()
    closed_issue_data = []
    mttr_per_month = defaultdict(list)  # To store MTTR values for each month for averaging

    for issue in issues:
        # Skip pull requests which are included in the issues endpoint by checking the presence of 'pull_request' key
        if 'pull_request' in issue:
            continue

        # Check if the issue has a label "outage"
        labels = issue.get('labels', [])
        if not any(label['name'].lower() == 'outage' for label in labels):
            continue  # Skip if the issue does not have the 'outage' label

        # Extract relevant information for closed issues
        issue_number = issue.get('number')
        issue_title = issue.get('title')
        created_at = issue.get('created_at')
        closed_at = issue.get('closed_at')

        if closed_at:  # If the issue is closed
            created_date = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ")
            closed_date = datetime.strptime(closed_at, "%Y-%m-%dT%H:%M:%SZ")

            # Separate date and time for created and closed dates
            created_date_only = created_date.strftime("%Y-%m-%d")
            created_time_only = created_date.strftime("%H:%M:%S")
            closed_date_only = closed_date.strftime("%Y-%m-%d")
            closed_time_only = closed_date.strftime("%H:%M:%S")

            # Calculate MTTR in days and hours
            time_diff = closed_date - created_date
            mttr_in_days = time_diff.days
            mttr_in_hrs = time_diff.total_seconds() / 3600  # Convert seconds to hours

            # Get the month of issue closure
            issue_closed_month = closed_date.strftime("%Y-%m")

            # Store MTTR in hours for the respective month
            mttr_per_month[issue_closed_month].append(mttr_in_hrs)

            closed_issue_data.append({
                'issue_number': issue_number,
                'issue_title': issue_title,
                'created_date': created_date_only,
                'created_time': created_time_only,
                'closed_date': closed_date_only,
                'closed_time': closed_time_only,
                'mttr_in_days': mttr_in_days,
                'mttr_in_hrs': round(mttr_in_hrs, 2),
                'issue_closed_month': issue_closed_month
            })

    # Calculate average MTTR for each month
    avg_mttr_data = {
        month: round(sum(hours) / len(hours), 2) if hours else 0
        for month, hours in mttr_per_month.items()
    }

    # Add the avg_mttr_data to each row based on the issue_closed_month
    for row in closed_issue_data:
        row['avg_mttr_data'] = avg_mttr_data.get(row['issue_closed_month'], 0)

    # Write the closed issue data to a CSV file
    with open('closed_issues_mttr_outage.csv', 'w', newline='') as csvfile:
        fieldnames = ['issue_number', 'issue_title', 'created_date', 'created_time', 
                      'closed_date', 'closed_time', 'mttr_in_days', 'mttr_in_hrs',
                      'issue_closed_month', 'avg_mttr_data']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        writer.writerows(closed_issue_data)

    print(f"{len(closed_issue_data)} outage-related closed issues with MTTR saved to closed_issues_mttr_outage.csv")

if __name__ == "__main__":
    collect_closed_issue_data()
    
#################

import csv

def create_unique_avg_mttr():
    unique_values = {}

    # Read the closed issues data
    with open('closed_issues_mttr_outage.csv', 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            issue_closed_month = row['issue_closed_month']
            avg_mttr_data = float(row['avg_mttr_data'])
            
            # Store the average MTTR for each unique issue_closed_month
            # This will ensure only unique month values with their respective avg_mttr_data
            unique_values[issue_closed_month] = avg_mttr_data

    # Write the unique values to a new CSV file
    with open('unique_avg_mttr.csv', 'w', newline='') as csvfile:
        fieldnames = ['issue_closed_month', 'avg_mttr_data']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for month, avg_mttr in unique_values.items():
            writer.writerow({'issue_closed_month': month, 'avg_mttr_data': avg_mttr})

    print("Unique values saved to unique_avg_mttr.csv")

if __name__ == "__main__":
    create_unique_avg_mttr()

########################
#Graph for mttr

import csv
import matplotlib.pyplot as plt
from datetime import datetime

# Load data from unique_avg_mttr.csv
months = []
avg_mttr_hours = []

# Read the MTTR data
with open('unique_avg_mttr.csv', 'r') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        # Convert issue_closed_month to a datetime object for better plotting
        issue_closed_month = datetime.strptime(row['issue_closed_month'], "%Y-%m")
        months.append(issue_closed_month)
        avg_mttr_hours.append(float(row['avg_mttr_data']))

# Plot the MTTR data
plt.figure(figsize=(10, 6))
plt.plot(months, avg_mttr_hours, marker='o', color='b', linestyle='-', linewidth=2, markersize=6)

# Add labels and title
plt.xlabel("Month-Year")
plt.ylabel("Average MTTR (Hours)")
plt.title("Average MTTR Over Time")
plt.xticks(rotation=45)  # Rotate x-axis labels for better readability
plt.grid(True, which='both', linestyle='--', linewidth=0.5)

# Display the plot
plt.tight_layout()  # Adjust layout for better fit
plt.show()
