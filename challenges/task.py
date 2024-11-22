from datetime import datetime, time
import re
import psycopg2
import select
import json
import yaml
from challenges.cache_graph import build_cache_graph
from challenges.enums import StampType
from challenges.graph import NodeGraph
from challenges.models import BH, BHD, BHSzD, BHSzakasz
import networkx as nx

from django.core.cache import caches

# Use the 'bhpont_memory' cache
bh_memory_cache = caches['bhpont_memory']
szakasz_memory_cache = caches['bhszakasz_memory']
graph_cache = caches['graph_memory']

with open('routing_backend/config.yaml', 'r') as file:
    config = yaml.safe_load(file)

def load_graph_cache():
    """
    Build and cache the graphs for AK, OKT, and DDK trails.
    """
    bhszakasz_cache = get_bhszakasz_cache()
    bh_cache = get_bhpont_cache()
    for trail in ['AK', 'OKT', 'RPDDK']:
        current_bhszakasz = [
            szakasz for szakasz in bhszakasz_cache 
            if szakasz['okk_mozgalom'] == trail and szakasz['end_date'] is None
        ]
        bhszd_sections = [
            BHSzD(
                BHSzakasz(**szakasz),
                validation_time=datetime.now(),  # Default validation time
                mozgalom=trail,
                stamp_type=StampType.DB,  # Default stamp type for this example
                kezdopont=BHD.create_bhd_from_bh_id(szakasz['kezdopont_bh_id'], bh_cache),
                vegpont=BHD.create_bhd_from_bh_id(szakasz['vegpont_bh_id'], bh_cache),
            )
            for szakasz in current_bhszakasz
        ]
        try:
            graph = build_cache_graph(bhszd_sections,trail)
            graph_cache.set(f'{trail}_GRAPH', graph)
        except Exception as e:
            print(f"Error building graph for {trail}: {e}")

        except Exception as main_exception:
            print(f"Unexpected error processing trail {trail}: {main_exception}")
    
        print(f"Finished {trail} Graph",get_graph_cache(trail))

def get_graph_cache(trail: str) -> NodeGraph:
    """
    Retrieve the cached graph for a specific trail.
    """
    return graph_cache.get(f'{trail}_GRAPH', None)

def load_bhszakasz_table():
    """
    Load the kektura.bhszakasz table into memory.
    """

    rows = BHSzakasz.objects.all().values()
    szakasz_memory_cache.set('BHSZAKASZ_CACHE', list(rows))

def get_bhszakasz_cache():
    """
    Retrieve the BHSZAKASZ_CACHE from memory.
    """
    return szakasz_memory_cache.get('BHSZAKASZ_CACHE', [])

def load_bhpont_table():
    """
    Load the `kektura.bhpont` table into the memory cache.
    """
    rows = BH.objects.all().values()
    bh_memory_cache.set('BHPONT_CACHE', list(rows))

def get_bhpont_cache():
    """
    Retrieve the BHPONT_CACHE from memory.
    """
    return bh_memory_cache.get('BHPONT_CACHE', [])

def listen_to_changes():
    conn = psycopg2.connect(
        dbname=config['bh']['Name'],
        user=config['bh']['User'],
        password=config['bh']['Password'],
        host=config['DATABASE']['Host'],
        port=5432
    )
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()

    cur.execute("LISTEN bhpont_changes;")
    cur.execute("LISTEN bhszakasz_changes;")
    print("Listening to `bhpont_changes` and `bhszakasz_changes` notifications...")

    while True:
        if select.select([conn], [], [], 5) == ([], [], []):
            continue
        conn.poll()
        while conn.notifies:
            notify = conn.notifies.pop(0)
            print(f"{datetime.now()} Notification received: {notify.payload}")

            if notify.channel == 'bhpont_changes':
                load_bhpont_table()
            elif notify.channel == 'bhszakasz_changes':
                load_bhszakasz_table()
            load_graph_cache()