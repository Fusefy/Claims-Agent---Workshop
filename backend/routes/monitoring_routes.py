"""
Monitoring data routes
Serves real-time monitoring data from JSON files in the monitoring directory
"""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
import logging
import json
import os
import glob
from typing import List, Dict, Any, Optional
from datetime import datetime

router = APIRouter()
logger = logging.getLogger(__name__)

MONITORING_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "monitoring")


def get_monitoring_files() -> List[str]:
    """
    Discover all monitoring JSON files in the monitoring directory.
    Returns list of file paths.
    """
    pattern = os.path.join(MONITORING_DIR, "monitoring_*.json")
    files = glob.glob(pattern)
    logger.info(f"[MONITORING] Found {len(files)} monitoring files")
    return files


def parse_monitoring_file(file_path: str) -> Optional[Dict[str, Any]]:
    """
    Parse a monitoring JSON file and validate required fields.
    Returns parsed data or None if invalid.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Validate required fields
        required_fields = ['run_id', 'monitoring_window', 'metrics', 'drift', 'data_quality', 'alerts', 'status']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            logger.error(f"[MONITORING] File {os.path.basename(file_path)} missing required fields: {missing_fields}")
            return None
        
        # Validate monitoring_window has timestamp
        if 'start_time' not in data['monitoring_window'] and 'timestamp' not in data['monitoring_window']:
            logger.error(f"[MONITORING] File {os.path.basename(file_path)} missing timestamp in monitoring_window")
            return None
        
        return data
        
    except json.JSONDecodeError as e:
        logger.error(f"[MONITORING] Invalid JSON in {os.path.basename(file_path)}: {e}")
        return None
    except Exception as e:
        logger.error(f"[MONITORING] Error reading {os.path.basename(file_path)}: {e}")
        return None


def get_timestamp(monitoring_run: Dict[str, Any]) -> str:
    """
    Extract timestamp from monitoring run for sorting.
    Supports both start_time and timestamp fields.
    """
    monitoring_window = monitoring_run.get('monitoring_window', {})
    return monitoring_window.get('start_time', monitoring_window.get('timestamp', ''))


def sort_by_timestamp(monitoring_runs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Sort monitoring runs by start_time in ascending order (oldest first).
    """
    return sorted(monitoring_runs, key=get_timestamp)


def load_all_monitoring_data() -> List[Dict[str, Any]]:
    """
    Load and parse all monitoring JSON files.
    Returns sorted list of valid monitoring runs.
    """
    files = get_monitoring_files()
    
    if not files:
        logger.warning("[MONITORING] No monitoring files found")
        return []
    
    monitoring_runs = []
    for file_path in files:
        data = parse_monitoring_file(file_path)
        if data:
            monitoring_runs.append(data)
            logger.debug(f"[MONITORING] Loaded {os.path.basename(file_path)}")
    
    # Sort chronologically
    sorted_runs = sort_by_timestamp(monitoring_runs)
    logger.info(f"[MONITORING] Successfully loaded {len(sorted_runs)} monitoring runs")
    
    return sorted_runs


@router.get("/api/monitoring/all")
async def get_all_monitoring_data():
    """
    Get all monitoring runs sorted chronologically (oldest to newest).
    
    Returns:
        JSON with array of monitoring runs and count
    """
    try:
        monitoring_runs = load_all_monitoring_data()
        
        if not monitoring_runs:
            raise HTTPException(
                status_code=404,
                detail="No monitoring files found in backend/monitoring/ directory"
            )
        
        logger.info(f"[MONITORING] Serving {len(monitoring_runs)} monitoring runs")
        
        return JSONResponse(
            status_code=200,
            content={
                "runs": monitoring_runs,
                "count": len(monitoring_runs)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[MONITORING] Error loading monitoring data: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error reading monitoring files: {str(e)}")


@router.get("/api/monitoring/latest")
async def get_latest_monitoring_data():
    """
    Get the most recent monitoring run.
    
    Returns:
        Latest monitoring run JSON
    """
    try:
        monitoring_runs = load_all_monitoring_data()
        
        if not monitoring_runs:
            raise HTTPException(
                status_code=404,
                detail="No monitoring files found in backend/monitoring/ directory"
            )
        
        # Get the last item (most recent after sorting)
        latest_run = monitoring_runs[-1]
        
        logger.info(f"[MONITORING] Serving latest monitoring run: {latest_run.get('run_id', 'unknown')}")
        
        return JSONResponse(status_code=200, content=latest_run)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[MONITORING] Error loading latest monitoring data: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error reading monitoring files: {str(e)}")


@router.get("/api/monitoring/history")
async def get_monitoring_history(limit: Optional[int] = Query(default=10, ge=1, le=100)):
    """
    Get recent monitoring runs with optional limit.
    
    Args:
        limit: Maximum number of runs to return (default: 10, max: 100)
    
    Returns:
        JSON with array of recent monitoring runs and count
    """
    try:
        monitoring_runs = load_all_monitoring_data()
        
        if not monitoring_runs:
            raise HTTPException(
                status_code=404,
                detail="No monitoring files found in backend/monitoring/ directory"
            )
        
        # Get the most recent N runs (reverse order, then take limit, then reverse back)
        recent_runs = monitoring_runs[-limit:] if len(monitoring_runs) > limit else monitoring_runs
        
        logger.info(f"[MONITORING] Serving {len(recent_runs)} recent monitoring runs (limit: {limit})")
        
        return JSONResponse(
            status_code=200,
            content={
                "runs": recent_runs,
                "count": len(recent_runs)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[MONITORING] Error loading monitoring history: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error reading monitoring files: {str(e)}")
