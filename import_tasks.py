import csv
import subprocess
import time

# --- CONFIGURATION ---
# Replace this with your actual repository name
REPO = "ywateba/chesspunk" 
CSV_FILE = "chesstask.csv"
# ---------------------

def create_issue(title, body, labels, priority, status, due_date):
    """
    Creates an issue mapping 'Priority' and 'Status' to GitHub Labels,
    and 'Due Date' to the issue body.
    """
    
    # 1. format the Body to include the Due Date
    # We add a horizontal rule (---) to separate the description from metadata
    full_body = (
        f"{body}\n\n"
        f"---\n"
        f"📅 **Due Date:** {due_date}\n"
    )
    
    # 2. Construct the list of Labels
    # We split the original CSV labels by comma, then add our new metadata labels
    label_list = [l.strip() for l in labels.split(",") if l.strip()]
    
    # Add Priority as a label (e.g., "P0")
    if priority:
        label_list.append(f"{priority}")
        
    # Add Status as a label (optional, e.g., "Status: Todo")
    # Note: GitHub Projects usually handle status via columns, but a label helps filtering
    if status:
        label_list.append(f"Status: {status}")

    # 3. Build the CLI command
    cmd = [
        "gh", "issue", "create",
        "--repo", REPO,
        "--title", title,
        "--body", body
    ]
    
    # Append each label as a separate flag
    # for label in label_list:
    #     cmd.extend(["--label", label])

    # 4. Execute
    try:
        result = subprocess.run(cmd, check=True, text=True, capture_output=True)
        print(f"✅ Created: {title}")
        print(f"   Labels: {label_list}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create: {title}")
        print(f"   Error: {e.stderr}")

def main():
    print(f"🚀 Starting import to {REPO}...")
    
    try:
        with open(CSV_FILE, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                create_issue(
                    title=row["Title"],
                    body=row["Body"],
                    labels=row["Labels"],
                    priority=row["Priority"],
                    status=row["Status"],
                    due_date=row["DueDate"]
                )
                time.sleep(1) # Prevent rate-limiting
                
    except FileNotFoundError:
        print(f"❌ Error: Could not find {CSV_FILE}. Make sure it is in the same folder.")

if __name__ == "__main__":
    main()