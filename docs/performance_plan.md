# Performance-Optimierungsplan für GitHub Data Collector

## Übersicht

Dieses Dokument beschreibt einen Plan zur Optimierung der Performance des GitHub Data Collectors, insbesondere im Hinblick auf die Sammlung großer Datenmengen (2,5+ Millionen Repositories).

## 1. Parallelisierung und Asynchronität

### Geschätzter Aufwand
- **Grundlegende Umstellung auf asyncio**: 2-3 Tage
- **Vollständige Integration mit Thread-Pools**: 3-4 Tage
- **Testen und Optimieren**: 1-2 Tage
- **Gesamtaufwand**: 6-9 Tage

### Mögliche Risiken
1. **Transaktionskonsistenz**: Bei paralleler Verarbeitung könnten Datenbankzugriffe zu Race Conditions führen
   - **Lösung**: Verwendung von Transaktionen und Locks für kritische Operationen
   
2. **Error Handling**: Fehlerbehandlung wird komplexer in asynchronem Code
   - **Lösung**: Robuste try/except/finally-Blöcke und zentralisiertes Error Handling

3. **API-Rate-Limits**: Parallele Anfragen könnten schneller zu Rate-Limit-Überschreitungen führen
   - **Lösung**: Implementierung eines Token-Buckets und Ratenbegrenzung

### Modularer Aufbau
Die Umstellung sollte in folgender Reihenfolge erfolgen:

1. **API-Aufrufe** (höchste Priorität)
   ```python
   async def get_contributor_async(self, username: str) -> Dict[str, Any]:
       """Asynchrone Version von get_contributor."""
       loop = asyncio.get_event_loop()
       with concurrent.futures.ThreadPoolExecutor() as executor:
           return await loop.run_in_executor(
               executor, 
               lambda: self.get_contributor(username)
           )
   ```

2. **Batch-Verarbeitung** (mittlere Priorität)
   ```python
   async def _collect_contributors_metadata_batch_async(self, contributor_logins: List[str]) -> None:
       """Asynchrone Version der Batch-Verarbeitung."""
       tasks = []
       for login in contributor_logins:
           if login not in self._contributor_cache:
               tasks.append(self._get_contributor_data_async(login))
       
       await asyncio.gather(*tasks)
   ```

3. **Datenbankoperationen** (niedrigere Priorität)
   ```python
   async def insert_contributor_async(self, contributor_data: dict) -> Contributor:
       """Asynchrone Version von insert_contributor."""
       loop = asyncio.get_event_loop()
       with concurrent.futures.ThreadPoolExecutor() as executor:
           return await loop.run_in_executor(
               executor, 
               lambda: self.insert_contributor(contributor_data)
           )
   ```

### Worker-Queue-Struktur

```python
class WorkerQueue:
    def __init__(self, max_workers: int = 10, max_queue_size: int = 100):
        self.queue = asyncio.Queue(maxsize=max_queue_size)
        self.workers = [self._worker() for _ in range(max_workers)]
        self.results = []
    
    async def _worker(self):
        while True:
            task, args, kwargs = await self.queue.get()
            try:
                result = await task(*args, **kwargs)
                self.results.append(result)
            except Exception as e:
                logger.error(f"Fehler bei der Aufgabenausführung: {e}")
            finally:
                self.queue.task_done()
    
    async def add_task(self, task, *args, **kwargs):
        await self.queue.put((task, args, kwargs))
    
    async def join(self):
        await self.queue.join()
        return self.results
```

## 2. Bulk-Datenbankoperationen

### Geschätzter Aufwand
- **Implementierung von Bulk-Operationen**: 1-2 Tage
- **Testen und Optimieren**: 1 Tag
- **Gesamtaufwand**: 2-3 Tage

### Beispielimplementierung

