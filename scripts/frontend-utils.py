#!/usr/bin/env python3
"""
Pupper Frontend Utilities
Provides utilities for managing frontend deployments, CloudFront invalidations, and monitoring
"""

import boto3
import json
import time
import argparse
import sys
from datetime import datetime
from typing import Dict, List, Optional


class PupperFrontendManager:
    def __init__(self, region: str = 'us-east-1'):
        self.region = region
        self.s3_client = boto3.client('s3', region_name=region)
        self.cloudfront_client = boto3.client('cloudfront', region_name=region)
        self.cdk_outputs = self._load_cdk_outputs()
    
    def _load_cdk_outputs(self) -> Dict:
        """Load CDK outputs from cdk-outputs.json"""
        try:
            with open('cdk-outputs.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print("❌ cdk-outputs.json not found. Deploy the stack first.")
            return {}
    
    def get_distribution_id(self) -> Optional[str]:
        """Get CloudFront distribution ID from CDK outputs"""
        try:
            return self.cdk_outputs['PupperFrontendStack']['CloudFrontDistributionId']
        except KeyError:
            print("❌ CloudFront Distribution ID not found in outputs")
            return None
    
    def get_bucket_name(self) -> Optional[str]:
        """Get S3 bucket name from CDK outputs"""
        try:
            return self.cdk_outputs['PupperFrontendStack']['FrontendBucketName']
        except KeyError:
            print("❌ S3 Bucket name not found in outputs")
            return None
    
    def invalidate_cloudfront(self, paths: List[str] = None) -> str:
        """Create CloudFront invalidation"""
        distribution_id = self.get_distribution_id()
        if not distribution_id:
            return None
        
        if paths is None:
            paths = ['/*']
        
        try:
            response = self.cloudfront_client.create_invalidation(
                DistributionId=distribution_id,
                InvalidationBatch={
                    'Paths': {
                        'Quantity': len(paths),
                        'Items': paths
                    },
                    'CallerReference': f"pupper-invalidation-{int(time.time())}"
                }
            )
            
            invalidation_id = response['Invalidation']['Id']
            print(f"✅ CloudFront invalidation created: {invalidation_id}")
            return invalidation_id
            
        except Exception as e:
            print(f"❌ Failed to create invalidation: {e}")
            return None
    
    def wait_for_invalidation(self, invalidation_id: str) -> bool:
        """Wait for CloudFront invalidation to complete"""
        distribution_id = self.get_distribution_id()
        if not distribution_id or not invalidation_id:
            return False
        
        print(f"⏳ Waiting for invalidation {invalidation_id} to complete...")
        
        try:
            waiter = self.cloudfront_client.get_waiter('invalidation_completed')
            waiter.wait(
                DistributionId=distribution_id,
                Id=invalidation_id,
                WaiterConfig={
                    'Delay': 30,
                    'MaxAttempts': 40  # Wait up to 20 minutes
                }
            )
            print("✅ Invalidation completed!")
            return True
            
        except Exception as e:
            print(f"❌ Error waiting for invalidation: {e}")
            return False
    
    def get_distribution_status(self) -> Dict:
        """Get CloudFront distribution status and metrics"""
        distribution_id = self.get_distribution_id()
        if not distribution_id:
            return {}
        
        try:
            response = self.cloudfront_client.get_distribution(Id=distribution_id)
            distribution = response['Distribution']
            
            return {
                'id': distribution_id,
                'domain_name': distribution['DomainName'],
                'status': distribution['Status'],
                'enabled': distribution['DistributionConfig']['Enabled'],
                'price_class': distribution['DistributionConfig']['PriceClass'],
                'last_modified': distribution['LastModifiedTime'].isoformat(),
            }
            
        except Exception as e:
            print(f"❌ Error getting distribution status: {e}")
            return {}
    
    def list_bucket_objects(self, prefix: str = '') -> List[Dict]:
        """List objects in the S3 bucket"""
        bucket_name = self.get_bucket_name()
        if not bucket_name:
            return []
        
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=bucket_name,
                Prefix=prefix
            )
            
            objects = []
            for obj in response.get('Contents', []):
                objects.append({
                    'key': obj['Key'],
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'].isoformat(),
                    'etag': obj['ETag'].strip('"')
                })
            
            return objects
            
        except Exception as e:
            print(f"❌ Error listing bucket objects: {e}")
            return []
    
    def sync_local_to_s3(self, local_path: str, s3_prefix: str = '') -> bool:
        """Sync local directory to S3 bucket"""
        bucket_name = self.get_bucket_name()
        if not bucket_name:
            return False
        
        try:
            import os
            import mimetypes
            
            uploaded_files = []
            
            for root, dirs, files in os.walk(local_path):
                for file in files:
                    local_file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(local_file_path, local_path)
                    s3_key = os.path.join(s3_prefix, relative_path).replace('\\', '/')
                    
                    # Determine content type
                    content_type, _ = mimetypes.guess_type(local_file_path)
                    if content_type is None:
                        content_type = 'binary/octet-stream'
                    
                    # Upload file
                    extra_args = {'ContentType': content_type}
                    
                    # Add cache control headers
                    if any(relative_path.endswith(ext) for ext in ['.css', '.js', '.png', '.jpg', '.svg']):
                        extra_args['CacheControl'] = 'max-age=31536000'  # 1 year
                    elif relative_path.endswith('.html'):
                        extra_args['CacheControl'] = 'max-age=3600'  # 1 hour
                    
                    self.s3_client.upload_file(
                        local_file_path,
                        bucket_name,
                        s3_key,
                        ExtraArgs=extra_args
                    )
                    
                    uploaded_files.append(s3_key)
                    print(f"📤 Uploaded: {s3_key}")
            
            print(f"✅ Uploaded {len(uploaded_files)} files to S3")
            return True
            
        except Exception as e:
            print(f"❌ Error syncing to S3: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(description='Pupper Frontend Management Utilities')
    parser.add_argument('--region', default='us-east-1', help='AWS region')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Invalidate command
    invalidate_parser = subparsers.add_parser('invalidate', help='Create CloudFront invalidation')
    invalidate_parser.add_argument('--paths', nargs='*', default=['/*'], help='Paths to invalidate')
    invalidate_parser.add_argument('--wait', action='store_true', help='Wait for invalidation to complete')
    
    # Status command
    subparsers.add_parser('status', help='Get distribution status')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List S3 bucket objects')
    list_parser.add_argument('--prefix', default='', help='Object prefix filter')
    
    # Sync command
    sync_parser = subparsers.add_parser('sync', help='Sync local directory to S3')
    sync_parser.add_argument('local_path', help='Local directory path')
    sync_parser.add_argument('--prefix', default='', help='S3 prefix')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    manager = PupperFrontendManager(region=args.region)
    
    if args.command == 'invalidate':
        invalidation_id = manager.invalidate_cloudfront(args.paths)
        if invalidation_id and args.wait:
            manager.wait_for_invalidation(invalidation_id)
    
    elif args.command == 'status':
        status = manager.get_distribution_status()
        if status:
            print("📊 CloudFront Distribution Status:")
            for key, value in status.items():
                print(f"  {key}: {value}")
    
    elif args.command == 'list':
        objects = manager.list_bucket_objects(args.prefix)
        if objects:
            print(f"📁 S3 Bucket Objects ({len(objects)} items):")
            for obj in objects:
                print(f"  {obj['key']} ({obj['size']} bytes, {obj['last_modified']})")
        else:
            print("📁 No objects found")
    
    elif args.command == 'sync':
        success = manager.sync_local_to_s3(args.local_path, args.prefix)
        if success:
            print("🎉 Sync completed successfully!")
            # Optionally invalidate after sync
            print("Creating CloudFront invalidation...")
            manager.invalidate_cloudfront()


if __name__ == '__main__':
    main()
