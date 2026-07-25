from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from core.executor import Executor
from core.market_sync import MarketSync
from datetime import datetime

app = FastAPI(title='Luna Core API')

class PredictionRequest(BaseModel):
    engine: str
    market: str

class SyncReport(BaseModel):
    status: str
    timestamp: str
    files_processed: int
    markets_updated: int
    records_added: int
    records_skipped: int

@app.get('/status')
def status():
    return {
        'app': 'Luna Core',
        'status': 'ready',
        'version': '1.0',
        'timezone': 'Asia/Jakarta'
    }

@app.get('/engines')
def engines():
    executor = Executor()
    available_engines = executor.get_available_engines()
    return {
        'engines': available_engines,
        'count': len(available_engines)
    }

@app.post('/analyze')
def analyze(request: PredictionRequest):
    """
    Execute prediction for a specific engine and market.
    
    Supported engines:
    - 'oregon': For Oregon markets (OREGON03, OREGON06, OREGON09, OREGON12)
    - 'toto_macau': For Toto Macau markets (TOTO MACAU)
    
    Example requests:
    - {"engine": "toto_macau", "market": "TOTO MACAU"}
    - {"engine": "oregon", "market": "OREGON03"}
    """
    executor = Executor()
    
    try:
        # Execute prediction
        result = executor.execute(request.engine, request.market)
        
        # Convert to dictionary for JSON response
        prediction_data = result.to_dict()
        
        return {
            'success': True,
            'result': prediction_data,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f'Prediction failed: {str(e)}'
        )

@app.get('/reports')
def get_reports():
    """
    Get market sync reports and system information.
    """
    try:
        # Check if reports exist
        report_files = []
        import os
        reports_dir = 'reports'
        
        if os.path.exists(reports_dir):
            for filename in os.listdir(reports_dir):
                if filename.endswith('.md') or filename.endswith('.json'):
                    filepath = os.path.join(reports_dir, filename)
                    report_files.append({
                        'filename': filename,
                        'size': os.path.getsize(filepath),
                        'modified': os.path.getmtime(filepath)
                    })
        
        return {
            'reports_available': len(report_files),
            'report_files': report_files,
            'last_sync_info': {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'status': 'available'
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f'Failed to get reports: {str(e)}'
        )

@app.post('/sync')
def sync_markets():
    """
    Trigger market synchronization.
    """
    try:
        sync = MarketSync()
        stats = sync.sync_all()
        
        return {
            'success': True,
            'sync_stats': stats,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f'Sync failed: {str(e)}'
        )

# Convenience endpoints for user requirements
@app.get('/totomacau')
def toto_macau_prediction():
    """
    Convenience endpoint for Toto Macau prediction.
    Equivalent to POST /analyze with {"engine": "toto_macau", "market": "TOTO MACAU"}
    """
    executor = Executor()
    
    try:
        result = executor.execute('toto_macau', 'TOTO MACAU')
        prediction_data = result.to_dict()
        
        return {
            'success': True,
            'engine': 'toto_macau',
            'market': 'TOTO MACAU',
            'prediction': prediction_data['prediction'],
            'analysis': prediction_data['analysis'],
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f'Toto Macau prediction failed: {str(e)}'
        )

@app.get('/oregon')
def oregon_options():
    """
    Oregon engine options endpoint.
    Returns available Oregon market options.
    """
    return {
        'oregon_markets': ['OREGON03', 'OREGON06', 'OREGON09', 'OREGON12'],
        'usage': 'Use POST /analyze with {"engine": "oregon", "market": "OREGON03"}',
        'example': {
            'OREGON03': 'Predicts Oregon 03 using Oregon 06, 09, 12 as sources',
            'OREGON06': 'Predicts Oregon 06 using Oregon 03, 09, 12 as sources',
            'OREGON09': 'Predicts Oregon 09 using Oregon 03, 06, 12 as sources',
            'OREGON12': 'Predicts Oregon 12 using Oregon 03, 06, 09 as sources'
        }
    }

@app.get('/oregon/{market}')
def oregon_prediction(market: str):
    """
    Oregon prediction for specific market.
    
    Example: GET /oregon/OREGON03
    """
    valid_markets = ['OREGON03', 'OREGON06', 'OREGON09', 'OREGON12']
    
    if market not in valid_markets:
        raise HTTPException(
            status_code=400,
            detail=f'Invalid Oregon market. Must be one of: {valid_markets}'
        )
    
    executor = Executor()
    
    try:
        result = executor.execute('oregon', market)
        prediction_data = result.to_dict()
        
        return {
            'success': True,
            'engine': 'oregon',
            'market': market,
            'prediction': prediction_data['prediction'],
            'analysis': prediction_data['analysis'],
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f'Oregon {market} prediction failed: {str(e)}'
        )

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)
