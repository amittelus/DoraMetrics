import requests
import csv
from datetime import datetime
from collections import defaultdict

# Replace with your GitHub personal access token
GITHUB_TOKEN = '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'
REPO_OWNER = 'dyrector-io'  
REPO_NAME = 'dyrectorio'    

# Define the API URL for fetching releases
releases_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases"

# Set up headers for authentication
headers = {
    'Authorization': f'token {GITHUB_TOKEN}'
}

def get_total_releases():
    try:
        # Make a request to fetch the releases
        response = requests.get(releases_url, headers=headers)

        # Check if the request was successful
        if response.status_code == 200:
            releases = response.json()

            # Dictionary to count releases per month
            releases_per_month = defaultdict(int)

            # List to store details for the CSV output
            release_details = []

            # Calculate the releases per month and gather details
            for release in releases:
                published_at = release.get('published_at')
                tag_name = release.get('tag_name', '')

                # Extract the date component if the timestamp exists
                if published_at:
                    date_obj = datetime.strptime(published_at.split('T')[0], "%Y-%m-%d")
                    month_year = date_obj.strftime("%Y-%m")
                    releases_per_month[month_year] += 1
                    published_date = published_at.split('T')[0]  # Get only the date part

                    release_details.append({
                        'tag_name': tag_name,
                        'published_date': published_date,
                        'month_year': month_year
                    })

            # Save the release data to a CSV file
            with open('releases_summary.csv', 'w', newline='') as csvfile:
                fieldnames = ['tag_name', 'published_date', 'month_year', 'number_of_releases_every_month']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                # Write the header
                writer.writeheader()

                # Write each release's details along with release counts
                for detail in release_details:
                    writer.writerow({
                        'tag_name': detail['tag_name'],
                        'published_date': detail['published_date'],
                        'month_year': detail['month_year'],
                        'number_of_releases_every_month': releases_per_month[detail['month_year']]
                    })

            print("Release details saved to releases_summary.csv")
        else:
            print(f"Failed to fetch releases. Status code: {response.status_code}")
            print(response.json())
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    get_total_releases()

#########################
#creating another file which contain unique month and df for each month 
import csv
from collections import defaultdict

def create_depfreq_csv():
    try:
        # Dictionary to store deployment counts per month-year
        deployments_per_month = defaultdict(int)

        # Read data from releases_summary.csv
        with open('releases_summary.csv', 'r') as csvfile:
            reader = csv.DictReader(csvfile)

            # Iterate through each row to count deployments per month-year
            for row in reader:
                month_year = row['month_year']
                number_of_releases = int(row['number_of_releases_every_month'])
                deployments_per_month[month_year] += number_of_releases

        # Prepare data for depfreq.csv
        depfreq_data = [{'month_year': month, 'number_of_deployments': count} for month, count in deployments_per_month.items()]

        # Write to depfreq.csv
        with open('depfreq.csv', 'w', newline='') as csvfile:
            fieldnames = ['month_year', 'number_of_deployments']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            # Write the rows
            writer.writerows(depfreq_data)

        print("Deployment frequency details saved to depfreq.csv")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    create_depfreq_csv()

##########################
# ##Graph for df
import csv
import matplotlib.pyplot as plt

