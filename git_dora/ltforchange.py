import requests
import csv
from datetime import datetime
from collections import defaultdict

# Replace with your GitHub personal access token
GITHUB_TOKEN = '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'
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
from datetime import datetime

# Load the data from leadtimechange.csv
months = []
avg_lead_time_hours = []

# Read the lead time change data
with open('leadtimechange.csv', 'r') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        # Convert month_year to a datetime object for better plotting
        month_year = datetime.strptime(row['month_year'], "%Y-%m")
        months.append(month_year)
        avg_lead_time_hours.append(float(row['avg_lead_time_change_in_hrs']))

# Plot the data
plt.figure(figsize=(10, 6))
plt.plot(months, avg_lead_time_hours, marker='o', color='r', linestyle='-', linewidth=2, markersize=6)

# Add labels and title
plt.xlabel("Month-Year")
plt.ylabel("Average Lead Time for Change (Hours)")
plt.title("Average Lead Time for Change Over Time")
plt.xticks(rotation=45)  # Rotate x-axis labels for better readability
plt.grid(True, which='both', linestyle='--', linewidth=0.5)

# Display the plot
plt.tight_layout()  # Adjust layout for better fit
plt.show()
