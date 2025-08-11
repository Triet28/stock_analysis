#!/usr/bin/env python
import logging
import os
import sys
import argparse
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("stock-analysis")

def check_environment():
    """Verify environment setup and configuration"""
    logger.info("Checking environment setup...")
    
    # Check Python version
    python_version = sys.version.split()[0]
    logger.info(f"Python version: {python_version}")
    
    # Check required environment variables
    load_dotenv()
    required_vars = [
        'API_BASE_URL', 
        'ATTACHMENT_TOKEN', 
        'TRADE_DATA_TOKEN'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please create a .env file with these variables or set them in your environment.")
        return False
    
    # Check if needed packages are installed
    try:
        import fastapi
        import pandas
        import plotly
        import uvicorn
        
        logger.info("All required packages are installed.")
    except ImportError as e:
        logger.error(f"Missing required package: {e}")
        logger.error("Please install all required packages with: pip install -r requirements.txt")
        return False
    
    logger.info("Environment check completed successfully!")
    return True

def main():
    """Run the application based on command line arguments"""
    parser = argparse.ArgumentParser(description='Stock Analysis Application')
    parser.add_argument('--service', choices=['api', 'bot', 'both'], default='both',
                      help='Choose which service to run: api, bot, or both (default)')
    parser.add_argument('--check', action='store_true', 
                      help='Check environment setup and exit')
    parser.add_argument('--port', type=int, default=8686,
                      help='Port to run the API server on (default: 8000)')
    
    args = parser.parse_args()
    
    # Check environment if requested
    if args.check:
        check_environment()
        return
    
    # Verify environment before running services
    if not check_environment():
        logger.error("Environment check failed. Please fix the issues before running the application.")
        return
    
    # Run the requested services
    if args.service in ['api', 'both']:
        # Import here to avoid importing if we're just checking environment
        import uvicorn
        from threading import Thread
        
        # Start API server in a separate thread if running both services
        if args.service == 'both':
            api_thread = Thread(
                target=uvicorn.run,
                kwargs={
                    "app": "candlestick_chart:app",
                    "host": "0.0.0.0",
                    "port": args.port,
                    "log_level": "info"
                }
            )
            api_thread.daemon = False
            api_thread.start()
            logger.info(f"API server starting in background on port {args.port}...")
        else:
            # Run API server in main thread
            logger.info(f"Starting API server on port {args.port}...")
            uvicorn.run("candlestick_chart:app", host="0.0.0.0", port=args.port)
    
    # Run Telegram bot if requested
    if args.service in ['bot', 'both']:
        # Check if Telegram token is set
        if not os.getenv('TELEGRAM_BOT_TOKEN'):
            logger.error("TELEGRAM_BOT_TOKEN is not set in environment variables.")
            logger.error("Please set it in your .env file or environment and try again.")
            return
        
        # Check if SERVER_URL is set when running bot only
        if args.service == 'bot' and not os.getenv('SERVER_URL'):
            logger.error("SERVER_URL is not set in environment variables.")
            logger.error("This is required when running the bot service alone.")
            logger.error("Please set it in your .env file or environment and try again.")
            return
        
        # Set default SERVER_URL when running both services together
        if args.service == 'both' and not os.getenv('SERVER_URL'):
            os.environ['SERVER_URL'] = f"http://localhost:{args.port}"
            logger.info(f"Setting SERVER_URL to http://localhost:{args.port}")
        
        logger.info("Starting Telegram bot...")
        # Import and run the bot
        import telegram_bot
        telegram_bot.main()

if __name__ == "__main__":
    main()
