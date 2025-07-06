#!/usr/bin/env python3
"""
Web Dashboard for Web Scraping Tool
Flask-based interface for monitoring and controlling scraping operations
"""

from flask import Flask, render_template, request, jsonify, send_file, flash, redirect, url_for
from flask_socketio import SocketIO, emit
import json
import os
import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import uuid
from dataclasses import dataclass, asdict
from enum import Enum

from main import WebScrapingTool
from data_output import DataOutput
from proxy_manager import ProxyManager
from api_integration import APIIntegration

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask app setup
app = Flask(__name__)
app.secret_key = 'web_scraping_tool_secret_key_2024'
socketio = SocketIO(app, cors_allowed_origins="*")

class JobStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class ScrapingJob:
    id: str
    query: str
    urls: List[str]
    extraction_level: str
    output_format: str
    status: JobStatus
    progress: float
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    results_count: int = 0
    error_message: Optional[str] = None
    output_file: Optional[str] = None

class WebDashboard:
    """Web dashboard controller"""
    
    def __init__(self):
        self.active_jobs: Dict[str, ScrapingJob] = {}
        self.completed_jobs: List[ScrapingJob] = []
        self.proxy_manager = ProxyManager()
        self.api_integration = APIIntegration()
        self.job_history = []
        self.system_stats = {
            'total_jobs': 0,
            'successful_jobs': 0,
            'failed_jobs': 0,
            'total_companies_scraped': 0,
            'uptime_start': datetime.now()
        }
        
        # Load job history
        self._load_job_history()
    
    def create_job(self, query: str = None, urls: List[str] = None, 
                   extraction_level: str = "basic", output_format: str = "json") -> str:
        """Create a new scraping job"""
        job_id = str(uuid.uuid4())
        
        job = ScrapingJob(
            id=job_id,
            query=query or "",
            urls=urls or [],
            extraction_level=extraction_level,
            output_format=output_format,
            status=JobStatus.PENDING,
            progress=0.0,
            created_at=datetime.now()
        )
        
        self.active_jobs[job_id] = job
        self.system_stats['total_jobs'] += 1
        
        logger.info(f"Created job {job_id}: {query or f'{len(urls)} URLs'}")
        return job_id
    
    def start_job(self, job_id: str):
        """Start a scraping job"""
        if job_id not in self.active_jobs:
            raise ValueError(f"Job {job_id} not found")
        
        job = self.active_jobs[job_id]
        job.status = JobStatus.RUNNING
        job.started_at = datetime.now()
        
        # Start job in background thread
        thread = threading.Thread(target=self._execute_job, args=(job_id,))
        thread.daemon = True
        thread.start()
        
        logger.info(f"Started job {job_id}")
    
    def _execute_job(self, job_id: str):
        """Execute a scraping job"""
        job = self.active_jobs[job_id]
        
        try:
            # Initialize scraping tool
            tool = WebScrapingTool(use_selenium=True, output_dir="dashboard_output")
            
            # Emit progress updates
            self._emit_job_progress(job_id, 10, "Initializing scraping tool...")
            
            if job.query:
                # Search-based scraping
                self._emit_job_progress(job_id, 20, "Discovering companies...")
                result = tool.scrape_from_query(
                    query=job.query,
                    max_results=20,
                    extraction_level=job.extraction_level,
                    output_format=job.output_format,
                    output_filename=f"job_{job_id}"
                )
            else:
                # URL-based scraping
                self._emit_job_progress(job_id, 20, "Starting URL scraping...")
                result = tool.scrape_from_urls(
                    urls=job.urls,
                    extraction_level=job.extraction_level,
                    output_format=job.output_format,
                    output_filename=f"job_{job_id}"
                )
            
            self._emit_job_progress(job_id, 90, "Finalizing results...")
            
            if result.get('success'):
                job.status = JobStatus.COMPLETED
                job.results_count = len(result.get('results', []))
                job.output_file = result.get('saved_file')
                self.system_stats['successful_jobs'] += 1
                self.system_stats['total_companies_scraped'] += job.results_count
                
                self._emit_job_progress(job_id, 100, "Job completed successfully!")
            else:
                job.status = JobStatus.FAILED
                job.error_message = result.get('error', 'Unknown error')
                self.system_stats['failed_jobs'] += 1
                
                self._emit_job_progress(job_id, 100, f"Job failed: {job.error_message}")
            
            tool.close()
            
        except Exception as e:
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            self.system_stats['failed_jobs'] += 1
            
            self._emit_job_progress(job_id, 100, f"Job failed: {str(e)}")
            logger.error(f"Job {job_id} failed: {e}")
        
        finally:
            job.completed_at = datetime.now()
            
            # Move to completed jobs
            if job_id in self.active_jobs:
                completed_job = self.active_jobs.pop(job_id)
                self.completed_jobs.append(completed_job)
                self.job_history.append(completed_job)
                
                # Keep only last 100 completed jobs
                if len(self.completed_jobs) > 100:
                    self.completed_jobs.pop(0)
                
                self._save_job_history()
    
    def _emit_job_progress(self, job_id: str, progress: float, message: str):
        """Emit job progress to connected clients"""
        if job_id in self.active_jobs:
            self.active_jobs[job_id].progress = progress
            
            socketio.emit('job_progress', {
                'job_id': job_id,
                'progress': progress,
                'message': message,
                'timestamp': datetime.now().isoformat()
            })
    
    def cancel_job(self, job_id: str):
        """Cancel a running job"""
        if job_id in self.active_jobs:
            job = self.active_jobs[job_id]
            if job.status == JobStatus.RUNNING:
                job.status = JobStatus.CANCELLED
                job.completed_at = datetime.now()
                logger.info(f"Cancelled job {job_id}")
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job status"""
        if job_id in self.active_jobs:
            job = self.active_jobs[job_id]
            return asdict(job)
        
        for job in self.completed_jobs:
            if job.id == job_id:
                return asdict(job)
        
        return None
    
    def get_all_jobs(self) -> Dict[str, Any]:
        """Get all jobs"""
        return {
            'active_jobs': [asdict(job) for job in self.active_jobs.values()],
            'completed_jobs': [asdict(job) for job in self.completed_jobs[-10:]]  # Last 10
        }
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics"""
        uptime = datetime.now() - self.system_stats['uptime_start']
        
        stats = self.system_stats.copy()
        stats['uptime_hours'] = uptime.total_seconds() / 3600
        stats['proxy_stats'] = self.proxy_manager.get_proxy_stats()
        stats['api_status'] = self.api_integration.get_api_status()
        
        return stats
    
    def _save_job_history(self):
        """Save job history to file"""
        try:
            history_data = []
            for job in self.job_history[-50:]:  # Save last 50 jobs
                job_dict = asdict(job)
                # Convert datetime objects to strings
                for key, value in job_dict.items():
                    if isinstance(value, datetime):
                        job_dict[key] = value.isoformat()
                    elif isinstance(value, JobStatus):
                        job_dict[key] = value.value
                history_data.append(job_dict)
            
            with open('job_history.json', 'w') as f:
                json.dump(history_data, f, indent=2)
        
        except Exception as e:
            logger.error(f"Error saving job history: {e}")
    
    def _load_job_history(self):
        """Load job history from file"""
        try:
            if os.path.exists('job_history.json'):
                with open('job_history.json', 'r') as f:
                    history_data = json.load(f)
                
                for job_dict in history_data:
                    # Convert string dates back to datetime
                    for key, value in job_dict.items():
                        if key.endswith('_at') and value:
                            job_dict[key] = datetime.fromisoformat(value)
                        elif key == 'status':
                            job_dict[key] = JobStatus(value)
                    
                    job = ScrapingJob(**job_dict)
                    self.job_history.append(job)
                    
                    if job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                        self.completed_jobs.append(job)
                
                logger.info(f"Loaded {len(self.job_history)} jobs from history")
        
        except Exception as e:
            logger.error(f"Error loading job history: {e}")

