

from django.core.management.base import BaseCommand
from django.conf import settings
import os
import mysql.connector
import requests
import json
from time import sleep
from geopy.distance import geodesic
from typing import Dict, List, Tuple, Optional, Union
import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from elasticsearch import Elasticsearch, helpers
from elasticsearch.exceptions import ApiError, ElasticsearchWarning
import warnings


class OverpassAPI:
    def __init__(self, radius: int = 5000):
        self.session = self._create_session()
        self.base_url = "https://overpass-api.de/api/interpreter"
        self.radius = radius
        
    @staticmethod
    def _create_session() -> requests.Session:
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def get_amenities(self, lat: float, lon: float) -> Dict[str, int]:
        amenities = {
            "hospital": ["amenity", "hospital"],
            "gym": ["leisure", "fitness_centre"],
            "cafe": ["amenity", "cafe"],
            "restaurant": ["amenity", "restaurant"],
            "park": ["leisure", "park"],
            "mall": ["shop", "mall"],
            "atm": ["amenity", "atm"],
            "stationery": ["shop", "stationery"],
            "police": ["amenity", "police"]
        }
        
        results = {}
        for amenity_name, (key, value) in amenities.items():
            query = f"""
            [out:json][timeout:25];
            (
              node["{key}"="{value}"](around:{self.radius},{lat},{lon});
              way["{key}"="{value}"](around:{self.radius},{lat},{lon});
              relation["{key}"="{value}"](around:{self.radius},{lat},{lon});
            );
            out center;
            """
            
            try:
                response = self.session.post(
                    self.base_url, 
                    data={"data": query}, 
                    timeout=30
                )
                response.raise_for_status()
                data = response.json()
                results[amenity_name] = self._count_unique_locations(data.get("elements", []))
                sleep(1)  # Rate limiting to avoid hitting API limits
            except Exception as e:
                logging.error(f"Error fetching {amenity_name} at ({lat}, {lon}): {e}")
                results[amenity_name] = 0
                
        return results

    def _count_unique_locations(self, elements: List[Dict], max_distance: int = 1000) -> int:
        """Count unique locations, considering points within max_distance meters as the same location"""
        unique_locations = []
        
        for element in elements:
            # Get coordinates from element
            if "lat" in element and "lon" in element:
                point = (element["lat"], element["lon"])
            elif "center" in element:
                point = (element["center"]["lat"], element["center"]["lon"])
            else:
                continue
                
     
            is_unique = True
            for existing_point in unique_locations:
                if geodesic(point, existing_point).meters < max_distance:
                    is_unique = False
                    break
                    
            if is_unique:
                unique_locations.append(point)
                
        return len(unique_locations)

warnings.filterwarnings("ignore", category=ElasticsearchWarning)

class Command(BaseCommand):
    help = 'Fetch and store college amenities data from Overpass API to Elasticsearch'

    def add_arguments(self, parser):
        parser.add_argument(
            '--workers',
            type=int,
            default=5,
            help='Number of worker threads'
        )
        parser.add_argument(
            '--radius',
            type=int,
            default=5000,
            help='Search radius in meters for amenities'
        )
        parser.add_argument(
            '--use-master',
            action='store_true',
            help='Use master database instead of slave'
        )

    def handle(self, *args, **options):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            filename=f'college_amenities_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
        )
        
        try:
            self.stdout.write(self.style.SUCCESS('Starting college amenities update...'))
            
            db = DatabaseConnection(use_master=options['use_master'])
            api = OverpassAPI(radius=options['radius'])
            es_uploader = ElasticsearchUploader(
                es_host= os.getenv('ES_HOST', 'https://elastic.careers360.de'),
                es_index=os.getenv('ES_INDEX', 'college__amenities')
            )
            
            colleges = db.fetch_colleges()
            self.stdout.write(f'Fetched {len(colleges)} colleges')
            
            with ThreadPoolExecutor(max_workers=options['workers']) as executor:
                results = list(executor.map(
                    lambda college: self._process_college(college, api),
                    colleges
                ))
            
            valid_results = [r for r in results if r is not None]
            es_uploader.upload_college_data(valid_results)
            
            self.stdout.write(self.style.SUCCESS(
                f'Successfully processed {len(valid_results)} colleges'
            ))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error in command execution: {str(e)}'))
            raise

    def _process_college(self, college: Tuple[int, float, float], api: OverpassAPI) -> Optional[Dict]:
        college_id, lat, lon = college
        self.stdout.write(f'Processing college {college_id} at ({lat}, {lon})')
        
        try:
            amenities = api.get_amenities(lat, lon)
            amenities = self._apply_manual_caps(amenities)
            return {
                "college_id": college_id,
                "location": {"lat": lat, "lon": lon},
                "amenities": amenities,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'Error processing college {college_id}: {str(e)}')
            )
            return None

    def _apply_manual_caps(self, amenities: Dict[str, int]) -> Dict[str, int]:
        caps = {
            "police": 1,
            "hospital": 5,
            "atm": 10,
            "cafe": 10,
            "park": 5,
            "mall": 5,
            "restaurant": 10,
            "stationery": 10
        }
        return {
            amenity: min(count, caps.get(amenity, count))
            for amenity, count in amenities.items()
        }


