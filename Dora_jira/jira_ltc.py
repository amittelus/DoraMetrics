import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime, timedelta
from collections import defaultdict
import csv
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import ttk, messagebox


import tkinter as tk
from tkinter import ttk, messagebox

def get_inputs():
    inputs = {"project_key": None, "start_date": None, "end_date": None}

    def on_submit():
        inputs["project_key"] = project_key_var.get()
        inputs["start_date"] = start_date_var.get()
        inputs["end_date"] = end_date_var.get()

        if not all(inputs.values()):
            messagebox.showerror("Error", "All fields are required!")
            root.destroy()
            exit()
        root.destroy()

    root = tk.Tk()
    root.title("Lead time to Chnage Inputs")

    # Enable HD scaling for high-resolution displays
    try:
        root.tk.call('tk', 'scaling', 2.0)  # Adjust this scaling factor if necessary
    except Exception as e:
        print(f"Error enabling scaling: {e}")

    # Input variables
    project_key_var = tk.StringVar()
    start_date_var = tk.StringVar()
    end_date_var = tk.StringVar()

    # Labels and input fields
    tk.Label(root, text="Project Key (e.g., TIDP):").grid(row=0, column=0, sticky="w", padx=10, pady=5)
    tk.Entry(root, textvariable=project_key_var).grid(row=0, column=1, sticky="ew", padx=10, pady=5)

    tk.Label(root, text="Start Date (YYYY-MM-DD):").grid(row=1, column=0, sticky="w", padx=10, pady=5)
    tk.Entry(root, textvariable=start_date_var).grid(row=1, column=1, sticky="ew", padx=10, pady=5)

    tk.Label(root, text="End Date (YYYY-MM-DD):").grid(row=2, column=0, sticky="w", padx=10, pady=5)
    tk.Entry(root, textvariable=end_date_var).grid(row=2, column=1, sticky="ew", padx=10, pady=5)

    # Submit button
    tk.Button(root, text="Submit", command=on_submit).grid(row=4, column=0, columnspan=2, pady=10)

    root.mainloop()
    return inputs["project_key"], inputs["start_date"], inputs["end_date"]






# Unified Input
project_key, start_date, end_date = get_inputs()

# Jira instance details and credentials
JIRA_URL = ""
USERNAME = ""
PASSWORD = ""
MAX_RESULTS = 100

# Add time to the date: Start of the day (00:00) for the start date
start_date_time = f"{start_date} 00:00"
# End of the day (23:59) for the end date
end_date_time = f"{end_date} 23:59"

# Construct the JQL query to fetch issues from the project within the time window
jql_query = f'project={project_key} AND issuetype = "TASK" AND created >= "{start_date_time}" AND created <= "{end_date_time}"'

# The API URL to search for issues using JQL
url = f"{JIRA_URL}/rest/api/2/search"

# Parameters for the API request
params = {
    "jql": jql_query,
    "maxResults": MAX_RESULTS
}

auth = HTTPBasicAuth(USERNAME, PASSWORD)



def get_issues(jql, expand=None):
    # Prepare the params dictionary with the jql and optional expand parameter
    params = {'jql': jql}
    if expand:
        params['expand'] = expand

    response = requests.get(url, auth=auth, headers={"Content-Type": "application/json"}, params=params)

    if response.status_code == 200:
        return response.json().get('issues', [])
    else:
        print(f"Failed to fetch issues. Status code: {response.status_code}")
        print(f"Response: {response.text}")  # Print the response for any errors or clues
        return []

#### Lead Time for Changes (LT)

def get_done_transition_date(issue):
    for history in issue['changelog']['histories']:
        for item in history['items']:
            if item['field'] == 'status' and item['toString'] == 'Done':
                # Found the transition to "Done"
                return history['created']
    return None  # Return None if no "Done" transition is found


