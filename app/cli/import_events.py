#!/usr/bin/env python3
"""
CLI script for importing historical event data from CSV.

Usage:
    python -m app.cli.import_events data/events_sample.csv
"""

import argparse
import csv
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import List
from uuid import UUID

from ..core.config import settings
from ..core.logging import setup_logging, get_logger
from ..database.connection import get_database_url, AsyncSessionLocal
from ..models.schemas import EventInput
from ..services.event_service import EventService

logger = get_logger(__name__)


def parse_csv_row(row: dict) -> EventInput:
    """Parse CSV row into EventInput model."""
    try:
        # Parse the datetime string
        occurred_at = datetime.fromisoformat(row['occurred_at'].replace('Z', '+00:00'))
        
        # Parse properties JSON
        properties = {}
        if row.get('properties_json'):
            properties = json.loads(row['properties_json'])
        
        return EventInput(
            event_id=UUID(row['event_id']),
            occurred_at=occurred_at,
            user_id=str(row['user_id']),  # Convert to string as required by schema
            event_type=row['event_type'],
            properties=properties
        )
    except (ValueError, KeyError) as e:
        raise ValueError(f"Failed to parse row {row}: {e}")


async def import_events_from_csv(csv_path: Path, batch_size: int = 1000) -> None:
    """Import events from CSV file."""
    
    if not csv_path.exists():
        logger.error(f"CSV file not found: {csv_path}")
        sys.exit(1)
    
    # Initialize database tables using sync engine
    from sqlalchemy import create_engine
    from ..models.database import Base
    
    sync_engine = create_engine(get_database_url(async_url=False))
    Base.metadata.create_all(bind=sync_engine)
    sync_engine.dispose()
    
    total_processed = 0
    total_created = 0
    total_duplicates = 0
    
    logger.info(f"Starting import from {csv_path}")
    
    with open(csv_path, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        batch = []
        
        for row_num, row in enumerate(reader, start=1):
            try:
                event = parse_csv_row(row)
                batch.append(event)
                
                # Process batch when it reaches batch_size
                if len(batch) >= batch_size:
                    processed, created, duplicates = await process_batch_async(batch)
                    total_processed += processed
                    total_created += created
                    total_duplicates += duplicates
                    
                    logger.info(
                        f"Processed batch",
                        batch_size=len(batch),
                        total_processed=total_processed,
                        total_created=total_created,
                        total_duplicates=total_duplicates
                    )
                    
                    batch = []
                
            except ValueError as e:
                logger.error(f"Skipping invalid row {row_num}: {e}")
                continue
        
        # Process remaining events in the final batch
        if batch:
            processed, created, duplicates = await process_batch_async(batch)
            total_processed += processed
            total_created += created
            total_duplicates += duplicates
    
    logger.info(
        "Import completed",
        total_processed=total_processed,
        total_created=total_created,
        total_duplicates=total_duplicates
    )


async def process_batch_async(events: List[EventInput]) -> tuple[int, int, int]:
    """Process a batch of events asynchronously."""
    try:
        async with AsyncSessionLocal() as db:
            event_service = EventService(db)
            responses, created_count, duplicate_count = await event_service.create_events(events)
            return len(responses), created_count, duplicate_count
    except Exception as e:
        logger.error(f"Failed to process batch: {e}")
        return 0, 0, 0


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Import historical event data from CSV"
    )
    parser.add_argument(
        "csv_path",
        type=Path,
        help="Path to CSV file with event data"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=1000,
        help="Number of events to process in each batch (default: 1000)"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging()
    
    try:
        import asyncio
        asyncio.run(import_events_from_csv(args.csv_path, args.batch_size))
    except KeyboardInterrupt:
        logger.info("Import interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Import failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