# Global dashboard instance
dashboard = WebDashboard()

# Routes
@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/api/jobs', methods=['GET'])
def get_jobs():
    """Get all jobs API"""
    return jsonify(dashboard.get_all_jobs())

@app.route('/api/jobs', methods=['POST'])
def create_job():
    """Create new job API"""
    data = request.get_json()
    
    query = data.get('query')
    urls = data.get('urls', [])
    extraction_level = data.get('extraction_level', 'basic')
    output_format = data.get('output_format', 'json')
    
    if not query and not urls:
        return jsonify({'error': 'Either query or URLs must be provided'}), 400
    
    job_id = dashboard.create_job(
        query=query,
        urls=urls,
        extraction_level=extraction_level,
        output_format=output_format
    )
    
    return jsonify({'job_id': job_id})

@app.route('/api/jobs/<job_id>/start', methods=['POST'])
def start_job(job_id):
    """Start job API"""
    try:
        dashboard.start_job(job_id)
        return jsonify({'status': 'started'})
    except ValueError as e:
        return jsonify({'error': str(e)}), 404

@app.route('/api/jobs/<job_id>/cancel', methods=['POST'])
def cancel_job(job_id):
    """Cancel job API"""
    dashboard.cancel_job(job_id)
    return jsonify({'status': 'cancelled'})