def calculate_lead_time_for_changes():
    jql_done = f'project = {project_key} AND issuetype = "TASK" AND status = Done AND updated >= "{start_date_time}" AND updated <= "{end_date_time}"'
    done_issues = get_issues(jql_done, expand='changelog')  # Fetch issues with changelog data

    lead_times = []
    for issue in done_issues:
        created_date = issue['fields']['created']
        done_date = get_done_transition_date(issue)

        if done_date:
            # Parse created and done dates
            created_date_dt = datetime.strptime(created_date, "%Y-%m-%dT%H:%M:%S.%f%z")
            done_date_dt = datetime.strptime(done_date, "%Y-%m-%dT%H:%M:%S.%f%z")

            # Calculate precise lead time as a timedelta
            lead_time_delta = done_date_dt - created_date_dt
            days = lead_time_delta.days
            hours, remainder = divmod(lead_time_delta.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)

            # Append details for each issue
            lead_times.append({
                'issue_key': issue['key'],
                'created_date': created_date,
                'done_date': done_date,
                'lead_time_days': days,
                'lead_time_hours': hours,
                'lead_time_minutes': minutes,
                'lead_time_seconds': seconds
            })

    # Calculate average lead time in seconds, then convert to days
    avg_lead_time_seconds = sum((
        (datetime.strptime(item['done_date'], "%Y-%m-%dT%H:%M:%S.%f%z") -
         datetime.strptime(item['created_date'], "%Y-%m-%dT%H:%M:%S.%f%z")).total_seconds()
        for item in lead_times
    )) / len(lead_times) if lead_times else 0
    avg_lead_time_days = avg_lead_time_seconds / 86400  # Convert seconds to days

    # Write lead time details to lt_details.csv
    with open('lt_details.csv', 'w', newline='') as csvfile:
        fieldnames = ['issue_key', 'created_date', 'done_date', 'lead_time_days', 'lead_time_hours', 'lead_time_minutes', 'lead_time_seconds']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(lead_times)

    # Write aggregated lead time data to lt_aggregated.csv
    with open('lt_aggregated.csv', 'w', newline='') as csvfile:
        fieldnames = ['average_lead_time_days']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow({'average_lead_time_days': avg_lead_time_days})

    print("Lead Time for Changes details saved to lt_details.csv and lt_aggregated.csv")



def plot_lead_time_graph():
    issue_keys = []
    lead_time_days = []

    # Read lead time data from lt_details.csv
    with open('lt_details.csv', 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            issue_key = row['issue_key']
            days = int(row['lead_time_days'])
            hours = int(row['lead_time_hours'])
            minutes = int(row['lead_time_minutes'])
            seconds = int(row['lead_time_seconds'])

            # Calculate the total lead time in seconds for each issue, then convert to days
            total_seconds = (days * 86400) + (hours * 3600) + (minutes * 60) + seconds
            total_days = total_seconds / 86400  # Convert seconds to days

            issue_keys.append(issue_key)  # Store issue key for x-axis
            lead_time_days.append(total_days)  # Store lead time in days for y-axis

    # Calculate the average lead time in days
    avg_lead_time = sum(lead_time_days) / len(lead_time_days) if lead_time_days else 0

    # Plot the lead time for each issue
    plt.figure(figsize=(8, 4))
    bars = plt.bar(issue_keys, lead_time_days, color='lightgreen', edgecolor='black', label="Lead Time per Issue")
    plt.axhline(y=avg_lead_time, color='red', linestyle='--', linewidth=1.5, label=f"Average Lead Time ({avg_lead_time:.2f} days)")

    # Add performance flags above bars
    for bar, lead_time in zip(bars, lead_time_days):
        category = ""
        if lead_time < 1:
            category = "Elite"
        elif 1 <= lead_time < 7:
            category = "High"
        elif 7 <= lead_time < 30:
            category = "Medium"
        else:
            category = "Low"

        plt.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.2,
            category,
            ha="center",
            va="bottom",
            fontsize=8,
            color="blue"
        )

    # Add title and labels
    plt.title("Lead Time for Changes per Issue", fontsize=10)
    plt.xlabel("Issue Key (TT Name)", fontsize=6)
    plt.ylabel("Lead Time (Days)", fontsize=6)
    plt.xticks(rotation=45, ha='right', fontsize=6)  # Reduced font size for x-axis
    plt.yticks(fontsize=6)  # Reduced font size for y-axis
    plt.legend()
    plt.tight_layout()

    # Display the plot
    plt.show()



# Main execution
if __name__ == "__main__":
    calculate_lead_time_for_changes()
    plot_lead_time_graph()

