"""Geocoding-Service für die Umwandlung von Standortangaben in Länder- und Regionsinformationen."""

import os
import json
import logging
import time
import re
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime

import pycountry
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable

logger = logging.getLogger(__name__)

class GeocodingCache:
    """
    Cache für Geocoding-Ergebnisse.
    
    Diese Klasse speichert Geocoding-Ergebnisse, um wiederholte API-Aufrufe zu vermeiden.
    """
    
    def __init__(self, cache_file: str = "geocoding_cache.json"):
        """
        Initialisiere den Geocoding-Cache.
        
        Args:
            cache_file: Pfad zur Cache-Datei
        """
        self.cache_file = cache_file
        self.cache = self._load_cache()
    
    def _load_cache(self) -> Dict[str, Dict[str, Any]]:
        """
        Lade den Cache aus der Datei.
        
        Returns:
            Cache-Daten oder leeres Dictionary, wenn keine Datei existiert
        """
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Fehler beim Laden des Geocoding-Caches: {e}")
        
        return {}
    
    def save(self) -> None:
        """
        Speichere den aktuellen Cache in der Datei.
        """
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, indent=2, ensure_ascii=False)
            logger.debug(f"Geocoding-Cache gespeichert in {self.cache_file}")
        except Exception as e:
            logger.error(f"Fehler beim Speichern des Geocoding-Caches: {e}")
    
    def get(self, location: str) -> Optional[Dict[str, Any]]:
        """
        Rufe ein Geocoding-Ergebnis aus dem Cache ab.
        
        Args:
            location: Standortangabe
            
        Returns:
            Geocoding-Ergebnis oder None, wenn nicht im Cache
        """
        # Normalisiere den Standort für konsistente Schlüssel
        normalized_location = self._normalize_location(location)
        return self.cache.get(normalized_location)
    
    def set(self, location: str, result: Dict[str, Any]) -> None:
        """
        Speichere ein Geocoding-Ergebnis im Cache.
        
        Args:
            location: Standortangabe
            result: Geocoding-Ergebnis
        """
        # Normalisiere den Standort für konsistente Schlüssel
        normalized_location = self._normalize_location(location)
        self.cache[normalized_location] = result
        
        # Speichere den Cache periodisch (nach jeder 10. Aktualisierung)
        if len(self.cache) % 10 == 0:
            self.save()
    
    def _normalize_location(self, location: str) -> str:
        """
        Normalisiere eine Standortangabe für konsistente Cache-Schlüssel.
        
        Args:
            location: Standortangabe
            
        Returns:
            Normalisierte Standortangabe
        """
        if not location:
            return ""
        
        # Entferne Leerzeichen am Anfang und Ende
        normalized = location.strip()
        
        # Konvertiere zu Kleinbuchstaben
        normalized = normalized.lower()
        
        # Entferne mehrfache Leerzeichen
        normalized = re.sub(r'\s+', ' ', normalized)
        
        return normalized