@app.route('/api/jobs/<job_id>', methods=['GET'])
def get_job_status(job_id):
    """Get job status API"""
    status = dashboard.get_job_status(job_id)
    if status:
        return jsonify(status)
    return jsonify({'error': 'Job not found'}), 404

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get system statistics API"""
    return jsonify(dashboard.get_system_stats())

@app.route('/api/download/<job_id>')
def download_results(job_id):
    """Download job results"""
    job_status = dashboard.get_job_status(job_id)
    if not job_status or not job_status.get('output_file'):
        return jsonify({'error': 'No results available'}), 404
    
    output_file = job_status['output_file']
    if os.path.exists(output_file):
        return send_file(output_file, as_attachment=True)
    
    return jsonify({'error': 'Results file not found'}), 404

@app.route('/api/proxy/test', methods=['POST'])
def test_proxies():
    """Test proxy connections"""
    try:
        results = dashboard.proxy_manager.test_all_proxies()
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/proxy/stats', methods=['GET'])
def get_proxy_stats():
    """Get proxy statistics"""
    return jsonify(dashboard.proxy_manager.get_proxy_stats())

# Socket.IO events
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    emit('connected', {'status': 'Connected to Web Scraping Dashboard'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info('Client disconnected')

@socketio.on('get_live_stats')
def handle_live_stats():
    """Send live statistics"""
    stats = dashboard.get_system_stats()
    emit('live_stats', stats)

# Template creation functions
def create_templates():
    """Create HTML templates for the dashboard"""
    
    # Create templates directory
    os.makedirs('templates', exist_ok=True)
    
    # Main template
    index_html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Web Scraping Tool Dashboard</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f5f5f5; }
        .header { background: #2c3e50; color: white; padding: 1rem; text-align: center; }
        .container { max-width: 1200px; margin: 0 auto; padding: 2rem; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 2rem; }
        .card { background: white; border-radius: 8px; padding: 1.5rem; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .card h2 { color: #2c3e50; margin-bottom: 1rem; border-bottom: 2px solid #3498db; padding-bottom: 0.5rem; }
        .form-group { margin-bottom: 1rem; }
        .form-group label { display: block; margin-bottom: 0.5rem; font-weight: bold; }
        .form-group input, .form-group select, .form-group textarea { width: 100%; padding: 0.75rem; border: 1px solid #ddd; border-radius: 4px; }
        .btn { background: #3498db; color: white; padding: 0.75rem 1.5rem; border: none; border-radius: 4px; cursor: pointer; }
        .btn:hover { background: #2980b9; }
        .btn-success { background: #27ae60; }
        .btn-danger { background: #e74c3c; }
        .btn-warning { background: #f39c12; }
        .status { padding: 0.25rem 0.75rem; border-radius: 20px; font-size: 0.8rem; font-weight: bold; }
        .status-pending { background: #f39c12; color: white; }
        .status-running { background: #3498db; color: white; }
        .status-completed { background: #27ae60; color: white; }
        .status-failed { background: #e74c3c; color: white; }
        .progress-bar { width: 100%; height: 20px; background: #ecf0f1; border-radius: 10px; overflow: hidden; }
        .progress-fill { height: 100%; background: #3498db; transition: width 0.3s ease; }
        .job-item { border: 1px solid #ecf0f1; border-radius: 6px; padding: 1rem; margin-bottom: 1rem; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1rem; }
        .stat-item { text-align: center; padding: 1rem; background: #ecf0f1; border-radius: 6px; }
        .stat-number { font-size: 2rem; font-weight: bold; color: #2c3e50; }
        .stat-label { font-size: 0.9rem; color: #7f8c8d; }
        .log-container { max-height: 300px; overflow-y: auto; background: #2c3e50; color: #ecf0f1; padding: 1rem; border-radius: 6px; font-family: monospace; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🕷️ Web Scraping Tool Dashboard</h1>
        <p>Monitor and control your scraping operations</p>
    </div>

    <div class="container">
        <div class="grid">
            <!-- Create New Job -->
            <div class="card">
                <h2>Create New Job</h2>
                <form id="job-form">
                    <div class="form-group">
                        <label for="job-type">Job Type:</label>
                        <select id="job-type" onchange="toggleJobType()">
                            <option value="search">Search Query</option>
                            <option value="urls">Direct URLs</option>
                        </select>
                    </div>
                    
                    <div class="form-group" id="query-group">
                        <label for="query">Search Query:</label>
                        <input type="text" id="query" placeholder="e.g., AI startups in Silicon Valley">
                    </div>
                    
                    <div class="form-group" id="urls-group" style="display: none;">
                        <label for="urls">URLs (one per line):</label>
                        <textarea id="urls" rows="4" placeholder="https://example.com\\nhttps://company.com"></textarea>
                    </div>
                    
                    <div class="form-group">
                        <label for="extraction-level">Extraction Level:</label>
                        <select id="extraction-level">
                            <option value="basic">Basic</option>
                            <option value="medium">Medium</option>
                            <option value="advanced">Advanced</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label for="output-format">Output Format:</label>
                        <select id="output-format">
                            <option value="json">JSON</option>
                            <option value="csv">CSV</option>
                            <option value="xlsx">Excel</option>
                        </select>
                    </div>
                    
                    <button type="submit" class="btn">Create Job</button>
                </form>
            </div>

            <!-- System Statistics -->
            <div class="card">
                <h2>System Statistics</h2>
                <div class="stats-grid" id="stats-grid">
                    <!-- Stats will be populated by JavaScript -->
                </div>
            </div>

            <!-- Active Jobs -->
            <div class="card">
                <h2>Active Jobs</h2>
                <div id="active-jobs">
                    <p>No active jobs</p>
                </div>
            </div>

            <!-- Recent Jobs -->
            <div class="card">
                <h2>Recent Jobs</h2>
                <div id="recent-jobs">
                    <p>No recent jobs</p>
                </div>
            </div>

            <!-- Live Log -->
            <div class="card">
                <h2>Live Log</h2>
                <div class="log-container" id="live-log">
                    <div>Dashboard initialized...</div>
                </div>
            </div>

            <!-- Proxy Status -->
            <div class="card">
                <h2>Proxy Status</h2>
                <div id="proxy-status">
                    <button class="btn btn-warning" onclick="testProxies()">Test Proxies</button>
                    <div id="proxy-results"></div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Socket.IO connection
        const socket = io();
        
        // Job form handling
        document.getElementById('job-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const jobType = document.getElementById('job-type').value;
            const query = document.getElementById('query').value;
            const urlsText = document.getElementById('urls').value;
            const extractionLevel = document.getElementById('extraction-level').value;
            const outputFormat = document.getElementById('output-format').value;
            
            const data = {
                extraction_level: extractionLevel,
                output_format: outputFormat
            };
            
            if (jobType === 'search') {
                data.query = query;
            } else {
                data.urls = urlsText.split('\\n').filter(url => url.trim());
            }
            
            try {
                const response = await fetch('/api/jobs', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    addToLog(`Created job: ${result.job_id}`);
                    // Auto-start the job
                    startJob(result.job_id);
                    // Reset form
                    document.getElementById('job-form').reset();
                } else {
                    addToLog(`Error: ${result.error}`);
                }
            } catch (error) {
                addToLog(`Error creating job: ${error.message}`);
            }
        });
        
        // Job type toggle
        function toggleJobType() {
            const jobType = document.getElementById('job-type').value;
            const queryGroup = document.getElementById('query-group');
            const urlsGroup = document.getElementById('urls-group');
            
            if (jobType === 'search') {
                queryGroup.style.display = 'block';
                urlsGroup.style.display = 'none';
            } else {
                queryGroup.style.display = 'none';
                urlsGroup.style.display = 'block';
            }
        }
        
        // Start job
        async function startJob(jobId) {
            try {
                const response = await fetch(`/api/jobs/${jobId}/start`, { method: 'POST' });
                const result = await response.json();
                
                if (response.ok) {
                    addToLog(`Started job: ${jobId}`);
                } else {
                    addToLog(`Error starting job: ${result.error}`);
                }
            } catch (error) {
                addToLog(`Error starting job: ${error.message}`);
            }
        }
        
        // Cancel job
        async function cancelJob(jobId) {
            try {
                const response = await fetch(`/api/jobs/${jobId}/cancel`, { method: 'POST' });
                const result = await response.json();
                
                if (response.ok) {
                    addToLog(`Cancelled job: ${jobId}`);
                } else {
                    addToLog(`Error cancelling job: ${result.error}`);
                }
            } catch (error) {
                addToLog(`Error cancelling job: ${error.message}`);
            }
        }
        
        // Download results
        function downloadResults(jobId) {
            window.open(`/api/download/${jobId}`, '_blank');
        }
        
        // Test proxies
        async function testProxies() {
            addToLog('Testing proxies...');
            document.getElementById('proxy-results').innerHTML = '<p>Testing proxies...</p>';
            
            try {
                const response = await fetch('/api/proxy/test', { method: 'POST' });
                const result = await response.json();
                
                if (response.ok) {
                    const html = `
                        <p>Working: ${result.working_proxies}, Failed: ${result.failed_proxies}</p>
                        <details>
                            <summary>Detailed Results</summary>
                            <div style="max-height: 200px; overflow-y: auto;">
                                ${result.test_results.map(r => 
                                    `<div>${r.proxy} - ${r.working ? '✅' : '❌'} (${r.response_time ? r.response_time.toFixed(2) + 's' : 'N/A'})</div>`
                                ).join('')}
                            </div>
                        </details>
                    `;
                    document.getElementById('proxy-results').innerHTML = html;
                    addToLog(`Proxy test completed: ${result.working_proxies} working`);
                } else {
                    addToLog(`Proxy test error: ${result.error}`);
                }
            } catch (error) {
                addToLog(`Error testing proxies: ${error.message}`);
            }
        }
        
        // Add message to log
        function addToLog(message) {
            const log = document.getElementById('live-log');
            const timestamp = new Date().toLocaleTimeString();
            const div = document.createElement('div');
            div.textContent = `[${timestamp}] ${message}`;
            log.appendChild(div);
            log.scrollTop = log.scrollHeight;
        }
        
        // Update jobs display
        async function updateJobs() {
            try {
                const response = await fetch('/api/jobs');
                const data = await response.json();
                
                // Update active jobs
                const activeJobsDiv = document.getElementById('active-jobs');
                if (data.active_jobs.length === 0) {
                    activeJobsDiv.innerHTML = '<p>No active jobs</p>';
                } else {
                    activeJobsDiv.innerHTML = data.active_jobs.map(job => `
                        <div class="job-item">
                            <div style="display: flex; justify-content: between; align-items: center; margin-bottom: 0.5rem;">
                                <strong>${job.query || 'URL Scraping'}</strong>
                                <span class="status status-${job.status}">${job.status}</span>
                            </div>
                            <div class="progress-bar">
                                <div class="progress-fill" style="width: ${job.progress}%"></div>
                            </div>
                            <div style="margin-top: 0.5rem; font-size: 0.9rem;">
                                Progress: ${job.progress.toFixed(1)}% | Level: ${job.extraction_level}
                            </div>
                            <div style="margin-top: 0.5rem;">
                                <button class="btn btn-danger btn-sm" onclick="cancelJob('${job.id}')">Cancel</button>
                            </div>
                        </div>
                    `).join('');
                }
                
                // Update recent jobs
                const recentJobsDiv = document.getElementById('recent-jobs');
                if (data.completed_jobs.length === 0) {
                    recentJobsDiv.innerHTML = '<p>No recent jobs</p>';
                } else {
                    recentJobsDiv.innerHTML = data.completed_jobs.map(job => `
                        <div class="job-item">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <strong>${job.query || 'URL Scraping'}</strong>
                                <span class="status status-${job.status}">${job.status}</span>
                            </div>
                            <div style="margin-top: 0.5rem; font-size: 0.9rem;">
                                Results: ${job.results_count} | Format: ${job.output_format}
                            </div>
                            ${job.status === 'completed' ? `
                                <div style="margin-top: 0.5rem;">
                                    <button class="btn btn-success btn-sm" onclick="downloadResults('${job.id}')">Download</button>
                                </div>
                            ` : ''}
                        </div>
                    `).join('');
                }
                
            } catch (error) {
                console.error('Error updating jobs:', error);
            }
        }
        
        // Update statistics
        async function updateStats() {
            try {
                const response = await fetch('/api/stats');
                const stats = await response.json();
                
                const statsGrid = document.getElementById('stats-grid');
                statsGrid.innerHTML = `
                    <div class="stat-item">
                        <div class="stat-number">${stats.total_jobs}</div>
                        <div class="stat-label">Total Jobs</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-number">${stats.successful_jobs}</div>
                        <div class="stat-label">Successful</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-number">${stats.failed_jobs}</div>
                        <div class="stat-label">Failed</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-number">${stats.total_companies_scraped}</div>
                        <div class="stat-label">Companies</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-number">${stats.uptime_hours.toFixed(1)}h</div>
                        <div class="stat-label">Uptime</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-number">${stats.proxy_stats.working_proxies}</div>
                        <div class="stat-label">Proxies</div>
                    </div>
                `;
                
            } catch (error) {
                console.error('Error updating stats:', error);
            }
        }
        
        // Socket.IO event handlers
        socket.on('connect', () => {
            addToLog('Connected to dashboard');
        });
        
        socket.on('job_progress', (data) => {
            addToLog(`Job ${data.job_id}: ${data.progress.toFixed(1)}% - ${data.message}`);
        });
        
        // Auto-refresh data
        setInterval(updateJobs, 2000);  // Every 2 seconds
        setInterval(updateStats, 5000); // Every 5 seconds
        
        // Initial load
        updateJobs();
        updateStats();
    </script>
</body>
</html>'''
    
    with open('templates/index.html', 'w') as f:
        f.write(index_html)
    
    logger.info("Created HTML templates")

def run_dashboard(host='localhost', port=5000, debug=False):
    """Run the web dashboard"""
    print(f"🌐 Starting Web Dashboard on http://{host}:{port}")
    
    # Create templates if they don't exist
    if not os.path.exists('templates/index.html'):
        create_templates()
    
    # Run the Flask app
    socketio.run(app, host=host, port=port, debug=debug)

if __name__ == "__main__":
    # Create templates
    create_templates()
    
    # Run dashboard
    run_dashboard(host='0.0.0.0', port=5000, debug=True) 