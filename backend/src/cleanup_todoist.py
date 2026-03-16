from todoist_api_python.api import TodoistAPI
import os
from dotenv import load_dotenv

# Load your token from the .env file
load_dotenv()
token = os.getenv("TToken") # Ensure this matches your .env key

def delete_all_todoist_tasks(delete_everything=False):
    if not token:
        print("Error: Todoist token not found in .env")
        return

    api = TodoistAPI(token)
    try:
        tasks = api.get_tasks()
        print(f"Found {len(tasks)} tasks.")
        
        count = 0
        for task in tasks:
            # OPTION A: Delete only tasks with descriptions (Canvas assignments)
            if not delete_everything:
                if task.description and task.description.strip():
                    print(f"Deleting synced task: {task.content}")
                    api.delete_task(task_id=task.id)
                    count += 1
            
            # OPTION B: Delete every single task in the inbox/projects
            else:
                print(f"Deleting task: {task.content}")
                api.delete_task(task_id=task.id)
                count += 1
        
        print(f"\nFinished! Deleted {count} tasks.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Change to True if you want to wipe EVERY task in your Todoist
    delete_all_todoist_tasks(delete_everything=False)
