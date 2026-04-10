import React, { useMemo, useState } from "react";
import { GitBranch, Loader2, Search } from "lucide-react";

import { addRepo, discoverRepos, startRun } from "../api";

const TECH_TAGS = ["GitHub API", "PyDriller", "Radon", "LangChain"];
const PROVIDERS = [
  { value: "github", label: "GitHub" },
  { value: "gitlab", label: "GitLab" },
];
const SCOPES = [
  { value: "specific", label: "Specific repository" },
  { value: "all", label: "All or selected repositories" },
];

export default function Connect({ onStarted }) {
  const [provider, setProvider] = useState("github");
  const [scope, setScope] = useState("specific");
  const [url, setUrl] = useState("");
  const [profileUrl, setProfileUrl] = useState("");
  const [token, setToken] = useState("");
  const [repoOptions, setRepoOptions] = useState([]);
  const [selectedUrls, setSelectedUrls] = useState([]);
  const [discovering, setDiscovering] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const selectedCount = selectedUrls.length;
  const canAnalyze =
    !loading && ((scope === "specific" && Boolean(url.trim())) || (scope === "all" && selectedCount > 0));

  const selectedReposPreview = useMemo(
    () => repoOptions.filter((repo) => selectedUrls.includes(repo.url)).slice(0, 3),
    [repoOptions, selectedUrls],
  );

  const handleScopeChange = (nextScope) => {
    setScope(nextScope);
    setError("");
  };

  const loadRepos = async () => {
    setDiscovering(true);
    setError("");
    try {
      const res = await discoverRepos({
        provider,
        profile_url: profileUrl.trim() || undefined,
        token: token.trim() || undefined,
      });
      const repos = res.data?.repos || [];
      setRepoOptions(repos);
      setSelectedUrls(repos.map((item) => item.url));
      if (repos.length === 0) {
        setError("No repositories found. Try a different profile or provide a valid access token.");
      }
    } catch (err) {
      setRepoOptions([]);
      setSelectedUrls([]);
      setError(err?.response?.data?.detail || "Failed to discover repositories");
    } finally {
      setDiscovering(false);
    }
  };

  const toggleRepo = (repoUrl) => {
    setSelectedUrls((current) =>
      current.includes(repoUrl) ? current.filter((value) => value !== repoUrl) : [...current, repoUrl],
    );
  };

  const submit = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      if (scope === "specific") {
        const repo = await addRepo(url, token || undefined);
        const run = await startRun(repo.data.id);
        onStarted({
          jobs: [
            {
              repoId: repo.data.id,
              repoName: repo.data.name,
              repoUrl: repo.data.url,
              runId: run.data.run_id,
            },
          ],
          activeRunId: run.data.run_id,
        });
      } else {
        if (selectedUrls.length === 0) {
          throw new Error("Choose at least one repository");
        }

        const jobs = [];
        for (const repoUrl of selectedUrls) {
          const repo = await addRepo(repoUrl, token || undefined);
          const run = await startRun(repo.data.id);
          jobs.push({
            repoId: repo.data.id,
            repoName: repo.data.name,
            repoUrl: repo.data.url,
            runId: run.data.run_id,
          });
        }

        onStarted({
          jobs,
          activeRunId: jobs[0]?.runId || "",
        });
      }
    } catch (err) {
      setError(err?.response?.data?.detail || err?.message || "Failed to start analysis");
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="connect-layout reveal-1">
      <div className="panel intro-panel">
        <h2 className="intro-title">Predictive Engineering Intelligence Platform</h2>
        <p className="intro-copy">
          Build a multi-agent AI system that connects to a GitHub or GitLab repository, analyzes code change history,
          bug patterns, and test coverage trends, and predicts which components are most likely to cause a failure in
          the next 90 days.
        </p>
        <div className="intro-tags">
          {TECH_TAGS.map((tag) => (
            <span key={tag} className="intro-tag">
              {tag}
            </span>
          ))}
        </div>
      </div>

      <div className="panel connect-panel">
        <div className="panel-header">
          <h3>Start Repository Analysis</h3>
          <p>Connect with a token, select specific or all repositories, and launch a full PEIP risk scan.</p>
        </div>
        <form onSubmit={submit} className="form-grid">
          <div className="control-grid">
            <label>
              Provider
              <select value={provider} onChange={(event) => setProvider(event.target.value)}>
                {PROVIDERS.map((item) => (
                  <option key={item.value} value={item.value}>
                    {item.label}
                  </option>
                ))}
              </select>
            </label>
          </div>

          <div className="scope-picker">
            {SCOPES.map((item) => (
              <label key={item.value} className="choice-card">
                <input
                  type="radio"
                  name="scope"
                  value={item.value}
                  checked={scope === item.value}
                  onChange={() => handleScopeChange(item.value)}
                />
                <span>{item.label}</span>
              </label>
            ))}
          </div>

          {scope === "specific" && (
            <label>
              Repository URL
              <input
                type="url"
                required
                placeholder="https://github.com/org/repo.git"
                value={url}
                onChange={(event) => setUrl(event.target.value)}
              />
            </label>
          )}

          {scope === "all" && (
            <>
              <label>
                Profile URL or owner name (optional)
                <input
                  type="text"
                  placeholder={provider === "github" ? "https://github.com/your-user" : "https://gitlab.com/your-user"}
                  value={profileUrl}
                  onChange={(event) => setProfileUrl(event.target.value)}
                />
              </label>
              <button type="button" className="btn ghost" onClick={loadRepos} disabled={discovering}>
                {discovering ? <Loader2 className="spin" size={16} /> : <Search size={16} />}
                {discovering ? "Loading repositories..." : "Load Repositories"}
              </button>

              {repoOptions.length > 0 && (
                <div className="repo-picker">
                  <div className="repo-picker-head">
                    <p>
                      Selected {selectedCount} of {repoOptions.length}
                    </p>
                    <div className="repo-picker-actions">
                      <button type="button" className="text-btn" onClick={() => setSelectedUrls(repoOptions.map((repo) => repo.url))}>
                        Select all
                      </button>
                      <button type="button" className="text-btn" onClick={() => setSelectedUrls([])}>
                        Clear
                      </button>
                    </div>
                  </div>
                  <div className="repo-list">
                    {repoOptions.map((repo) => (
                      <label key={repo.url} className="repo-item">
                        <input
                          type="checkbox"
                          checked={selectedUrls.includes(repo.url)}
                          onChange={() => toggleRepo(repo.url)}
                        />
                        <span>
                          {repo.full_name}
                          {repo.private ? " (private)" : ""}
                        </span>
                      </label>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}

          <label>
            {provider === "gitlab" ? "GitLab" : "GitHub"} Token (optional)
            <input
              type="password"
              placeholder={provider === "gitlab" ? "glpat-..." : "ghp_..."}
              value={token}
              onChange={(event) => setToken(event.target.value)}
            />
          </label>
          {scope === "all" && selectedReposPreview.length > 0 && (
            <p className="helper-text">
              Ready to scan: {selectedReposPreview.map((repo) => repo.full_name).join(", ")}
              {selectedCount > selectedReposPreview.length ? ` +${selectedCount - selectedReposPreview.length} more` : ""}
            </p>
          )}
          <button type="submit" className="btn" disabled={!canAnalyze}>
            {loading ? <Loader2 className="spin" size={16} /> : <GitBranch size={16} />}
            {loading
              ? "Starting..."
              : scope === "specific"
                ? "Analyze Repository"
                : `Analyze ${selectedCount} Selected Repositories`}
          </button>
        </form>
        {error && <p className="error">{error}</p>}
      </div>
    </section>
  );
}
