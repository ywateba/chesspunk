#!/bin/bash

# 1. Update these variables!
REPO="ywateba/chesspunk" 

# 2. Loop through the CSV (skipping the header)
tail -n +2 chesstask.csv | while IFS=, read -r title body status priority due_date labels
do
  # Remove quotes from the CSV fields
  title=$(echo $title | tr -d '"')
  body=$(echo $body | tr -d '"')
  labels=$(echo $labels | tr -d '"')

  echo "Creating issue: $title"
  
  # Create the issue on GitHub
  gh issue create --repo "$REPO" \
    --title "$title" \
    --body "$body" \
    --label "$labels"
    
  # Note: This creates Issues, which you can then easily bulk-add to your Project Board.
done