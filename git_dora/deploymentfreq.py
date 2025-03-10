import requests
import csv
from datetime import datetime
from collections import defaultdict
from config import GITHUB_TOKEN

# Replace with your GitHub personal access token
#GITHUB_TOKEN = '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'
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
