import os
import json
from github import Github

def fetch_bug_patterns(repo_full_name, output_file, token=None):
    print(f"Fetching bug patterns for {repo_full_name}...")
    g = Github(token) if token else Github()
    
    try:
        repo = g.get_repo(repo_full_name)
        
        # Fetch closed bug issues
        issues = repo.get_issues(state='closed', labels=['bug'])
        bug_issues = []
        count = 0
        for issue in issues:
            if count >= 20: break
            bug_issues.append({
                'title': issue.title,
                'body': issue.body,
                'closed_at': issue.closed_at.isoformat() if issue.closed_at else None
            })
            count += 1
            
        # Fetch closed PRs
        pulls = repo.get_pulls(state='closed')
        closed_pulls = []
        count = 0
        for pr in pulls:
            if count >= 20: break
            closed_pulls.append({
                'title': pr.title,
                'body': pr.body,
                'closed_at': pr.closed_at.isoformat() if pr.closed_at else None,
                'is_merged': pr.merged
            })
            count += 1
            
        result = {
            'bug_issues': bug_issues,
            'pull_requests': closed_pulls
        }
        
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"Saved bug patterns to {output_file}")
        
    except Exception as e:
        print(f"Error fetching data for {repo_full_name}: {e}")
        # Save empty structure if failed
        with open(output_file, 'w') as f:
            json.dump({'bug_issues': [], 'pull_requests': []}, f, indent=2)

if __name__ == "__main__":
    token = os.getenv("GITHUB_TOKEN")
    repos_dir = "repos"
    for repo_name in os.listdir(repos_dir):
        repo_path = os.path.join(repos_dir, repo_name)
        if os.path.isdir(repo_path):
            repo_full_name = f"chaitu-png/{repo_name}"
            output_file = os.path.join(repo_path, "bug_patterns.json")
            fetch_bug_patterns(repo_full_name, output_file, token)
