"""
Metrics validation routes
Serves real-time metrics data from metrics_output.json (day1.json format)
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import logging
import json
import os
import glob
from typing import Optional

router = APIRouter()
logger = logging.getLogger(__name__)

# Use the metrics output file in validation folder
METRICS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "validation", "metrics_output.json")


@router.get("/api/metrics/latest")
async def get_latest_metrics():
    """
    Get the latest metrics validation output from metrics_output.json
    
    Returns:
        Latest metrics JSON with KPI data in day1.json format
    """
    try:
        # Check if metrics file exists
        if not os.path.exists(METRICS_FILE):
            raise HTTPException(
                status_code=404,
                detail=f"Metrics file not found: {METRICS_FILE}"
            )
        
        logger.info(f"[METRICS] Serving metrics from: {METRICS_FILE}")
        
        # Read and return the JSON
        with open(METRICS_FILE, 'r', encoding='utf-8') as f:
            metrics_data = json.load(f)
        
        return JSONResponse(status_code=200, content=metrics_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[METRICS] Error reading metrics: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/metrics/history")
async def get_metrics_history(limit: Optional[int] = 10):
    """
    Get historical metrics data
    
    Args:
        limit: Maximum number of historical records to return (default: 10)
    
    Returns:
        List of historical metrics data
    """
    try:
        # Find all metrics output files
        pattern = os.path.join(VALIDATION_DIR, "metrics_output_*.json")
        files = glob.glob(pattern)
        
        if not files:
            raise HTTPException(
                status_code=404,
                detail="No metrics output files found."
            )
        
        # Sort by creation time (newest first) and limit
        files = sorted(files, key=os.path.getctime, reverse=True)[:limit]
        
        history = []
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    history.append(data)
            except Exception as e:
                logger.warning(f"[METRICS] Could not read {file_path}: {e}")
                continue
        
        return JSONResponse(status_code=200, content={"history": history, "count": len(history)})
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[METRICS] Error reading metrics history: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