# Read Deployment Frequency data from CSV file
def read_deployment_data():
    """Read the deployment frequency data from the CSV file."""
    months = []
    deployments = []

    # Read the deployment frequency data file
    with open('depfreq.csv', 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            months.append(row['month_year'])
            deployments.append(int(row['number_of_deployments']))

    return months, deployments

# Plot the Deployment Frequency graph (Bar format)
def plot_deployment_frequency_graph(months, deployments, filename="deployment_frequency_graph.png"):
    """Plot the Deployment Frequency bar graph and save it as a PNG file."""
    plt.figure(figsize=(10, 6))
    plt.bar(months, deployments, color='teal')
    plt.xlabel('Month')
    plt.ylabel('Number of Deployments')
    plt.title('Deployment Frequency by Month')
    plt.xticks(rotation=45)
    plt.tight_layout()

    # Save the graph as a PNG file
    plt.savefig(filename)
    print(f"Deployment Frequency bar graph saved as {filename}")

if __name__ == "__main__":
    # Read Deployment Frequency data
    months, deployments = read_deployment_data()

    # Plot the Deployment Frequency bar graph and save it as an image
    plot_deployment_frequency_graph(months, deployments)

#####################################
###cfr.py

import requests
import csv
from datetime import datetime
from collections import defaultdict

# Replace with your GitHub token and repository details
# GITHUB_TOKEN = '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'
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

#####################
# #CFR graph plotting
import csv
import matplotlib.pyplot as plt

# Read the unique incident month and CFR data from CSV file
def read_cfr_data():
    """Read the CFR data from the CSV file."""
    months = []
    cfr_values = []

    # Read the unique incident month and CFR data file
    with open('unique_incident_month_cfr.csv', 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            months.append(row['incident_month'])
            cfr_values.append(float(row['cfr in percentage(%)']))

    return months, cfr_values

# Plot the Change Failure Rate (CFR) graph (Bar format)
def plot_cfr_graph(months, cfr_values, filename="cfr_graph_bar.png"):
    """Plot the CFR bar graph and save it as a PNG file."""
    plt.figure(figsize=(10, 6))
    plt.bar(months, cfr_values, color='purple')
    plt.xlabel('Month')
    plt.ylabel('CFR (%)')
    plt.title('Change Failure Rate by Month')
    plt.xticks(rotation=45)
    plt.tight_layout()

    # Save the graph as a PNG file
    plt.savefig(filename)
    print(f"CFR bar graph saved as {filename}")

if __name__ == "__main__":
    # Read CFR data
    months, cfr_values = read_cfr_data()

    # Plot the CFR bar graph and save it as an image
    plot_cfr_graph(months, cfr_values)

#########################
##ltforchange.py

import requests
import csv
from datetime import datetime
from collections import defaultdict

# Replace with your GitHub personal access token
# GITHUB_TOKEN = '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'
REPO_OWNER = 'dyrector-io'  
REPO_NAME = 'dyrectorio'    

# Define the API URL for fetching pull requests
pulls_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/pulls?state=all"

# Set up headers for authentication
headers = {
    'Authorization': f'token {GITHUB_TOKEN}'
}

def get_pr_details():
    try:
        # Make a request to fetch the pull requests
        response = requests.get(pulls_url, headers=headers)

        # Check if the request was successful
        if response.status_code == 200:
            prs = response.json()

            # Data structure to calculate average lead time per month
            monthly_data = defaultdict(lambda: {'total_hours': 0, 'count': 0})

            # Save the PR details to a CSV file
            with open('pr_details.csv', 'w', newline='') as csvfile:
                fieldnames = ['pr_number', 'pr_title', 'pr_created_date', 'pr_created_time', 'released_date', 'released_time', 
                              'lead_time_change_in_days', 'lead_time_change_in_hrs', 'month_year', 'avg_lead_time_change_in_hrs']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                # Write the header
                writer.writeheader()

                # Write each PR's details into the CSV
                for pr in prs:
                    # Parse the created_at timestamp for the PR
                    created_at = pr.get('created_at')
                    created_date = created_at.split('T')[0] if created_at else ''
                    created_time = created_at.split('T')[1].replace('Z', '') if created_at else ''

                    # Parse the merged_at timestamp for the PR (indicating the release time)
                    merged_at = pr.get('merged_at')
                    released_date = merged_at.split('T')[0] if merged_at else 'Not Merged'
                    released_time = merged_at.split('T')[1].replace('Z', '') if merged_at else 'Not Merged'

                    # Calculate the lead time if the PR is merged
                    lead_time_change_in_days = ''
                    lead_time_change_in_hrs = ''

                    if merged_at:
                        # Convert the date strings to datetime objects
                        created_datetime = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ")
                        merged_datetime = datetime.strptime(merged_at, "%Y-%m-%dT%H:%M:%SZ")

                        # Calculate the difference in days and hours
                        time_diff = merged_datetime - created_datetime
                        lead_time_change_in_days = time_diff.days
                        lead_time_change_in_hrs = time_diff.total_seconds() // 3600  # Convert seconds to hours

                        # Extract month and year for grouping
                        month_year = merged_datetime.strftime("%Y-%m")

                        # Update monthly data for averaging
                        monthly_data[month_year]['total_hours'] += lead_time_change_in_hrs
                        monthly_data[month_year]['count'] += 1
                    else:
                        month_year = 'Not Merged'

                    # Add a placeholder for average time initially
                    writer.writerow({
                        'pr_number': pr.get('number'),
                        'pr_title': pr.get('title'),
                        'pr_created_date': created_date,
                        'pr_created_time': created_time,
                        'released_date': released_date,
                        'released_time': released_time,
                        'lead_time_change_in_days': lead_time_change_in_days,
                        'lead_time_change_in_hrs': lead_time_change_in_hrs,
                        'month_year': month_year,
                        'avg_lead_time_change_in_hrs': ''
                    })

            # Reopen the file to add average lead times
            with open('pr_details.csv', 'r') as csvfile:
                rows = list(csv.DictReader(csvfile))
            
            # Calculate the average lead time for each month
            for row in rows:
                month_year = row['month_year']
                if month_year != 'Not Merged' and monthly_data[month_year]['count'] > 0:
                    avg_hours = monthly_data[month_year]['total_hours'] / monthly_data[month_year]['count']
                    row['avg_lead_time_change_in_hrs'] = round(avg_hours, 2)

            # Write the updated data back to the CSV
            with open('pr_details.csv', 'w', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)

            print("PR details saved to pr_details.csv")
        else:
            print(f"Failed to fetch PRs. Status code: {response.status_code}")
            print(response.json())
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    get_pr_details()

#####################################
#Create new leadtimechangefile from using previos file

import csv
from collections import defaultdict

def create_leadtimechange_csv():
    try:
        # Dictionary to store total hours and count for each month-year
        monthly_data = defaultdict(lambda: {'total_hours': 0, 'count': 0})
        
        # Read data from pr_details.csv
        with open('pr_details.csv', 'r') as pr_file:
            reader = csv.DictReader(pr_file)

            # Iterate through each row to sum up the total hours for each month-year
            for row in reader:
                month_year = row['month_year']
                lead_time_in_hrs = row['lead_time_change_in_hrs']

                # Skip rows where lead_time_in_hrs is empty
                if lead_time_in_hrs and month_year != 'Not Merged':
                    monthly_data[month_year]['total_hours'] += float(lead_time_in_hrs)
                    monthly_data[month_year]['count'] += 1

        # Prepare data for leadtimechange.csv
        leadtimechange_data = []
        for month_year, data in monthly_data.items():
            if data['count'] > 0:
                avg_hours = data['total_hours'] / data['count']
                leadtimechange_data.append({'month_year': month_year, 'avg_lead_time_change_in_hrs': round(avg_hours, 2)})

        # Write to leadtimechange.csv
        with open('leadtimechange.csv', 'w', newline='') as csvfile:
            fieldnames = ['month_year', 'avg_lead_time_change_in_hrs']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            # Write the rows
            writer.writerows(leadtimechange_data)

        print("Lead time change details saved to leadtimechange.csv")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    create_leadtimechange_csv()

########################
#Graph for LT for change
import csv
import matplotlib.pyplot as plt

# Read Lead Time for Change data from CSV file
def read_lead_time_data():
    """Read the lead time data from the CSV file."""
    months = []
    avg_lead_time_values = []

    # Read the lead time change data file
    with open('leadtimechange.csv', 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            months.append(row['month_year'])
            avg_lead_time_values.append(float(row['avg_lead_time_change_in_hrs']))

    return months, avg_lead_time_values

# Plot the Lead Time for Change graph
def plot_lead_time_graph(months, avg_lead_time_values, filename="lead_time_graph.png"):
    """Plot the Lead Time for Change graph and save it as a PNG file."""
    plt.figure(figsize=(10, 6))
    plt.bar(months, avg_lead_time_values, color='salmon')
    plt.xlabel('Month')
    plt.ylabel('Average Lead Time for Change (Hours)')
    plt.title('Lead Time for Change by Month')
    plt.xticks(rotation=45)
    plt.tight_layout()

    # Save the graph as a PNG file
    plt.savefig(filename)
    print(f"Lead Time for Change graph saved as {filename}")

if __name__ == "__main__":
    # Read Lead Time data
    months, avg_lead_time_values = read_lead_time_data()

    # Plot the Lead Time graph and save it as an image
    plot_lead_time_graph(months, avg_lead_time_values)

##############################
#mttr.py

import requests
import csv
from datetime import datetime
from collections import defaultdict

# Replace with your GitHub personal access token
# GITHUB_TOKEN = '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'
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

# Read MTTR data from CSV file
def read_mttr_data():
    """Read the unique MTTR data from the CSV file."""
    months = []
    avg_mttr_values = []

    # Read the unique MTTR data file
    with open('unique_avg_mttr.csv', 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            months.append(row['issue_closed_month'])
            avg_mttr_values.append(float(row['avg_mttr_data']))

    return months, avg_mttr_values

# Plot the MTTR graph
def plot_mttr_graph(months, avg_mttr_values, filename="mttr_graph.png"):
    """Plot the MTTR (Mean Time to Restore) graph and save it as a PNG file."""
    plt.figure(figsize=(10, 6))
    plt.bar(months, avg_mttr_values, color='skyblue')
    plt.xlabel('Month')
    plt.ylabel('Average MTTR (Hours)')
    plt.title('Mean Time to Restore (MTTR) by Month')
    plt.xticks(rotation=45)
    plt.tight_layout()

    # Save the graph as a PNG file
    plt.savefig(filename)
    print(f"MTTR graph saved as {filename}")

if __name__ == "__main__":
    # Read MTTR data
    months, avg_mttr_values = read_mttr_data()

    # Plot the MTTR graph and save it as an image
    plot_mttr_graph(months, avg_mttr_values)

####################
##Combining all 4 graph and deleting seperate csv files and png files

import os
from PIL import Image

# List of image file names
image_files = [
    "deployment_frequency_graph.png",
    "cfr_graph_bar.png",
    "lead_time_graph.png",
    "mttr_graph.png"
]

# List of CSV files to remove
csv_files = [
    "closed_issues_mttr_outage.csv",
    "depfreq.csv",
    "leadtimechange.csv",
    "pr_details.csv",
    "release_incidents.csv",
    "releases_summary.csv",
    "unique_avg_mttr.csv",
    "unique_incident_month_cfr.csv"
]

def combine_images(image_files, output_filename="combined_graph.png"):
    try:
        # Open the images
        images = [Image.open(img) for img in image_files]
        
        # Get the maximum width and total height for the combined image
        max_width = max(img.width for img in images)
        total_height = sum(img.height for img in images)

        # Create a new blank image with the calculated dimensions
        combined_image = Image.new("RGB", (max_width, total_height))

        # Paste each image into the combined image
        current_height = 0
        for img in images:
            combined_image.paste(img, (0, current_height))
            current_height += img.height

        # Save the combined image
        combined_image.save(output_filename)
        print(f"Combined image saved as {output_filename}")

        # Delete the original image files
        for img in image_files:
            if os.path.exists(img):
                os.remove(img)
                print(f"Deleted {img}")
            else:
                print(f"{img} not found!")

        # Delete the specified CSV files
        for csv_file in csv_files:
            if os.path.exists(csv_file):
                os.remove(csv_file)
                print(f"Deleted {csv_file}")
            else:
                print(f"{csv_file} not found!")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    combine_images(image_files)
