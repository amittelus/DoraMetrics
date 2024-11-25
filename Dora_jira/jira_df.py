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
    inputs = {"project_key": None, "start_date": None, "end_date": None, "frequency": None}

    def on_submit():
        inputs["project_key"] = project_key_var.get()
        inputs["start_date"] = start_date_var.get()
        inputs["end_date"] = end_date_var.get()
        inputs["frequency"] = frequency_var.get()

        if not all(inputs.values()):
            messagebox.showerror("Error", "All fields are required!")
            root.destroy()
            exit()
        root.destroy()

    root = tk.Tk()
    root.title("Deployment Frequency Inputs")

    # Enable HD scaling for high-resolution displays
    try:
        root.tk.call('tk', 'scaling', 2.0)  # Adjust this scaling factor if necessary
    except Exception as e:
        print(f"Error enabling scaling: {e}")

    # Input variables
    project_key_var = tk.StringVar()
    start_date_var = tk.StringVar()
    end_date_var = tk.StringVar()
    frequency_var = tk.StringVar()

    # Labels and input fields
    tk.Label(root, text="Project Key (e.g., TIDP):").grid(row=0, column=0, sticky="w", padx=10, pady=5)
    tk.Entry(root, textvariable=project_key_var).grid(row=0, column=1, sticky="ew", padx=10, pady=5)

    tk.Label(root, text="Start Date (YYYY-MM-DD):").grid(row=1, column=0, sticky="w", padx=10, pady=5)
    tk.Entry(root, textvariable=start_date_var).grid(row=1, column=1, sticky="ew", padx=10, pady=5)

    tk.Label(root, text="End Date (YYYY-MM-DD):").grid(row=2, column=0, sticky="w", padx=10, pady=5)
    tk.Entry(root, textvariable=end_date_var).grid(row=2, column=1, sticky="ew", padx=10, pady=5)

    tk.Label(root, text="Frequency:").grid(row=3, column=0, sticky="w", padx=10, pady=5)
    ttk.Combobox(root, textvariable=frequency_var, values=["Weekly", "Bi-Weekly", "Monthly"]).grid(row=3, column=1, sticky="ew", padx=10, pady=5)

    # Submit button
    tk.Button(root, text="Submit", command=on_submit).grid(row=4, column=0, columnspan=2, pady=10)

    root.mainloop()
    return inputs["project_key"], inputs["start_date"], inputs["end_date"], inputs["frequency"]






# Unified Input
project_key, start_date, end_date, frequency = get_inputs()

JIRA_URL = ""
USERNAME = ""
PASSWORD = ""
MAX_RESULTS = 100

# Prepare time window
start_date_time = f"{start_date} 00:00"
end_date_time = f"{end_date} 23:59"

# JQL query
jql_query = f'project={project_key} AND issuetype = "TASK" AND created >= "{start_date_time}" AND created <= "{end_date_time}"'
url = f"{JIRA_URL}/rest/api/2/search"
auth = HTTPBasicAuth(USERNAME, PASSWORD)


def get_issues(jql):
    response = requests.get(url, auth=auth, headers={"Content-Type": "application/json"}, params={"jql": jql})
    if response.status_code == 200:
        return response.json().get('issues', [])
    else:
        print(f"Failed to fetch issues. Status code: {response.status_code}")
        print(f"Response: {response.text}")
        return []


# def calculate_frequency_based_on_selection(frequency, start_date, end_date):
#     issues = get_issues(jql_query)
#     date_format = "%Y-%m-%d"
#     deployments = defaultdict(int)
#     release_details = []

#     for issue in issues:
#         deploy_date = issue['fields']['updated'].split('T')[0]
#         tag_name = issue['key']
#         release_details.append({"tag_name": tag_name, "deploy_date": deploy_date})

#     # Calculate frequency
#     if frequency == "Weekly":
#         period = 7
#     elif frequency == "Bi-Weekly":
#         period = 14
#     else:
#         period = 30  # Monthly approximation

#     start = datetime.strptime(start_date, date_format)
#     end = datetime.strptime(end_date, date_format)
#     delta = end - start
#     total_days = delta.days + 1

#     current_start = start
#     while current_start <= end:
#         next_period_end = current_start + timedelta(days=period - 1)
#         if next_period_end > end:
#             next_period_end = end
#         count = sum(1 for detail in release_details if current_start <= datetime.strptime(detail["deploy_date"], date_format) <= next_period_end)
#         deployments[current_start.strftime("%Y-%m-%d")] = count
#         current_start = next_period_end + timedelta(days=1)

#     # Save to CSV
#     with open('df_aggregated.csv', 'w', newline='') as csvfile:
#         writer = csv.writer(csvfile)
#         writer.writerow(["Start Date", "Deployments"])
#         for period_start, count in deployments.items():
#             writer.writerow([period_start, count])

