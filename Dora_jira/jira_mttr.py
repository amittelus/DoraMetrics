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
#jql_query = f'project={project_key} AND created >= "{start_date_time}" AND created <= "{end_date_time}"'

jql_query = (
    f'project={project_key} AND '
    f'issuetype="issue" AND '
    f'summary ~ "outage" AND '
    f'created >= "{start_date_time}" AND '
    f'created <= "{end_date_time}"'
)

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


def calculate_mttr():
    # JQL to fetch issues of type 'Issue' that transitioned to 'Done' within the specified date range
    jql_issue_done = (
        f'project = {project_key} AND '
        f'issuetype = "issue" AND '
        f'status = Done AND '
        f'updated >= "{start_date_time}" AND '
        f'updated <= "{end_date_time}"'
    )

    issues = get_issues(jql_issue_done, expand='changelog')

    mttr_details = []

    # Loop through each issue to calculate the time between creation and the Done transition
    for issue in issues:
        created_time = issue['fields']['created']  # Time when the issue was created
        done_time = None

        # Find the time when the issue transitioned to 'Done'
        for history in issue['changelog']['histories']:
            for item in history['items']:
                if item['field'] == 'status' and item['toString'] == 'Done':
                    done_time = history['created']
                    break
            if done_time:
                break

        if created_time and done_time:
            # Calculate the time difference
            created_dt = datetime.strptime(created_time, "%Y-%m-%dT%H:%M:%S.%f%z")
            done_dt = datetime.strptime(done_time, "%Y-%m-%dT%H:%M:%S.%f%z")

            recovery_time_delta = done_dt - created_dt
            days = recovery_time_delta.days
            hours, remainder = divmod(recovery_time_delta.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)

            mttr_details.append({
                'issue_key': issue['key'],
                'created_time': created_time,
                'done_time': done_time,
                'recovery_time_days': days,
                'recovery_time_hours': hours,
                'recovery_time_minutes': minutes,
                'recovery_time_seconds': seconds
            })

    # Calculate the average MTTR (Mean Time to Recover)
    if mttr_details:
        total_recovery_time_seconds = sum((
            (datetime.strptime(item['done_time'], "%Y-%m-%dT%H:%M:%S.%f%z") -
             datetime.strptime(item['created_time'], "%Y-%m-%dT%H:%M:%S.%f%z")).total_seconds()
            for item in mttr_details
        ))

        avg_mttr_seconds = total_recovery_time_seconds / len(mttr_details)
        avg_mttr_days = avg_mttr_seconds / 86400  # Convert seconds to days
    else:
        avg_mttr_days = 0

    # Write detailed MTTR data to mttr_details.csv
    with open('mttr_details.csv', 'w', newline='') as csvfile:
        fieldnames = ['issue_key', 'created_time', 'done_time', 'recovery_time_days', 'recovery_time_hours', 'recovery_time_minutes', 'recovery_time_seconds']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(mttr_details)

    # Write aggregated MTTR data to mttr_aggregated.csv
    with open('mttr_aggregated.csv', 'w', newline='') as csvfile:
        fieldnames = ['average_mttr_days']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow({'average_mttr_days': avg_mttr_days})

    print("MTTR details saved to mttr_details.csv and mttr_aggregated.csv")


# def plot_mttr_graph():
#     issue_keys = []
#     recovery_times_days = []

#     # Read data from mttr_details.csv
#     with open('mttr_details.csv', 'r') as csvfile:
#         reader = csv.DictReader(csvfile)

#         for row in reader:
#             # Calculate total recovery time in days for each issue
#             total_days = (
#                 int(row['recovery_time_days']) +
#                 int(row['recovery_time_hours']) / 24 +
#                 int(row['recovery_time_minutes']) / 1440 +
#                 int(row['recovery_time_seconds']) / 86400
#             )
#             issue_keys.append(row['issue_key'])
#             recovery_times_days.append(total_days)

#     # Calculate the average MTTR in days
#     avg_mttr_days = sum(recovery_times_days) / len(recovery_times_days) if recovery_times_days else 0

#     # Plotting the MTTR for each issue
#     plt.figure(figsize=(8, 6))
#     plt.plot(issue_keys, recovery_times_days, marker='o', color='b', label='MTTR per Issue')
#     plt.axhline(y=avg_mttr_days, color='r', linestyle='--', label=f'Average MTTR ({avg_mttr_days:.2f} days)')

#     # Graph labels and title
#     plt.xlabel('Issue Key')
#     plt.ylabel('MTTR in Days')
#     plt.title('Mean Time to Recovery (MTTR) per Issue')
#     plt.xticks(rotation=45, ha='right')
#     plt.legend()
#     plt.tight_layout()

#     # Display the plot
#     plt.show()

def plot_mttr_graph():
    issue_keys = []
    recovery_times_hours = []
    categories = []

    # Read data from mttr_details.csv
    with open('mttr_details.csv', 'r') as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            # Calculate total recovery time in hours for each issue
            total_hours = (
                int(row['recovery_time_days']) * 24 +
                int(row['recovery_time_hours']) +
                int(row['recovery_time_minutes']) / 60 +
                int(row['recovery_time_seconds']) / 3600
            )
            issue_keys.append(row['issue_key'])
            recovery_times_hours.append(total_hours)

            # Determine category based on total hours
            if total_hours < 1:  # Less than 1 hour
                categories.append('elite')
            elif total_hours < 24:  # Less than 1 day
                categories.append('high')
            elif total_hours < 168:  # Less than 1 week
                categories.append('medium')
            elif total_hours <= 720:  # Between 1 week and 1 month
                categories.append('low')

    # Calculate the average MTTR in hours
    avg_mttr_hours = sum(recovery_times_hours) / len(recovery_times_hours) if recovery_times_hours else 0

    # Plotting the MTTR for each issue
    plt.figure(figsize=(5, 3))
    colors = {'elite': 'gold', 'high': 'limegreen', 'medium': 'dodgerblue', 'low': 'darkorange'}
    bar_colors = [colors[cat] for cat in categories]

    plt.bar(issue_keys, recovery_times_hours, color=bar_colors)

    # Add vertical category labels
    for i, (key, cat) in enumerate(zip(issue_keys, categories)):
        plt.text(i, recovery_times_hours[i] + 0.5, cat, rotation=45, ha='center', fontsize=6, color='black')

    # Plot average line
    plt.axhline(y=avg_mttr_hours, color='red', linestyle='--', label=f'Avg MTTR ({avg_mttr_hours:.2f} hours)')

    # Adjust text size for axes
    plt.xticks(fontsize=6, rotation=45, ha='right')
    plt.yticks(fontsize=6)

    # Labels and title
    plt.xlabel('Issue Key', fontsize=6)
    plt.ylabel('MTTR (Hours)', fontsize=6)
    plt.title('Mean Time to Recovery (MTTR) per Issue', fontsize=9)
    plt.legend()

    # Ensure everything fits well
    plt.tight_layout()

    # Display the plot
    plt.show()



# Main execution
if __name__ == "__main__":
    calculate_mttr()
    plot_mttr_graph()
