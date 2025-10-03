#!/usr/bin/env python3
"""
Database Verification Script
============================

Quick script to verify the SafeHorizon database setup is working correctly.

Usage:
    python verify_database.py
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


async def verify_database():
    """Verify database connection and schema"""
    try:
        # Load environment variables
        from dotenv import load_dotenv
        load_dotenv()
        
        # Test database connection
        from app.database import AsyncSessionLocal
        from sqlalchemy import text
        
        logger.info("Testing database connection...")
        async with AsyncSessionLocal() as session:
            # Test basic connection
            result = await session.execute(text("SELECT version();"))
            version = result.scalar()
            logger.info(f"✓ PostgreSQL version: {version}")
            
            # Test PostGIS
            try:
                result = await session.execute(text("SELECT PostGIS_version();"))
                postgis_version = result.scalar()
                logger.info(f"✓ PostGIS version: {postgis_version}")
            except Exception as e:
                logger.warning(f"PostGIS not available: {e}")
            
            # Check if tables exist
            result = await session.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name;
            """))
            tables = [row[0] for row in result.fetchall()]
            
            if tables:
                logger.info(f"✓ Found {len(tables)} tables:")
                for table in tables:
                    logger.info(f"  - {table}")
            else:
                logger.warning("No tables found. Run migrations with: python -m alembic upgrade head")
            
            # Check sample data if it exists
            from app.models.database_models import Tourist, Authority
            from sqlalchemy import select
            
            # Count tourists
            result = await session.execute(select(Tourist))
            tourist_count = len(result.scalars().all())
            logger.info(f"✓ Found {tourist_count} tourists in database")
            
            # Count authorities
            result = await session.execute(select(Authority))
            authority_count = len(result.scalars().all())
            logger.info(f"✓ Found {authority_count} authorities in database")
            
        logger.info("🎉 Database verification completed successfully!")
        return True
        
    except ImportError as e:
        logger.error(f"Missing dependencies: {e}")
        logger.info("Install with: python3 -m pip install -r requirements.txt --user")
        return False
    except Exception as e:
        logger.error(f"Database verification failed: {e}")
        return False


def verify_config():
    """Verify configuration files"""
    logger.info("Checking configuration files...")
    
    project_root = Path(__file__).parent
    
    # Check .env file
    env_file = project_root / '.env'
    if env_file.exists():
        logger.info("✓ .env file found")
        
        # Check required variables
        required_vars = ['DATABASE_URL', 'SYNC_DATABASE_URL']
        with open(env_file, 'r') as f:
            content = f.read()
            
        for var in required_vars:
            if var in content:
                logger.info(f"✓ {var} configured")
            else:
                logger.warning(f"❌ {var} not found in .env")
    else:
        logger.error("❌ .env file not found")
        return False
    
    # Check requirements.txt
    req_file = project_root / 'requirements.txt'
    if req_file.exists():
        logger.info("✓ requirements.txt found")
    else:
        logger.warning("❌ requirements.txt not found")
    
    # Check alembic directory
    alembic_dir = project_root / 'alembic'
    if alembic_dir.exists():
        logger.info("✓ alembic directory found")
        
        # Check for migration files
        versions_dir = alembic_dir / 'versions'
        if versions_dir.exists():
            migrations = list(versions_dir.glob('*.py'))
            logger.info(f"✓ Found {len(migrations)} migration files")
        else:
            logger.warning("❌ No migrations directory found")
    else:
        logger.warning("❌ alembic directory not found")
    
    return True


def main():
    logger.info("Starting SafeHorizon Database Verification...")
    
    # Verify configuration
    config_ok = verify_config()
    
    if not config_ok:
        logger.error("Configuration verification failed")
        sys.exit(1)
    
    # Verify database
    try:
        db_ok = asyncio.run(verify_database())
        if db_ok:
            logger.info("\n✅ All verifications passed! Your database is ready.")
        else:
            logger.error("\n❌ Database verification failed.")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Verification failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()