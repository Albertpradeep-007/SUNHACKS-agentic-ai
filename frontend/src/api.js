import axios from "axios";

const BASE = import.meta.env.VITE_API_BASE || (import.meta.env.DEV ? "http://localhost:8000" : "/api");
const API_BASE = BASE.endsWith("/") ? BASE.slice(0, -1) : BASE;

export const addRepo = (url, token) => axios.post(`${API_BASE}/repos`, { url, token });
export const discoverRepos = ({ provider, profile_url, token }) =>
	axios.post(`${API_BASE}/repos/discover`, { provider, profile_url, token });
export const startRun = (repo_id) => axios.post(`${API_BASE}/analyze`, { repo_id });
export const getResults = (run_id) => axios.get(`${API_BASE}/results/${run_id}`);
export const getReportMarkdown = (run_id) => axios.get(`${API_BASE}/report/${run_id}/markdown`);
export const reportUrl = (run_id) => `${API_BASE}/report/${run_id}/pdf`;
export const reportHtmlUrl = (run_id) => `${API_BASE}/report/${run_id}/html`;
