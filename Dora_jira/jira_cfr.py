import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime, timedelta
from collections import defaultdict
import csv
import matplotlib.pyplot as plt
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
        root.tk.call('tk', 'scaling', 1.)  # Adjust this scaling factor if necessary
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

auth = HTTPBasicAuth(USERNAME, PASSWORD)

# Fetch issues from Jira with changelog
def fetch_issues(jql):
    url = f"{JIRA_URL}/rest/api/2/search"
    params = {"jql": jql, "maxResults": MAX_RESULTS, "expand": "changelog"}
    response = requests.get(url, auth=auth, headers={"Content-Type": "application/json"}, params=params)

    if response.status_code == 200:
        return response.json().get("issues", [])
    else:
        print(f"Failed to fetch issues. Status code: {response.status_code}")
        print(f"Response: {response.text}")
        return []

# Analyze Transition History for CFR
def calculate_cfr_with_transitions():
    jql = f'project = {project_key} AND issuetype = "Task" AND updated >= "{start_date_time}" AND updated <= "{end_date_time}"'
    issues = fetch_issues(jql)

    deployed_count = 0
    reopened_count = 0
    cfr_details = []

    for issue in issues:
        transitions = issue.get("changelog", {}).get("histories", [])
        first_deploy = None
        reopen_after_deploy = False

        for entry in transitions:
            for item in entry.get("items", []):
                if item["field"] == "status":
                    from_status = item["fromString"]
                    to_status = item["toString"]

                    # Detect the first deployment
                    if to_status == "Deploy" and not first_deploy:
                        first_deploy = datetime.strptime(entry["created"], "%Y-%m-%dT%H:%M:%S.%f%z")
                        deployed_count += 1

                    # Check if "Reopen" occurs after the first deploy
                    if to_status == "Reopen" and first_deploy:
                        reopen_time = datetime.strptime(entry["created"], "%Y-%m-%dT%H:%M:%S.%f%z")
                        if reopen_time > first_deploy:
                            reopen_after_deploy = True
                            reopened_count += 1
                            cfr_details.append({
                                "issue_key": issue["key"],
                                "first_deploy_time": first_deploy.strftime("%Y-%m-%d %H:%M:%S"),
                                "reopen_time": reopen_time.strftime("%Y-%m-%d %H:%M:%S"),
                            })

    # Calculate CFR
    total_attempts = deployed_count
    cfr = reopened_count / total_attempts if total_attempts > 0 else 0

    # Write detailed CFR data to CSV
    with open("cfr_details.csv", "w", newline="") as csvfile:
        fieldnames = ["issue_key", "first_deploy_time", "reopen_time"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for detail in cfr_details:
            writer.writerow(detail)

    # Write aggregated data to CSV
    with open("cfr_aggregated.csv", "w", newline="") as csvfile:
        fieldnames = ["total_deployments", "total_reopens", "change_failure_rate"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow({
            "total_deployments": deployed_count,
            "total_reopens": reopened_count,
            "change_failure_rate": round(cfr * 100, 2),
        })

    print(f"Change Failure Rate: {round(cfr * 100, 2)}%")
    print("Details saved to cfr_details.csv and cfr_aggregated.csv")



def plot_combined_change_failure_metrics():
    with open("cfr_aggregated.csv", newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        data = next(reader)

    total_deployments = int(data["total_deployments"])
    total_reopens = int(data["total_reopens"])
    cfr = float(data["change_failure_rate"])

    # Determine performance category based on CFR
    if cfr <= 10:
        performance_flag = "Elite"
    elif 11 <= cfr <= 20:
        performance_flag = "High"
    elif 21 <= cfr <= 35:
        performance_flag = "Medium"
    else:
        performance_flag = "Low"

    # Plotting
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(6, 3))  # Adjusted figure size for better spacing
    fig.suptitle("Change Failure Rate Analysis", fontsize=9)

    # First bar chart: Deployments vs Reopens
    bar_width = 0.4  # Reduced bar width
    ax1.bar(["Deployments", "Reopens"], [total_deployments, total_reopens], color=["blue", "red"], width=bar_width)
    ax1.set_title("Deployments vs Reopens", fontsize=8)
    ax1.set_ylabel("Count", fontsize=6)
    ax1.tick_params(axis='x', labelsize=6)
    ax1.tick_params(axis='y', labelsize=6)

    # Second bar chart: CFR
    bar_width = 0.4
    ax2.bar(["Change Failure Rate (%)"], [cfr], color="purple", width=bar_width)
    ax2.set_title("CFR", fontsize=8)
    ax2.set_ylabel("Percentage", fontsize=6)
    ax2.set_ylim(0, 100)
    ax2.set_yticks(range(0, 101, 5))  # Add percentage ticks in 5% intervals
    ax2.tick_params(axis='x', labelsize=6)
    ax2.tick_params(axis='y', labelsize=6)

    # Add the performance category as a text annotation
    ax2.text(0, cfr + 2, f"{performance_flag}", fontsize=8, color="darkgreen", ha="center", va="bottom")

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.show()


# Main execution
if __name__ == "__main__":   
    # Calculate CFR and plot results
    calculate_cfr_with_transitions()
    plot_combined_change_failure_metrics()