#     print("Frequency details saved to df_aggregated.csv")
#     return deployments


# def plot_frequency(deployments):
#     # Plot Deployment Frequency
#     dates = list(deployments.keys())
#     counts = list(deployments.values())

#     plt.figure(figsize=(10, 6))
#     plt.bar(dates, counts, color='skyblue')
#     plt.xlabel("Start Date")
#     plt.ylabel("Number of Deployments")
#     plt.title(f"Deployment Frequency ({frequency})")
#     plt.xticks(rotation=45)
#     plt.tight_layout()
#     plt.show()


# # Main execution
# if __name__ == "__main__":
#     print(f"Calculating deployment frequency for {frequency}...")
#     deployments = calculate_frequency_based_on_selection(frequency, start_date, end_date)
#     print("Completed!")

#     print("Plotting deployment frequency...")
#     plot_frequency(deployments)
def calculate_frequency_based_on_selection(frequency, start_date, end_date):
    issues = get_issues(jql_query)
    date_format = "%Y-%m-%d"
    deployments = {}
    release_details = []

    for issue in issues:
        deploy_date = issue['fields']['updated'].split('T')[0]
        tag_name = issue['key']
        release_details.append({"tag_name": tag_name, "deploy_date": deploy_date})

    # Define period based on frequency
    if frequency == "Weekly":
        period = 7
    elif frequency == "Bi-Weekly":
        period = 14
    else:
        period = 30  # Monthly approximation

    start = datetime.strptime(start_date, date_format)
    end = datetime.strptime(end_date, date_format)
    current_start = start

    # Calculate deployments for each period
    while current_start <= end:
        next_period_end = current_start + timedelta(days=period - 1)
        if next_period_end > end:
            next_period_end = end
        period_range = f"{current_start.strftime('%Y-%m-%d')} to {next_period_end.strftime('%Y-%m-%d')}"
        count = sum(
            1 for detail in release_details if current_start <= datetime.strptime(detail["deploy_date"], date_format) <= next_period_end
        )
        deployments[period_range] = count
        current_start = next_period_end + timedelta(days=1)

    # Save to CSV
    with open('df_aggregated.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Time Period", "Deployments"])
        for period_range, count in deployments.items():
            writer.writerow([period_range, count])

    print("Frequency details saved to df_aggregated.csv")
    return deployments



def plot_frequency(deployments):
    # Prepare data for plotting
    periods = list(deployments.keys())  # E.g., ["2024-11-01 to 2024-11-07", ...]
    counts = list(deployments.values())

    # Define performance categories
    def categorize_deployments(count):
        if count > 30:  # Assuming multiple deploys per day
            return "Elite"
        elif 7 < count <= 30:  # Between once per day and once per week
            return "High"
        elif 1 < count <= 7:  # Between once per week and once per month
            return "Medium"
        else:  # Between once per month and every six months
            return "Low"

    categories = [categorize_deployments(count) for count in counts]

    # Set up plot
    plt.figure(figsize=(6, 4))
    bar_width = 0.5 # Width of the bars

    # Generate positions for bars (centered between edges)
    positions = range(len(periods))
    bars = plt.bar(positions, counts, color='skyblue', width=bar_width, align='center')

    # Add annotations for counts and performance categories
    for bar, count, category in zip(bars, counts, categories):
        # Display count on the bar
        plt.text(
            bar.get_x() + bar.get_width() / 2,  # Center of the bar
            bar.get_height() - 1.5,  # Slightly below the top of the bar
            str(count),
            ha="center",
            va="bottom",
            fontsize=9,
            color="white",
            weight="bold"
        )
        # Display category above the bar
        plt.text(
            bar.get_x() + bar.get_width() / 2,  # Center of the bar
            bar.get_height() + 0.2,  # Slightly above the bar
            category,
            ha="center",
            va="bottom",
            fontsize=9,
            color="blue"
        )

    # Prepare x-axis ticks
    ticks = [f"{period.split(' to ')[0]}\n{period.split(' to ')[1]}" for period in periods]
    plt.xticks(positions, ticks, rotation=45, ha='center', fontsize=5)  # Adjust x-axis text font size
    plt.yticks(fontsize=6)  # Adjust y-axis text font size

    # Add labels and title
    plt.xlabel("Time Period (Start to End Dates)", fontsize=6)  # Adjust label font size
    plt.ylabel("Number of Deployments", fontsize=6)  # Adjust label font size
    plt.title(f"Deployment Frequency ({frequency})", fontsize=9)  # Adjust title font size
    plt.tight_layout()
    plt.show()



# Main execution
if __name__ == "__main__":
    print(f"Calculating deployment frequency for {frequency}...")
    deployments = calculate_frequency_based_on_selection(frequency, start_date, end_date)
    print("Completed!")

    print("Plotting deployment frequency...")
    plot_frequency(deployments)
