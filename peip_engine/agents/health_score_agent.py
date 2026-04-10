import os
import json

def calculate_health_score(repo_dir):
    try:
        git_history_path = os.path.join(repo_dir, "git_history.json")
        complexity_path = os.path.join(repo_dir, "complexity.json")
        maintainability_path = os.path.join(repo_dir, "maintainability.json")
        bug_patterns_path = os.path.join(repo_dir, "bug_patterns.json")
        
        # Load data
        with open(git_history_path, 'r') as f: git_history = json.load(f)
        with open(complexity_path, 'r') as f: complexity = json.load(f)
        with open(maintainability_path, 'r') as f: maintainability = json.load(f)
        with open(bug_patterns_path, 'r') as f: bug_patterns = json.load(f)
        
        # Stability Score (0-100)
        # Based on average lines modified per commit
        if git_history:
            avg_lines = sum(c['lines'] for c in git_history) / len(git_history)
            stability = max(0, 100 - (avg_lines / 10))
        else:
            stability = 0
            
        # Complexity Score (0-100)
        # Average CC. Radon CC: 1-5 A, 6-10 B, etc.
        # We'll normalize CC. Average CC > 20 is bad.
        all_cc = []
        for file_data in complexity.values():
            if isinstance(file_data, list):
                for item in file_data:
                    if 'complexity' in item: all_cc.append(item['complexity'])
        
        avg_cc = sum(all_cc) / len(all_cc) if all_cc else 0
        complexity_score = max(0, 100 - (avg_cc * 4))
        
        # Maintainability Score (0-100)
        # Radon MI is already 0-100.
        all_mi = [v['mi'] for v in maintainability.values() if 'mi' in v]
        avg_mi = sum(all_mi) / len(all_mi) if all_mi else 50
        
        # Risk Score (0-100)
        # Based on bug issues and closed PRs
        num_bugs = len(bug_patterns.get('bug_issues', []))
        risk_score = max(0, 100 - (num_bugs * 10))
        
        # Aggregate Health Score
        final_score = (stability * 0.25) + (complexity_score * 0.25) + (avg_mi * 0.25) + (risk_score * 0.25)
        
        result = {
            'repo': os.path.basename(repo_dir),
            'scores': {
                'stability': round(stability, 2),
                'complexity': round(complexity_score, 2),
                'maintainability': round(avg_mi, 2),
                'risk': round(risk_score, 2)
            },
            'final_health_score': round(final_score, 2)
        }
        return result
        
    except Exception as e:
        print(f"Error calculating score for {repo_dir}: {e}")
        return None

if __name__ == "__main__":
    repos_dir = "repos"
    all_scores = []
    for repo_name in os.listdir(repos_dir):
        repo_path = os.path.join(repos_dir, repo_name)
        if os.path.isdir(repo_path):
            score = calculate_health_score(repo_path)
            if score:
                all_scores.append(score)
                # Also save individual score
                with open(os.path.join(repo_path, "health_score.json"), 'w') as f:
                    json.dump(score, f, indent=2)
                    
    # Save global health scores
    with open("health_scores.json", 'w') as f:
        json.dump(all_scores, f, indent=2)
    print(f"Saved global health scores to health_scores.json")
