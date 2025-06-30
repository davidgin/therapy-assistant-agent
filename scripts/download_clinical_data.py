#!/usr/bin/env python3
"""
Script to download and manage free clinical data sources
"""

import asyncio
import argparse
import logging
import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent / "backend"))

from app.services.data_acquisition import (
    DataAcquisitionService,
    download_clinical_guidelines,
    download_research_data,
    download_classification_data
)
from app.config.data_sources import (
    FREE_CLINICAL_DATA_SOURCES,
    get_sources_by_category,
    get_high_reliability_sources,
    DATA_CATEGORIES
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def list_sources(args):
    """List available data sources"""
    print("Available Clinical Data Sources:")
    print("=" * 50)
    
    if args.category:
        sources = get_sources_by_category(args.category)
        print(f"\nCategory: {args.category}")
        print(f"Description: {DATA_CATEGORIES.get(args.category, 'No description')}")
    else:
        sources = list(FREE_CLINICAL_DATA_SOURCES.values())
    
    for source in sources:
        print(f"\nName: {source.name}")
        print(f"Description: {source.description}")
        print(f"URL: {source.url}")
        print(f"Type: {source.source_type.value}")
        print(f"Format: {source.data_format.value}")
        print(f"Reliability: {source.reliability_score}")
        print(f"Categories: {', '.join(source.categories)}")
        print(f"Rate Limit: {source.rate_limit or 'None'}")
        print("-" * 30)
    
    print(f"\nTotal sources: {len(sources)}")

async def list_categories(args):
    """List available categories"""
    print("Available Categories:")
    print("=" * 30)
    
    for category, description in DATA_CATEGORIES.items():
        sources = get_sources_by_category(category)
        print(f"\n{category}: {description}")
        print(f"  Sources: {len(sources)}")

async def download_all(args):
    """Download from all sources"""
    service = DataAcquisitionService(
        data_dir=args.output_dir,
        max_concurrent=args.concurrent
    )
    
    print(f"Starting download from all sources...")
    print(f"Output directory: {args.output_dir}")
    print(f"Max concurrent: {args.concurrent}")
    print(f"Min reliability: {args.min_reliability}")
    
    if args.categories:
        print(f"Categories: {', '.join(args.categories)}")
    
    results = await service.acquire_all_sources(
        categories=args.categories,
        min_reliability=args.min_reliability
    )
    
    print_results(results)

async def download_category(args):
    """Download from specific category"""
    if args.category not in DATA_CATEGORIES:
        print(f"Error: Unknown category '{args.category}'")
        print(f"Available categories: {', '.join(DATA_CATEGORIES.keys())}")
        return
    
    service = DataAcquisitionService(
        data_dir=args.output_dir,
        max_concurrent=args.concurrent
    )
    
    print(f"Downloading from category: {args.category}")
    
    if args.category == "guidelines":
        results = await download_clinical_guidelines()
    elif args.category == "research":
        results = await download_research_data()
    elif args.category == "classification":
        results = await download_classification_data()
    else:
        results = await service.acquire_all_sources(
            categories=[args.category],
            min_reliability=args.min_reliability
        )
    
    print_results(results)

async def download_source(args):
    """Download from specific source"""
    if args.source not in FREE_CLINICAL_DATA_SOURCES:
        print(f"Error: Unknown source '{args.source}'")
        print(f"Available sources: {', '.join(FREE_CLINICAL_DATA_SOURCES.keys())}")
        return
    
    service = DataAcquisitionService(
        data_dir=args.output_dir,
        max_concurrent=1
    )
    
    source = FREE_CLINICAL_DATA_SOURCES[args.source]
    print(f"Downloading from: {source.name}")
    
    result = await service._acquire_source(args.source, source)
    
    if result.get("success"):
        print(f"✓ Successfully downloaded from {args.source}")
        print(f"  Files: {result.get('files', [])}")
        print(f"  Records: {result.get('records', 0)}")
        print(f"  Size: {result.get('size_bytes', 0)} bytes")
    else:
        print(f"✗ Failed to download from {args.source}")
        print(f"  Error: {result.get('error', 'Unknown error')}")

async def validate_data(args):
    """Validate downloaded data"""
    data_dir = Path(args.output_dir)
    
    if not data_dir.exists():
        print(f"Error: Data directory {data_dir} does not exist")
        return
    
    print(f"Validating data in: {data_dir}")
    print("=" * 40)
    
    total_files = 0
    total_size = 0
    
    for category_dir in data_dir.iterdir():
        if category_dir.is_dir() and category_dir.name != "metadata":
            files = list(category_dir.rglob("*"))
            files = [f for f in files if f.is_file()]
            
            category_size = sum(f.stat().st_size for f in files)
            
            print(f"\n{category_dir.name}:")
            print(f"  Files: {len(files)}")
            print(f"  Size: {format_bytes(category_size)}")
            
            total_files += len(files)
            total_size += category_size
    
    print(f"\nTotal:")
    print(f"  Files: {total_files}")
    print(f"  Size: {format_bytes(total_size)}")
    
    # Check for recent acquisition reports
    metadata_dir = data_dir / "metadata"
    if metadata_dir.exists():
        reports = list(metadata_dir.glob("acquisition_report_*.json"))
        if reports:
            latest_report = max(reports, key=lambda x: x.stat().st_mtime)
            print(f"\nLatest acquisition report: {latest_report.name}")

def print_results(results):
    """Print acquisition results"""
    print("\nAcquisition Results:")
    print("=" * 30)
    
    print(f"Total sources processed: {results['total_sources']}")
    print(f"Successfully acquired: {len(results['acquired'])}")
    print(f"Failed: {len(results['failed'])}")
    print(f"Skipped: {len(results['skipped'])}")
    
    if results['acquired']:
        print(f"\n✓ Successfully acquired:")
        for item in results['acquired']:
            size_mb = item['size_bytes'] / (1024 * 1024)
            print(f"  • {item['name']}: {item['records']} records ({size_mb:.1f} MB)")
    
    if results['failed']:
        print(f"\n✗ Failed to acquire:")
        for item in results['failed']:
            print(f"  • {item['name']}: {item['error']}")
    
    if results['skipped']:
        print(f"\n⚠ Skipped:")
        for item in results['skipped']:
            print(f"  • {item['name']}: {item['reason']}")

def format_bytes(bytes_value):
    """Format bytes in human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} TB"

def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Download and manage free clinical data sources"
    )
    
    parser.add_argument(
        "--output-dir", "-o",
        default="backend/data/acquired",
        help="Output directory for downloaded data"
    )
    
    parser.add_argument(
        "--concurrent", "-c",
        type=int,
        default=3,
        help="Maximum concurrent downloads"
    )
    
    parser.add_argument(
        "--min-reliability", "-r",
        type=float,
        default=0.8,
        help="Minimum reliability score (0.0-1.0)"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # List sources command
    list_parser = subparsers.add_parser("list", help="List available data sources")
    list_parser.add_argument(
        "--category",
        choices=list(DATA_CATEGORIES.keys()),
        help="Filter by category"
    )
    list_parser.set_defaults(func=list_sources)
    
    # List categories command
    categories_parser = subparsers.add_parser("categories", help="List available categories")
    categories_parser.set_defaults(func=list_categories)
    
    # Download all command
    all_parser = subparsers.add_parser("download-all", help="Download from all sources")
    all_parser.add_argument(
        "--categories",
        nargs="+",
        choices=list(DATA_CATEGORIES.keys()),
        help="Limit to specific categories"
    )
    all_parser.set_defaults(func=download_all)
    
    # Download category command
    category_parser = subparsers.add_parser("download-category", help="Download from specific category")
    category_parser.add_argument(
        "category",
        choices=list(DATA_CATEGORIES.keys()),
        help="Category to download"
    )
    category_parser.set_defaults(func=download_category)
    
    # Download source command
    source_parser = subparsers.add_parser("download-source", help="Download from specific source")
    source_parser.add_argument(
        "source",
        choices=list(FREE_CLINICAL_DATA_SOURCES.keys()),
        help="Source to download"
    )
    source_parser.set_defaults(func=download_source)
    
    # Validate data command
    validate_parser = subparsers.add_parser("validate", help="Validate downloaded data")
    validate_parser.set_defaults(func=validate_data)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Run the selected command
    asyncio.run(args.func(args))

if __name__ == "__main__":
    main()