```python
def bulk_insert_contributors(self, contributors_data: List[Dict[str, Any]]) -> List[Contributor]:
    """Fügt mehrere Contributors in einem Batch in die Datenbank ein."""
    # Sammle IDs der vorhandenen Contributors
    existing_ids = {c.id for c in self.session.query(Contributor.id).all()}
    
    # Teile in neue und vorhandene Contributors auf
    new_contributors = []
    existing_contributors = []
    
    for data in contributors_data:
        if data['id'] in existing_ids:
            existing_contributors.append(data)
        else:
            new_contributors.append(data)
    
    # Bulk-Insert für neue Contributors
    if new_contributors:
        self.session.bulk_insert_mappings(Contributor, new_contributors)
    
    # Update für vorhandene Contributors
    for data in existing_contributors:
        existing = self.session.query(Contributor).filter_by(id=data['id']).first()
        self.update_contributor(existing, data)
    
    self.session.commit()
    
    # Gib die eingefügten/aktualisierten Contributors zurück
    contributor_ids = [data['id'] for data in contributors_data]
    return self.session.query(Contributor).filter(Contributor.id.in_(contributor_ids)).all()
```

### Vorteile
- Reduziert die Anzahl der Datenbankoperationen erheblich
- Verbessert die Performance bei großen Datenmengen
- Reduziert die Transaktionsoverhead

### Nachteile
- Komplexere Fehlerbehandlung
- Schwierigere Nachverfolgung einzelner Operationen

## 3. Caching-Optimierungen

### Geschätzter Aufwand
- **Implementierung eines persistenten Caches**: 1-2 Tage
- **Integration mit dem bestehenden Code**: 1 Tag
- **Gesamtaufwand**: 2-3 Tage

### Beispielimplementierung

```python
class PersistentCache:
    def __init__(self, cache_file: str = "cache.db"):
        self.cache_file = cache_file
        self.conn = sqlite3.connect(cache_file)
        self._init_db()
    
    def _init_db(self):
        cursor = self.conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS cache (
            key TEXT PRIMARY KEY,
            value TEXT,
            timestamp REAL
        )
        """)
        self.conn.commit()
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT value FROM cache WHERE key = ?", (key,))
        result = cursor.fetchone()
        if result:
            return json.loads(result[0])
        return None
    
    def set(self, key: str, value: Dict[str, Any]):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO cache (key, value, timestamp) VALUES (?, ?, ?)",
            (key, json.dumps(value), time.time())
        )
        self.conn.commit()
    
    def close(self):
        self.conn.close()
```

## 4. GraphQL-Migration

### Geschätzter Aufwand
- **Implementierung der GraphQL-Schnittstelle**: 3-4 Tage
- **Migration bestehender Endpunkte**: 2-3 Tage
- **Testen und Optimieren**: 2 Tage
- **Gesamtaufwand**: 7-9 Tage

### Beispiel-GraphQL-Query

```graphql
query($owner: String!, $name: String!) {
  repository(owner: $owner, name: $name) {
    name
    description
    stargazerCount
    forkCount
    owner {
      ... on User {
        id
        login
        name
        location
        company
      }
      ... on Organization {
        id
        login
        name
        location
        description
      }
    }
    mentionableUsers(first: 1) {
      totalCount  # Contributor-Count
    }
  }
}
```

### Vorteile
- Drastische Reduzierung der API-Aufrufe
- Bessere Kontrolle über die abgefragten Daten
- Effizientere Datenübertragung

### Nachteile
- Komplexere Implementierung
- Höhere Lernkurve
- Möglicherweise andere Rate-Limit-Regeln

## Empfohlene Reihenfolge der Implementierung

1. **Parallelisierung der API-Aufrufe** (höchste Priorität)
   - Bietet den größten Performance-Gewinn
   - Relativ einfach zu implementieren

2. **Bulk-Datenbankoperationen** (mittlere Priorität)
   - Reduziert Datenbankoverhead
   - Verbessert die Performance bei großen Datenmengen

3. **Persistenter Cache** (mittlere Priorität)
   - Reduziert redundante API-Aufrufe zwischen Programmläufen
   - Relativ einfach zu implementieren

4. **GraphQL-Migration** (niedrigere Priorität)
   - Langfristige Lösung für API-Effizienz
   - Erfordert umfangreichere Änderungen

## Fazit

Die vorgeschlagenen Optimierungen würden die Performance des GitHub Data Collectors erheblich verbessern und ihn für die Sammlung großer Datenmengen (2,5+ Millionen Repositories) geeignet machen. Die Implementierung sollte schrittweise erfolgen, beginnend mit der Parallelisierung der API-Aufrufe, da diese den größten Performance-Gewinn verspricht.
