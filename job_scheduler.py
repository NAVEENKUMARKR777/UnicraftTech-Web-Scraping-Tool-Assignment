#!/usr/bin/env python3
"""
Job Scheduler for Automated Web Scraping
Uses APScheduler for cron-like scheduling of scraping jobs
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
import logging
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import threading
import time

from main import WebScrapingTool
from data_output import DataOutput

logger = logging.getLogger(__name__)

class ScheduleType(Enum):
    ONCE = "once"           # Run once at specific time
    INTERVAL = "interval"   # Run every X minutes/hours/days
    CRON = "cron"          # Cron-style scheduling
    DAILY = "daily"        # Run daily at specific time
    WEEKLY = "weekly"      # Run weekly on specific day/time
    MONTHLY = "monthly"    # Run monthly on specific day/time

class JobStatus(Enum):
    SCHEDULED = "scheduled"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"

@dataclass
class ScheduledJob:
    id: str
    name: str
    description: str
    schedule_type: ScheduleType
    schedule_config: Dict[str, Any]
    scraping_config: Dict[str, Any]
    status: JobStatus
    created_at: datetime
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    run_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    output_files: List[str] = None
    
    def __post_init__(self):
        if self.output_files is None:
            self.output_files = []

class JobScheduler:
    """Advanced job scheduler for automated scraping"""
    
    def __init__(self, db_url: str = "sqlite:///scheduler.db"):
        # Configure job stores and executors
        jobstores = {
            'default': SQLAlchemyJobStore(url=db_url)
        }
        
        executors = {
            'default': ThreadPoolExecutor(max_workers=3)
        }
        
        job_defaults = {
            'coalesce': False,
            'max_instances': 1,
            'misfire_grace_time': 300  # 5 minutes
        }
        
        # Initialize scheduler
        self.scheduler = BackgroundScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
            timezone='UTC'
        )
        
        self.scheduled_jobs: Dict[str, ScheduledJob] = {}
        self.job_history: List[Dict[str, Any]] = []
        self.is_running = False
        self.lock = threading.Lock()
        
        # Event callbacks
        self.job_listeners: List[Callable] = []
        
        # Load existing jobs
        self._load_scheduled_jobs()
    
    def start(self):
        """Start the scheduler"""
        if not self.is_running:
            self.scheduler.start()
            self.is_running = True
            logger.info("Job scheduler started")
    
    def stop(self):
        """Stop the scheduler"""
        if self.is_running:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("Job scheduler stopped")
    
    def schedule_job(self, name: str, description: str, 
                    schedule_type: ScheduleType, schedule_config: Dict[str, Any],
                    scraping_config: Dict[str, Any]) -> str:
        """Schedule a new scraping job"""
        
        job_id = str(uuid.uuid4())
        
        # Create scheduled job record
        scheduled_job = ScheduledJob(
            id=job_id,
            name=name,
            description=description,
            schedule_type=schedule_type,
            schedule_config=schedule_config,
            scraping_config=scraping_config,
            status=JobStatus.SCHEDULED,
            created_at=datetime.now()
        )
        
        # Create appropriate trigger
        trigger = self._create_trigger(schedule_type, schedule_config)
        
        # Add job to scheduler
        self.scheduler.add_job(
            func=self._execute_scheduled_job,
            trigger=trigger,
            id=job_id,
            args=[job_id],
            name=name,
            replace_existing=True
        )
        
        # Update next run time
        job = self.scheduler.get_job(job_id)
        if job:
            scheduled_job.next_run = job.next_run_time
        
        # Store job
        with self.lock:
            self.scheduled_jobs[job_id] = scheduled_job
        
        self._save_scheduled_jobs()
        
        logger.info(f"Scheduled job '{name}' with ID {job_id}")
        return job_id
    
    def _create_trigger(self, schedule_type: ScheduleType, config: Dict[str, Any]):
        """Create appropriate trigger based on schedule type"""
        
        if schedule_type == ScheduleType.ONCE:
            run_date = config.get('run_date')
            if isinstance(run_date, str):
                run_date = datetime.fromisoformat(run_date)
            return DateTrigger(run_date=run_date)
            
        elif schedule_type == ScheduleType.INTERVAL:
            return IntervalTrigger(
                seconds=config.get('seconds', 0),
                minutes=config.get('minutes', 0),
                hours=config.get('hours', 0),
                days=config.get('days', 0),
                weeks=config.get('weeks', 0)
            )
            
        elif schedule_type == ScheduleType.CRON:
            return CronTrigger(
                year=config.get('year'),
                month=config.get('month'),
                day=config.get('day'),
                week=config.get('week'),
                day_of_week=config.get('day_of_week'),
                hour=config.get('hour'),
                minute=config.get('minute'),
                second=config.get('second')
            )
            
        elif schedule_type == ScheduleType.DAILY:
            hour = config.get('hour', 9)
            minute = config.get('minute', 0)
            return CronTrigger(hour=hour, minute=minute)
            
        elif schedule_type == ScheduleType.WEEKLY:
            day_of_week = config.get('day_of_week', 1)  # Monday
            hour = config.get('hour', 9)
            minute = config.get('minute', 0)
            return CronTrigger(day_of_week=day_of_week, hour=hour, minute=minute)
            
        elif schedule_type == ScheduleType.MONTHLY:
            day = config.get('day', 1)
            hour = config.get('hour', 9)
            minute = config.get('minute', 0)
            return CronTrigger(day=day, hour=hour, minute=minute)
        
        else:
            raise ValueError(f"Unsupported schedule type: {schedule_type}")
    
    def _execute_scheduled_job(self, job_id: str):
        """Execute a scheduled scraping job"""
        
        with self.lock:
            if job_id not in self.scheduled_jobs:
                logger.error(f"Scheduled job {job_id} not found")
                return
            
            scheduled_job = self.scheduled_jobs[job_id]
            scheduled_job.status = JobStatus.RUNNING
            scheduled_job.last_run = datetime.now()
            scheduled_job.run_count += 1
        
        # Notify listeners
        self._notify_job_event("job_started", job_id, scheduled_job)
        
        try:
            logger.info(f"Executing scheduled job: {scheduled_job.name} (ID: {job_id})")
            
            # Initialize scraping tool
            scraping_config = scheduled_job.scraping_config
            tool = WebScrapingTool(
                use_selenium=scraping_config.get('use_selenium', True),
                output_dir=scraping_config.get('output_dir', 'scheduled_output')
            )
            
            # Execute scraping based on configuration
            if 'query' in scraping_config:
                # Search-based scraping
                result = tool.scrape_from_query(
                    query=scraping_config['query'],
                    max_results=scraping_config.get('max_results', 20),
                    extraction_level=scraping_config.get('extraction_level', 'basic'),
                    output_format=scraping_config.get('output_format', 'json'),
                    output_filename=f"scheduled_{job_id}_{int(time.time())}"
                )
            elif 'urls' in scraping_config:
                # URL-based scraping
                result = tool.scrape_from_urls(
                    urls=scraping_config['urls'],
                    extraction_level=scraping_config.get('extraction_level', 'basic'),
                    output_format=scraping_config.get('output_format', 'json'),
                    output_filename=f"scheduled_{job_id}_{int(time.time())}"
                )
            else:
                raise ValueError("No query or URLs specified in scraping configuration")
            
            # Update job status based on result
            with self.lock:
                if result.get('success'):
                    scheduled_job.status = JobStatus.COMPLETED
                    scheduled_job.success_count += 1
                    
                    # Store output file path
                    output_file = result.get('saved_file')
                    if output_file:
                        scheduled_job.output_files.append(output_file)
                    
                    logger.info(f"Scheduled job {job_id} completed successfully")
                    self._notify_job_event("job_completed", job_id, scheduled_job, result)
                    
                else:
                    scheduled_job.status = JobStatus.FAILED
                    scheduled_job.failure_count += 1
                    
                    error_msg = result.get('error', 'Unknown error')
                    logger.error(f"Scheduled job {job_id} failed: {error_msg}")
                    self._notify_job_event("job_failed", job_id, scheduled_job, {'error': error_msg})
                
                # Update next run time
                scheduler_job = self.scheduler.get_job(job_id)
                if scheduler_job:
                    scheduled_job.next_run = scheduler_job.next_run_time
                else:
                    scheduled_job.next_run = None
                
                # For one-time jobs, mark as completed
                if scheduled_job.schedule_type == ScheduleType.ONCE:
                    scheduled_job.status = JobStatus.COMPLETED
            
            tool.close()
            
        except Exception as e:
            with self.lock:
                scheduled_job.status = JobStatus.FAILED
                scheduled_job.failure_count += 1
            
            logger.error(f"Error executing scheduled job {job_id}: {e}")
            self._notify_job_event("job_failed", job_id, scheduled_job, {'error': str(e)})
        
        finally:
            # Reset status for recurring jobs
            with self.lock:
                if scheduled_job.schedule_type != ScheduleType.ONCE and scheduled_job.status != JobStatus.FAILED:
                    scheduled_job.status = JobStatus.SCHEDULED
            
            # Record execution in history
            execution_record = {
                'job_id': job_id,
                'job_name': scheduled_job.name,
                'execution_time': scheduled_job.last_run.isoformat(),
                'status': scheduled_job.status.value,
                'run_number': scheduled_job.run_count
            }
            
            self.job_history.append(execution_record)
            
            # Keep only last 1000 history entries
            if len(self.job_history) > 1000:
                self.job_history = self.job_history[-1000:]
            
            self._save_scheduled_jobs()
    
    def pause_job(self, job_id: str) -> bool:
        """Pause a scheduled job"""
        try:
            self.scheduler.pause_job(job_id)
            
            with self.lock:
                if job_id in self.scheduled_jobs:
                    self.scheduled_jobs[job_id].status = JobStatus.PAUSED
            
            self._save_scheduled_jobs()
            logger.info(f"Paused job {job_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error pausing job {job_id}: {e}")
            return False
    
    def resume_job(self, job_id: str) -> bool:
        """Resume a paused job"""
        try:
            self.scheduler.resume_job(job_id)
            
            with self.lock:
                if job_id in self.scheduled_jobs:
                    self.scheduled_jobs[job_id].status = JobStatus.SCHEDULED
                    
                    # Update next run time
                    scheduler_job = self.scheduler.get_job(job_id)
                    if scheduler_job:
                        self.scheduled_jobs[job_id].next_run = scheduler_job.next_run_time
            
            self._save_scheduled_jobs()
            logger.info(f"Resumed job {job_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error resuming job {job_id}: {e}")
            return False
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a scheduled job"""
        try:
            self.scheduler.remove_job(job_id)
            
            with self.lock:
                if job_id in self.scheduled_jobs:
                    self.scheduled_jobs[job_id].status = JobStatus.CANCELLED
                    self.scheduled_jobs[job_id].next_run = None
            
            self._save_scheduled_jobs()
            logger.info(f"Cancelled job {job_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error cancelling job {job_id}: {e}")
            return False
    
    def get_job(self, job_id: str) -> Optional[ScheduledJob]:
        """Get scheduled job by ID"""
        return self.scheduled_jobs.get(job_id)
    
    def get_all_jobs(self) -> List[ScheduledJob]:
        """Get all scheduled jobs"""
        return list(self.scheduled_jobs.values())
    
    def get_job_history(self, job_id: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get job execution history"""
        if job_id:
            history = [record for record in self.job_history if record['job_id'] == job_id]
        else:
            history = self.job_history
        
        return history[-limit:]
    
    def get_scheduler_stats(self) -> Dict[str, Any]:
        """Get scheduler statistics"""
        active_jobs = [job for job in self.scheduled_jobs.values() 
                      if job.status in [JobStatus.SCHEDULED, JobStatus.RUNNING]]
        
        paused_jobs = [job for job in self.scheduled_jobs.values() 
                      if job.status == JobStatus.PAUSED]
        
        total_executions = sum(job.run_count for job in self.scheduled_jobs.values())
        total_successes = sum(job.success_count for job in self.scheduled_jobs.values())
        total_failures = sum(job.failure_count for job in self.scheduled_jobs.values())
        
        return {
            'total_jobs': len(self.scheduled_jobs),
            'active_jobs': len(active_jobs),
            'paused_jobs': len(paused_jobs),
            'total_executions': total_executions,
            'total_successes': total_successes,
            'total_failures': total_failures,
            'success_rate': (total_successes / total_executions * 100) if total_executions > 0 else 0,
            'scheduler_running': self.is_running,
            'next_jobs': self._get_next_jobs(5)
        }
    
    def _get_next_jobs(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get next jobs to run"""
        next_jobs = []
        
        for job in self.scheduler.get_jobs():
            if job.next_run_time:
                scheduled_job = self.scheduled_jobs.get(job.id)
                if scheduled_job:
                    next_jobs.append({
                        'job_id': job.id,
                        'job_name': scheduled_job.name,
                        'next_run': job.next_run_time.isoformat(),
                        'schedule_type': scheduled_job.schedule_type.value
                    })
        
        # Sort by next run time
        next_jobs.sort(key=lambda x: x['next_run'])
        
        return next_jobs[:limit]
    
    def add_job_listener(self, callback: Callable):
        """Add job event listener"""
        self.job_listeners.append(callback)
    
    def remove_job_listener(self, callback: Callable):
        """Remove job event listener"""
        if callback in self.job_listeners:
            self.job_listeners.remove(callback)
    
    def _notify_job_event(self, event: str, job_id: str, job: ScheduledJob, data: Dict[str, Any] = None):
        """Notify job event listeners"""
        for listener in self.job_listeners:
            try:
                listener(event, job_id, job, data or {})
            except Exception as e:
                logger.error(f"Error in job listener: {e}")
    
    def _save_scheduled_jobs(self):
        """Save scheduled jobs to file"""
        try:
            jobs_data = {}
            for job_id, job in self.scheduled_jobs.items():
                job_dict = asdict(job)
                # Convert datetime objects to strings
                for key, value in job_dict.items():
                    if isinstance(value, datetime):
                        job_dict[key] = value.isoformat()
                    elif isinstance(value, (ScheduleType, JobStatus)):
                        job_dict[key] = value.value
                
                jobs_data[job_id] = job_dict
            
            data_to_save = {
                'scheduled_jobs': jobs_data,
                'job_history': self.job_history[-500:]  # Save last 500 history entries
            }
            
            with open('scheduled_jobs.json', 'w') as f:
                json.dump(data_to_save, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving scheduled jobs: {e}")
    
    def _load_scheduled_jobs(self):
        """Load scheduled jobs from file"""
        try:
            if os.path.exists('scheduled_jobs.json'):
                with open('scheduled_jobs.json', 'r') as f:
                    data = json.load(f)
                
                # Load scheduled jobs
                jobs_data = data.get('scheduled_jobs', {})
                for job_id, job_dict in jobs_data.items():
                    # Convert string dates back to datetime
                    for key, value in job_dict.items():
                        if key.endswith('_at') and value:
                            job_dict[key] = datetime.fromisoformat(value)
                        elif key == 'schedule_type':
                            job_dict[key] = ScheduleType(value)
                        elif key == 'status':
                            job_dict[key] = JobStatus(value)
                    
                    # Ensure output_files is a list
                    if 'output_files' not in job_dict:
                        job_dict['output_files'] = []
                    
                    job = ScheduledJob(**job_dict)
                    self.scheduled_jobs[job_id] = job
                    
                    # Re-add job to scheduler if it's active
                    if job.status in [JobStatus.SCHEDULED, JobStatus.RUNNING]:
                        try:
                            trigger = self._create_trigger(job.schedule_type, job.schedule_config)
                            self.scheduler.add_job(
                                func=self._execute_scheduled_job,
                                trigger=trigger,
                                id=job_id,
                                args=[job_id],
                                name=job.name,
                                replace_existing=True
                            )
                        except Exception as e:
                            logger.error(f"Error re-adding job {job_id}: {e}")
                            job.status = JobStatus.FAILED
                
                # Load job history
                self.job_history = data.get('job_history', [])
                
                logger.info(f"Loaded {len(self.scheduled_jobs)} scheduled jobs")
                
        except Exception as e:
            logger.error(f"Error loading scheduled jobs: {e}")
    
    def export_jobs_config(self, filename: str = 'jobs_export.json'):
        """Export jobs configuration"""
        try:
            export_data = []
            
            for job in self.scheduled_jobs.values():
                job_config = {
                    'name': job.name,
                    'description': job.description,
                    'schedule_type': job.schedule_type.value,
                    'schedule_config': job.schedule_config,
                    'scraping_config': job.scraping_config
                }
                export_data.append(job_config)
            
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            logger.info(f"Exported {len(export_data)} jobs to {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting jobs: {e}")
            return False
    
    def import_jobs_config(self, filename: str = 'jobs_export.json'):
        """Import jobs configuration"""
        try:
            with open(filename, 'r') as f:
                import_data = json.load(f)
            
            imported_count = 0
            
            for job_config in import_data:
                try:
                    job_id = self.schedule_job(
                        name=job_config['name'],
                        description=job_config['description'],
                        schedule_type=ScheduleType(job_config['schedule_type']),
                        schedule_config=job_config['schedule_config'],
                        scraping_config=job_config['scraping_config']
                    )
                    imported_count += 1
                    logger.info(f"Imported job: {job_config['name']} (ID: {job_id})")
                    
                except Exception as e:
                    logger.error(f"Error importing job {job_config['name']}: {e}")
            
            logger.info(f"Imported {imported_count} jobs from {filename}")
            return imported_count
            
        except Exception as e:
            logger.error(f"Error importing jobs: {e}")
            return 0

# Utility functions for common scheduling patterns
def create_daily_job(name: str, query: str, hour: int = 9, minute: int = 0, 
                    extraction_level: str = "basic") -> Dict[str, Any]:
    """Create a daily job configuration"""
    return {
        'name': name,
        'description': f"Daily scraping: {query}",
        'schedule_type': ScheduleType.DAILY,
        'schedule_config': {'hour': hour, 'minute': minute},
        'scraping_config': {
            'query': query,
            'extraction_level': extraction_level,
            'output_format': 'json',
            'max_results': 20
        }
    }

def create_weekly_job(name: str, query: str, day_of_week: int = 1, 
                     hour: int = 9, minute: int = 0, extraction_level: str = "medium") -> Dict[str, Any]:
    """Create a weekly job configuration"""
    return {
        'name': name,
        'description': f"Weekly scraping: {query}",
        'schedule_type': ScheduleType.WEEKLY,
        'schedule_config': {'day_of_week': day_of_week, 'hour': hour, 'minute': minute},
        'scraping_config': {
            'query': query,
            'extraction_level': extraction_level,
            'output_format': 'xlsx',
            'max_results': 50
        }
    }

def create_interval_job(name: str, urls: List[str], hours: int = 1, 
                       extraction_level: str = "basic") -> Dict[str, Any]:
    """Create an interval-based job configuration"""
    return {
        'name': name,
        'description': f"Interval scraping: {len(urls)} URLs every {hours} hour(s)",
        'schedule_type': ScheduleType.INTERVAL,
        'schedule_config': {'hours': hours},
        'scraping_config': {
            'urls': urls,
            'extraction_level': extraction_level,
            'output_format': 'json'
        }
    }

# Example usage and testing
if __name__ == "__main__":
    # Create scheduler
    print("📅 Initializing Job Scheduler...")
    scheduler = JobScheduler()
    
    # Add a sample daily job
    daily_job_config = create_daily_job(
        name="Daily AI Startups Scan",
        query="AI startups in Silicon Valley",
        hour=9,
        minute=0,
        extraction_level="medium"
    )
    
    job_id = scheduler.schedule_job(**daily_job_config)
    print(f"✅ Created daily job: {job_id}")
    
    # Add a sample weekly job
    weekly_job_config = create_weekly_job(
        name="Weekly Fintech Report",
        query="fintech companies in New York",
        day_of_week=1,  # Monday
        hour=10,
        minute=30,
        extraction_level="advanced"
    )
    
    job_id = scheduler.schedule_job(**weekly_job_config)
    print(f"✅ Created weekly job: {job_id}")
    
    # Start scheduler
    scheduler.start()
    print("🚀 Scheduler started")
    
    # Show statistics
    stats = scheduler.get_scheduler_stats()
    print(f"📊 Scheduler Stats:")
    print(f"   Total jobs: {stats['total_jobs']}")
    print(f"   Active jobs: {stats['active_jobs']}")
    print(f"   Scheduler running: {stats['scheduler_running']}")
    
    # Show next jobs
    if stats['next_jobs']:
        print(f"📅 Next jobs:")
        for job in stats['next_jobs']:
            print(f"   - {job['job_name']}: {job['next_run']}")
    
    print("\n💡 Scheduler is running. Jobs will execute according to their schedules.")
    print("Press Ctrl+C to stop the scheduler.")
    
    try:
        import time
        while True:
            time.sleep(60)  # Check every minute
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping scheduler...")
        scheduler.stop()
        print("👋 Scheduler stopped") 