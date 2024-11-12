# DoraMetrics

Deployment Frequency → This is the total number of releases in any specific period of time. 

 ◾ Use Git tags to label all new releases. For example, follow a pattern like v1.2.3 to denote major, minor, and patch versions, so it's easy to track deployments. 

 ◾ Release from main/master branches should be captured.

 ◾ For any changing and merging of code always create a new PR , no code should be pushed to main/master branch without PR code review, for this protected branch rules should be implemented on main to prevent unreviewed changes from being merged directly.

Lead Time for Changes → This will capture the average time difference between pr creation date time and pr release date time in hrs. 

◾ Use GitHub’s auto-merge feature to merge PRs automatically after all checks pass. This eliminates the need for manual intervention once approvals and tests are complete, and will give a more accurate report via DORA. 

◾ Once the release is made, avoid deleting or re-tagging old releases, this will ensure that old data will be captured as it is for analysis.

◾ Ensure that all branches are up-to-date with main, so PRs can merge quickly without conflicts.

Change Failure Rate  → This will give the percentage value of rate of total number of deployment by total number of Incidents occurred for any specific month.  


Mean time to resolve → This is the average time difference between Issue created date time and issue closed date time in hrs. 

◾ For any deployment failure user would need to create a issue, label the issue with name bug/hotfix/outage then only DORA will be able to capture these values. 

◾ Create some notification channel to get notified for all deployment failure 