class GeocodingService:
    """
    Service für die Geokodierung von Standortangaben.
    
    Diese Klasse verwendet Geopy und Pycountry, um Standortangaben in
    Länder- und Regionsinformationen umzuwandeln.
    """
    
    def __init__(self, cache_file: str = "geocoding_cache.json", user_agent: str = "GitHub-Data-Collector"):
        """
        Initialisiere den Geocoding-Service.
        
        Args:
            cache_file: Pfad zur Cache-Datei
            user_agent: User-Agent für Nominatim
        """
        self.cache = GeocodingCache(cache_file)
        self.geolocator = Nominatim(user_agent=user_agent)
        
        # Lade Ländercodes für schnelle Lookups
        self.country_codes = {country.name.lower(): country.alpha_2 for country in pycountry.countries}
        self.country_codes.update({country.alpha_2.lower(): country.alpha_2 for country in pycountry.countries})
        self.country_codes.update({country.alpha_3.lower(): country.alpha_2 for country in pycountry.countries})
        
        # Füge alternative Namen für Länder hinzu
        self.country_aliases = {
            "usa": "US",
            "united states": "US",
            "united states of america": "US",
            "u.s.": "US",
            "u.s.a.": "US",
            "america": "US",
            "uk": "GB",
            "united kingdom": "GB",
            "great britain": "GB",
            "england": "GB",
            "russia": "RU",
            "deutschland": "DE",
            "germany": "DE",
            "france": "FR",
            "españa": "ES",
            "espana": "ES",
            "spain": "ES",
            "italia": "IT",
            "italy": "IT",
            "china": "CN",
            "japan": "JP",
            "brasil": "BR",
            "brazil": "BR",
            "canada": "CA",
            "australia": "AU",
            "india": "IN",
            "méxico": "MX",
            "mexico": "MX",
            "netherlands": "NL",
            "holland": "NL",
            "schweiz": "CH",
            "switzerland": "CH",
            "suisse": "CH",
            "sweden": "SE",
            "sverige": "SE",
            "norway": "NO",
            "norge": "NO",
            "denmark": "DK",
            "danmark": "DK",
            "finland": "FI",
            "suomi": "FI",
            "österreich": "AT",
            "osterreich": "AT",
            "austria": "AT",
            "belgium": "BE",
            "belgique": "BE",
            "belgië": "BE",
            "belgie": "BE",
            "portugal": "PT",
            "greece": "GR",
            "ελλάδα": "GR",
            "ellada": "GR",
            "ireland": "IE",
            "éire": "IE",
            "eire": "IE",
            "new zealand": "NZ",
            "south africa": "ZA",
            "south korea": "KR",
            "korea": "KR",
            "north korea": "KP",
            "taiwan": "TW",
            "singapore": "SG",
            "hong kong": "HK",
            "türkiye": "TR",
            "turkiye": "TR",
            "turkey": "TR",
            "israel": "IL",
            "argentina": "AR",
            "chile": "CL",
            "colombia": "CO",
            "peru": "PE",
            "venezuela": "VE",
            "egypt": "EG",
            "مصر": "EG",
            "saudi arabia": "SA",
            "المملكة العربية السعودية": "SA",
            "uae": "AE",
            "united arab emirates": "AE",
            "الإمارات العربية المتحدة": "AE",
            "pakistan": "PK",
            "پاکستان": "PK",
            "bangladesh": "BD",
            "বাংলাদেশ": "BD",
            "vietnam": "VN",
            "việt nam": "VN",
            "thailand": "TH",
            "ประเทศไทย": "TH",
            "malaysia": "MY",
            "indonesia": "ID",
            "philippines": "PH",
            "pilipinas": "PH",
            "new york": "US",
            "california": "US",
            "texas": "US",
            "florida": "US",
            "london": "GB",
            "paris": "FR",
            "berlin": "DE",
            "madrid": "ES",
            "rome": "IT",
            "roma": "IT",
            "tokyo": "JP",
            "東京": "JP",
            "beijing": "CN",
            "北京": "CN",
            "shanghai": "CN",
            "上海": "CN",
            "sydney": "AU",
            "mumbai": "IN",
            "मुंबई": "IN",
            "toronto": "CA",
            "vancouver": "CA",
            "são paulo": "BR",
            "sao paulo": "BR",
            "rio de janeiro": "BR",
            "moscow": "RU",
            "москва": "RU",
            "moskva": "RU",
            "st. petersburg": "RU",
            "saint petersburg": "RU",
            "санкт-петербург": "RU",
            "sankt-peterburg": "RU"
        }
    
    def geocode(self, location: str) -> Dict[str, Any]:
        """
        Geokodiere eine Standortangabe.
        
        Args:
            location: Standortangabe
            
        Returns:
            Dictionary mit Geocoding-Ergebnissen:
            {
                "country_code": "DE",
                "country": "Germany",
                "region": "Berlin",
                "latitude": 52.5200,
                "longitude": 13.4050,
                "formatted_address": "Berlin, Germany"
            }
        """
        if not location or not isinstance(location, str):
            return {}
        
        # Normalisiere die Standortangabe
        location = location.strip()
        
        if not location:
            return {}
        
        # Prüfe, ob das Ergebnis im Cache ist
        cached_result = self.cache.get(location)
        if cached_result is not None:
            return cached_result
        
        # Versuche, den Ländercode direkt aus der Standortangabe zu extrahieren
        country_code = self._extract_country_code(location)
        if country_code:
            result = {
                "country_code": country_code,
                "country": self._get_country_name(country_code),
                "region": "",
                "latitude": None,
                "longitude": None,
                "formatted_address": location
            }
            self.cache.set(location, result)
            return result
        
        # Versuche, die Standortangabe zu geokodieren
        try:
            geocode_result = self.geolocator.geocode(
                location,
                exactly_one=True,
                language="en",
                addressdetails=True,
                timeout=10
            )
            
            if geocode_result:
                # Extrahiere Länder- und Regionsinformationen
                address = geocode_result.raw.get("address", {})
                country_code = address.get("country_code", "").upper()
                country = address.get("country", "")
                
                # Bestimme die Region (Bundesland, Provinz, etc.)
                region = self._extract_region(address)
                
                result = {
                    "country_code": country_code,
                    "country": country,
                    "region": region,
                    "latitude": geocode_result.latitude,
                    "longitude": geocode_result.longitude,
                    "formatted_address": geocode_result.address
                }
            else:
                # Keine Ergebnisse gefunden
                result = {}
            
            # Speichere das Ergebnis im Cache
            self.cache.set(location, result)
            
            # Kurze Pause, um die API nicht zu überlasten
            time.sleep(1)
            
            return result
        
        except (GeocoderTimedOut, GeocoderUnavailable) as e:
            logger.warning(f"Geocoding-Fehler für '{location}': {e}")
            
            # Speichere ein leeres Ergebnis im Cache, um wiederholte Fehler zu vermeiden
            empty_result = {}
            self.cache.set(location, empty_result)
            
            return empty_result
    
    def _extract_country_code(self, location: str) -> Optional[str]:
        """
        Extrahiere den Ländercode aus einer Standortangabe.
        
        Args:
            location: Standortangabe
            
        Returns:
            Ländercode oder None, wenn nicht gefunden
        """
        if not location:
            return None
        
        # Prüfe auf direkte Übereinstimmung mit Ländercode oder -name
        location_lower = location.lower()
        
        # Prüfe auf Aliase
        if location_lower in self.country_aliases:
            return self.country_aliases[location_lower]
        
        # Prüfe auf direkte Übereinstimmung mit Ländercode oder -name
        if location_lower in self.country_codes:
            return self.country_codes[location_lower]
        
        # Prüfe, ob die Standortangabe mit einem Ländercode endet
        words = re.split(r'[,\s]+', location_lower)
        for word in words:
            if word in self.country_codes:
                return self.country_codes[word]
        
        # Prüfe auf Ländercode am Ende der Standortangabe
        match = re.search(r'[,\s]+([A-Za-z]{2})$', location)
        if match and match.group(1).lower() in self.country_codes:
            return self.country_codes[match.group(1).lower()]
        
        return None
    
    def _extract_region(self, address: Dict[str, str]) -> str:
        """
        Extrahiere die Region aus einer Adresse.
        
        Args:
            address: Adressinformationen von Nominatim
            
        Returns:
            Regionname oder leerer String, wenn nicht gefunden
        """
        # Prüfe verschiedene Felder, die die Region enthalten könnten
        region_fields = [
            "state",
            "province",
            "county",
            "region",
            "state_district",
            "city"
        ]
        
        for field in region_fields:
            if field in address and address[field]:
                return address[field]
        
        return ""
    
    def _get_country_name(self, country_code: str) -> str:
        """
        Ermittle den Ländernamen aus einem Ländercode.
        
        Args:
            country_code: ISO-Ländercode (2 Buchstaben)
            
        Returns:
            Ländername oder leerer String, wenn nicht gefunden
        """
        try:
            country = pycountry.countries.get(alpha_2=country_code)
            return country.name if country else ""
        except Exception:
            return ""
    
    def update_location_data(self, entity: Dict[str, Any]) -> Dict[str, Any]:
        """
        Aktualisiere die Standortdaten einer Entität (Contributor oder Organisation).
        
        Args:
            entity: Entitätsdaten mit einem 'location'-Feld
            
        Returns:
            Aktualisierte Entitätsdaten
        """
        location = entity.get("location")
        
        if not location:
            return entity
        
        # Geokodiere die Standortangabe
        geocode_result = self.geocode(location)
        
        if geocode_result:
            # Aktualisiere die Entitätsdaten
            entity["country_code"] = geocode_result.get("country_code", "")
            entity["region"] = geocode_result.get("region", "")
        
        return entity