class DatabaseConnection:
    def __init__(self, use_master: bool = False):
        self.connection = None
        self.use_master = use_master
        
    def connect(self):
        try:
            if self.use_master:
                config = {
                    'host': os.getenv('MASTER_DB_HOST'),
                    'database': os.getenv('MASTER_DB_NAME'),
                    'user': os.getenv('MASTER_DB_USER'),
                    'password':  os.getenv('MASTER_DB_PASSWORD'),
                    'port': os.getenv('MASTER_DB_PORT')
                }
            else:
                config = {
                    'host': os.getenv('SLAVE_DB_HOST'),
                    'database': os.getenv('SLAVE_DB_NAME'),
                    'user': os.getenv('SLAVE_DB_USER'),
                    'password':  os.getenv('SLAVE_DB_PASSWORD'),
                    'port': os.getenv('SLAVE_DB_PORT')
                }
            
            self.connection = mysql.connector.connect(**config)
            
        except mysql.connector.Error as err:
            logging.error(f"Database connection failed: {err}")
            raise

    def fetch_colleges(self) -> List[Tuple[int, float, float]]:
        cursor = None
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()
                
            cursor = self.connection.cursor()
            query = """
                SELECT college.id, location.lat, location.lng 
                FROM colleges AS college
                JOIN location ON location.id = college.location_id
                WHERE college.published = 'published' 
                AND location.lng != 0 
                AND location.lat != 0 
            """
            cursor.execute(query)
            return cursor.fetchall()
        except mysql.connector.Error as err:
            logging.error(f"Error fetching colleges: {err}")
            raise
        finally:
            if cursor:
                cursor.close()
            if self.connection:
                self.connection.close()


class OverpassAPI:
    def __init__(self, radius: int = 5000):
        self.session = self._create_session()
        self.base_url = "https://overpass-api.de/api/interpreter"
        self.radius = radius
        
    @staticmethod
    def _create_session() -> requests.Session:
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def get_amenities(self, lat: float, lon: float) -> Dict[str, int]:
        amenities = {
            "hospital": ["amenity", "hospital"],
            "gym": ["leisure", "fitness_centre"],
            "cafe": ["amenity", "cafe"],
            "restaurant": ["amenity", "restaurant"],
            "park": ["leisure", "park"],
            "mall": ["shop", "mall"],
            "atm": ["amenity", "atm"],
            "stationery": ["shop", "stationery"],
            "police": ["amenity", "police"]
        }
        
        results = {}
        for amenity_name, (key, value) in amenities.items():
            query = self._build_query(lat, lon, key, value)
            try:
                response = self.session.post(self.base_url, data={"data": query}, timeout=30)
                response.raise_for_status()
                data = response.json()
                results[amenity_name] = self._aggregate_elements(data.get("elements", []))
                sleep(1)  # Rate limiting
            except Exception as e:
                logging.error(f"Error fetching {amenity_name} at ({lat}, {lon}): {e}")
                results[amenity_name] = 0
        return results

    def _build_query(self, lat: float, lon: float, key: str, value: str) -> str:
        return f"""
        [out:json][timeout:25];
        (
          node(around:{self.radius},{lat},{lon})["{key}"="{value}"];
          way(around:{self.radius},{lat},{lon})["{key}"="{value}"];
          relation(around:{self.radius},{lat},{lon})["{key}"="{value}"];
        );
        out center;
        """

    @staticmethod
    def _aggregate_elements(elements: List[Dict], max_distance: int = 1000) -> int:
        coords = []
        for element in elements:
            if "lat" in element and "lon" in element:
                coord = (element["lat"], element["lon"])
            elif "center" in element:
                coord = (element["center"]["lat"], element["center"]["lon"])
            else:
                continue
                
            if not any(geodesic(coord, existing_coord).meters < max_distance 
                      for existing_coord in coords):
                coords.append(coord)
        return len(coords)


