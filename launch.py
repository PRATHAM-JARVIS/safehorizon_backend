#!/usr/bin/env python3
"""
SafeHorizon Quick Launcher
=========================

One-command setup for SafeHorizon complete server deployment.

Usage:
    python launch.py                    # Basic production server
    python launch.py --dev              # Development with sample data
    python launch.py --domain my.com    # Custom domain
    python launch.py --ssl              # Enable HTTPS
"""

import subprocess
import sys
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='SafeHorizon Quick Launcher')
    parser.add_argument('--dev', action='store_true',
                       help='Development mode with sample data')
    parser.add_argument('--domain', default='localhost',
                       help='Domain for the server')
    parser.add_argument('--ssl', action='store_true',
                       help='Enable SSL/HTTPS')
    
    args = parser.parse_args()
    
    # Build command
    cmd = ['python3', 'setup_complete_docker.py']
    
    if args.domain != 'localhost':
        cmd.extend(['--domain', args.domain])
    
    if args.ssl:
        cmd.append('--ssl')
    
    if args.dev:
        cmd.append('--with-sample-data')
        cmd.extend(['--environment', 'development'])
    
    logger.info("🚀 Launching SafeHorizon Server...")
    logger.info(f"Command: {' '.join(cmd)}")
    
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Setup failed: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("❌ Setup interrupted by user")
        sys.exit(1)


if __name__ == '__main__':
    main()