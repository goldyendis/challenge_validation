from threading import Thread
from django.apps import AppConfig



class ChallengesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'challenges'

    def ready(self):
        from .task import listen_to_changes,load_bhpont_table, load_bhszakasz_table,load_graph_cache

        load_bhpont_table()
        load_bhszakasz_table()
        load_graph_cache()

        Thread(target=listen_to_changes, daemon=True).start()