class ElasticsearchUploader:
    def __init__(self, es_host: str, es_index: str):
        self.es_host = os.getenv('ES_HOST', 'https://elastic.careers360.de'),
        self.es_index = os.getenv('ES_INDEX', 'college__amenities')
        self.es_client = self._create_client()
        self.batch_size = 1000
        
    def _create_client(self) -> Elasticsearch:
        try:
            client = Elasticsearch(
                self.es_host,
                retry_on_timeout=True,
                max_retries=3,
                request_timeout=9000,
                verify_certs=True,
            )
            if not client.ping():
                raise ConnectionError("Could not connect to Elasticsearch")
            return client
        except Exception as e:
            logging.error(f"Failed to create Elasticsearch client: {e}")
            raise

    def _create_index_if_not_exists(self) -> None:
        if not self.es_client.indices.exists(index=self.es_index):
            mapping = {
                "mappings": {
                    "properties": {
                        "college_id": {"type": "keyword"},
                        "location": {"type": "geo_point"},
                        "amenities": {
                            "properties": {
                                "hospital": {"type": "integer"},
                                "gym": {"type": "integer"},
                                "cafe": {"type": "integer"},
                                "restaurant": {"type": "integer"},
                                "park": {"type": "integer"},
                                "mall": {"type": "integer"},
                                "atm": {"type": "integer"},
                                "stationery": {"type": "integer"},
                                "police": {"type": "integer"}
                            }
                        },
                        "timestamp": {"type": "date"}
                    }
                },
                "settings": {
                    "number_of_shards": 3,
                    "number_of_replicas": 1
                }
            }
            self.es_client.indices.create(index=self.es_index, body=mapping)
            logging.info(f"Created new index: {self.es_index}")

    def _prepare_document(self, college_data: Dict) -> Dict:
        return {
            "_index": self.es_index,
            "_id": str(college_data["college_id"]),
            "_source": {
                "college_id": str(college_data["college_id"]),
                "location": college_data["location"],
                "amenities": college_data["amenities"],
                "timestamp": college_data["timestamp"]
            }
        }

    def upload_college_data(self, college_data: Union[Dict, List[Dict]]) -> None:
        try:
            self._create_index_if_not_exists()
            
            documents = college_data if isinstance(college_data, list) else [college_data]
            actions = [self._prepare_document(doc) for doc in documents]
            
            for i in range(0, len(actions), self.batch_size):
                batch = actions[i:i + self.batch_size]
                success, failed = helpers.bulk(
                    self.es_client,
                    batch,
                    stats_only=True,
                    raise_on_error=False
                )
                
                logging.info(f"Batch upload completed: {success} successful, {failed} failed")
                
                if failed > 0:
                    logging.warning(f"Failed to upload {failed} documents in batch")
                    
        except ApiError as e:
            logging.error(f"Elasticsearch error during upload: {e}")
            raise
        except Exception as e:
            logging.error(f"Unexpected error during upload: {e}")
            raise
            
    def close(self) -> None:
        if self.es_client:
            self.es_client.close()