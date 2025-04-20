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

    # Mapping für problematische Location-Werte
    _problematic_location_map = {
        # Allgemeine, nichtssagende Standorte und weitere häufige Platzhalter
        "earth": None,
        "worldwide": None,
        "everywhere": None,
        "all over the world": None,
        "planet earth": None,
        "global": None,
        "around the world": None,
        "the moon": None,
        "moon": None,
        "milky way": None,
        "the universe": None,
        "universe": None,
        "somewhere": None,
        "anywhere": None,
        "here": None,
        "there": None,
        "remote": None,
        "home": None,
        "home office": None,
        "internet": None,
        "on the internet": None,
        "cloud": None,
        "localhost": None,
        "n/a": None,
        "none": None,
        "nowhere": None,
        # Neue explizite Problemfälle:
        "the blockchain": None,
        "blockchain": None,
        # Typische Missverständnisse
        "mountain view, ca": {"country_code": "US", "country": "United States", "region": "California", "latitude": 37.3861, "longitude": -122.0839, "formatted_address": "Mountain View, CA, United States"},
        "new york, ny": {"country_code": "US", "country": "United States", "region": "New York", "latitude": 40.7128, "longitude": -74.0060, "formatted_address": "New York, NY, United States"},
        "san francisco, ca": {"country_code": "US", "country": "United States", "region": "California", "latitude": 37.7749, "longitude": -122.4194, "formatted_address": "San Francisco, CA, United States"},
        "los angeles, ca": {"country_code": "US", "country": "United States", "region": "California", "latitude": 34.0522, "longitude": -118.2437, "formatted_address": "Los Angeles, CA, United States"},
        # Explizite Korrektur für UK
        "uk": {"country_code": "GB", "country": "United Kingdom", "region": None, "latitude": None, "longitude": None, "formatted_address": "United Kingdom"},
        "united kingdom": {"country_code": "GB", "country": "United Kingdom", "region": None, "latitude": None, "longitude": None, "formatted_address": "United Kingdom"},
    }



    # Set of normalized ambiguous/non-geographic terms for fast lookup (for fallback check)
    _ambiguous_terms_set = set(k.lower().strip() for k, v in _problematic_location_map.items() if v is None)

    def __init__(self, cache_file: str = "geocoding_cache.json", user_agent: str = "GitHub-Data-Collector", enable_quality_logging: bool = False):
        self.cache = GeocodingCache(cache_file)
        self.geolocator = Nominatim(user_agent=user_agent)
        self.enable_quality_logging = enable_quality_logging

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
        # 1. Cache-Prüfung
        cached_result = self.cache.get(location)
        if cached_result is not None:
            return cached_result

        # 2. Vorverarbeitung & Normalisierung
        processed_location = self._preprocess_location(location)
        normalized = self._normalize_location(processed_location) if processed_location else ""
        if not processed_location or not normalized:
            self.cache.set(location, {})
            return {}

        # 3. Mapping für explizit problematische/nichtssagende Werte
        if normalized in self._problematic_location_map:
            mapped = self._problematic_location_map[normalized]
            if mapped is None:
                if self.enable_quality_logging:
                    logger.info(f"Location '{location}' ist laut Mapping ein nichtssagender Wert und wird ignoriert.")
                result = {}
            else:
                if self.enable_quality_logging:
                    logger.info(f"Location '{location}' wurde durch Mapping erkannt und zugeordnet: {mapped}")
                result = mapped.copy()
            self.cache.set(location, result)
            return result

        # 4. Alias-Check (direkt, falls vorhanden)
        if normalized in self.country_aliases:
            alias_code = self.country_aliases[normalized]
            country_name = self._get_country_name(alias_code)
            result = {
                "country_code": alias_code,
                "country": country_name,
                "region": None,
                "latitude": None,
                "longitude": None,
                "formatted_address": country_name
            }
            if self.enable_quality_logging:
                logger.info(f"Location '{location}' wurde als Alias erkannt und direkt auf {alias_code} gemappt.")
            self.cache.set(location, result)
            return result

        # 5. Nominatim-Geocoding
        nominatim_result_data = None
        nominatim_failed = False
        try:
            geocode_api_result = self.geolocator.geocode(
                processed_location,
                exactly_one=True,
                language="en",
                addressdetails=True,
                timeout=10
            )
            if geocode_api_result and hasattr(geocode_api_result, 'raw') and isinstance(geocode_api_result.raw, dict):
                address = geocode_api_result.raw.get("address", {})
                api_country_code = address.get("country_code", "").upper()
                api_country = address.get("country", "")
                # Plausibilitätsprüfung: Wenn Input ein Alias (z.B. 'uk'), Output aber nicht der erwartete Code → Fehler!
                if normalized in self.country_aliases:
                    expected_code = self.country_aliases[normalized]
                    if api_country_code != expected_code:
                        logger.warning(f"Alias '{normalized}' ergibt durch Geocoder '{api_country_code}' statt erwartet '{expected_code}'. Fallback wird genutzt.")
                        nominatim_failed = True
                    else:
                        region = self._extract_region(address)
                        nominatim_result_data = {
                            "country_code": api_country_code,
                            "country": api_country,
                            "region": region,
                            "latitude": geocode_api_result.latitude,
                            "longitude": geocode_api_result.longitude,
                            "formatted_address": geocode_api_result.address
                        }
                elif api_country_code and len(api_country_code) == 2 and api_country.lower() != 'earth':
                    region = self._extract_region(address)
                    nominatim_result_data = {
                        "country_code": api_country_code,
                        "country": api_country,
                        "region": region,
                        "latitude": geocode_api_result.latitude,
                        "longitude": geocode_api_result.longitude,
                        "formatted_address": geocode_api_result.address
                    }
                    if self.enable_quality_logging:
                        logger.debug(f"Nominatim successful for '{location}': {nominatim_result_data}")
                else:
                    if self.enable_quality_logging:
                        logger.info(f"Nominatim returned non-specific or invalid country_code ('{api_country_code}') for '{location}'. Treating as not found.")
                    nominatim_failed = True
            else:
                if self.enable_quality_logging:
                    logger.debug(f"Nominatim returned no result for '{location}'.")
                nominatim_failed = True
        except (GeocoderTimedOut, GeocoderUnavailable) as e:
            logger.warning(f"Nominatim Geocoding API error for '{location}': {e}")
            nominatim_failed = True
        except Exception as e:
            logger.error(f"Unexpected Geocoding exception for '{location}': {e}", exc_info=True)
            nominatim_failed = True

        if nominatim_result_data:
            self.cache.set(location, nominatim_result_data)
            return nominatim_result_data

        # 6. Fallback: Textbasierte Extraktion
        if nominatim_failed:
            if self.enable_quality_logging:
                logger.debug(f"Nominatim failed or implausible for '{location}', trying text extraction fallback using _extract_country_from_text.")
            code, region = self._extract_country_from_text(normalized)
            if code:
                country_name = self._get_country_name(code)
                result = {
                    "country_code": code,
                    "country": country_name,
                    "region": region,
                    "latitude": None,
                    "longitude": None,
                    "formatted_address": country_name
                }
                self.cache.set(location, result)
                return result
            else:
                logger.warning(f"Konnte keinen plausiblen Ländercode für '{location}' bestimmen. Leeres Ergebnis wird gecached.")
                self.cache.set(location, {})
                return {}

        # 7. Wenn alles fehlschlägt (Nominatim & Fallback), gib leeres Ergebnis zurück und cache es
        if self.enable_quality_logging:
            logger.warning(f"Could not determine valid geocoding data for location: '{location}' after all attempts.")
        result = {}
        self.cache.set(location, result) # Wichtig: Cache das leere Ergebnis, um wiederholte Fehler zu vermeiden
        return result

    def _preprocess_location(self, location: str) -> Optional[str]:
        """
        Normalisiere und bereinige Standortangaben für bessere Erkennung.
        Entfernt nur überflüssige Leerzeichen und gibt None zurück, wenn leer.
        Kann erweitert werden, um häufige Muster zu bereinigen.
        """
        if not location or not isinstance(location, str):
            return None

        location = location.strip()

        if not location:
            return None

        # Entferne gängige, nichtssagende Zusätze (optional, aber kann helfen)
        location = re.sub(r'\s*,?\s*(remote|home office|anywhere|on the internet|cloud)\s*$', '', location, flags=re.IGNORECASE).strip()
        location = re.sub(r'^\s*(remote|home office|anywhere|on the internet|cloud)\s*,?\s*', '', location, flags=re.IGNORECASE).strip()

        # Entferne URLs
        location = re.sub(r'https?://\S+', '', location).strip()

        # Entferne E-Mail-Adressen
        location = re.sub(r'\S+@\S+', '', location).strip()

        # Entferne typische Platzhalter/ungültige Zeichen, die Probleme machen könnten
        location = location.replace('[','').replace(']','').replace('(','').replace(')','')
        location = location.replace('"','').replace('\'','')

        # Ersetze mehrere Leerzeichen/Kommas durch ein einzelnes Leerzeichen/Komma
        location = re.sub(r'\s+', ' ', location).strip()
        location = re.sub(r',+', ',', location).strip()
        location = re.sub(r'\s*?,\s*', ', ', location).strip() # Einheitliches Format Komma+Leerzeichen

        if not location: # Erneut prüfen nach Bereinigung
             return None

        return location

    def _extract_country_from_text(self, location: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Versucht, aus dem Location-String einen Ländercode und ggf. eine Region zu extrahieren.
        """
        if not location:
            return None, None
        loc = location.lower()
        # US-Staaten Namen und Abkürzungen
        us_states = {
            'alabama': 'US', 'alaska': 'US', 'arizona': 'US', 'arkansas': 'US', 'california': 'US',
            'colorado': 'US', 'connecticut': 'US', 'delaware': 'US', 'florida': 'US', 'georgia': 'US',
            'hawaii': 'US', 'idaho': 'US', 'illinois': 'US', 'indiana': 'US', 'iowa': 'US',
            'kansas': 'US', 'kentucky': 'US', 'louisiana': 'US', 'maine': 'US', 'maryland': 'US',
            'massachusetts': 'US', 'michigan': 'US', 'minnesota': 'US', 'mississippi': 'US', 'missouri': 'US',
            'montana': 'US', 'nebraska': 'US', 'nevada': 'US', 'new hampshire': 'US', 'new jersey': 'US',
            'new mexico': 'US', 'new york': 'US', 'north carolina': 'US', 'north dakota': 'US', 'ohio': 'US',
            'oklahoma': 'US', 'oregon': 'US', 'pennsylvania': 'US', 'rhode island': 'US', 'south carolina': 'US',
            'south dakota': 'US', 'tennessee': 'US', 'texas': 'US', 'utah': 'US', 'vermont': 'US',
            'virginia': 'US', 'washington': 'US', 'west virginia': 'US', 'wisconsin': 'US', 'wyoming': 'US',
            'district of columbia': 'US', 'washington dc': 'US', 'washington d.c.': 'US', 'dc': 'US', 'd.c.': 'US',
            'puerto rico': 'US', 'guam': 'US', 'american samoa': 'US', 'virgin islands': 'US',
            'northern mariana islands': 'US'
        }
        us_state_abbr = {
            'al': 'US', 'ak': 'US', 'az': 'US', 'ar': 'US', 'ca': 'US', 'co': 'US', 'ct': 'US',
            'de': 'US', 'fl': 'US', 'ga': 'US', 'hi': 'US', 'id': 'US', 'il': 'US', 'in': 'US',
            'ia': 'US', 'ks': 'US', 'ky': 'US', 'la': 'US', 'me': 'US', 'md': 'US', 'ma': 'US',
            'mi': 'US', 'mn': 'US', 'ms': 'US', 'mo': 'US', 'mt': 'US', 'ne': 'US', 'nv': 'US',
            'nh': 'US', 'nj': 'US', 'nm': 'US', 'ny': 'US', 'nc': 'US', 'nd': 'US', 'oh': 'US',
            'ok': 'US', 'or': 'US', 'pa': 'US', 'ri': 'US', 'sc': 'US', 'sd': 'US', 'tn': 'US',
            'tx': 'US', 'ut': 'US', 'vt': 'US', 'va': 'US', 'wa': 'US', 'wv': 'US', 'wi': 'US',
            'wy': 'US', 'pr': 'US', 'gu': 'US', 'as': 'US', 'vi': 'US', 'mp': 'US'
        }
        major_us_cities = {
            'new york': 'US', 'new york city': 'US', 'nyc': 'US', 'los angeles': 'US', 'chicago': 'US',
            'houston': 'US', 'phoenix': 'US', 'philadelphia': 'US', 'san antonio': 'US', 'san diego': 'US',
            'dallas': 'US', 'san jose': 'US', 'austin': 'US', 'jacksonville': 'US', 'fort worth': 'US',
            'columbus': 'US', 'san francisco': 'US', 'charlotte': 'US', 'indianapolis': 'US', 'seattle': 'US',
            'denver': 'US', 'boston': 'US', 'portland': 'US', 'las vegas': 'US', 'detroit': 'US', 'atlanta': 'US',
            'miami': 'US', 'minneapolis': 'US', 'pittsburgh': 'US', 'cincinnati': 'US', 'cleveland': 'US',
            'nashville': 'US', 'salt lake city': 'US', 'baltimore': 'US', 'brooklyn': 'US', 'manhattan': 'US',
            'queens': 'US', 'bronx': 'US', 'staten island': 'US', 'silicon valley': 'US', 'bay area': 'US',
            'mountain view': 'US', 'palo alto': 'US', 'menlo park': 'US', 'redwood city': 'US', 'cupertino': 'US',
            'sunnyvale': 'US', 'santa clara': 'US', 'san mateo': 'US', 'berkeley': 'US', 'oakland': 'US', 'san bruno': 'US'
        }
        # 1. US-Staaten Name
        for state in us_states:
            if state == loc or loc.endswith(f", {state}") or f" {state} " in f" {loc} ":
                return 'US', state.title()
        # 2. US-Staaten Abkürzung
        abbr_match = re.search(r',\s*([A-Za-z]{2})$|\s+([A-Za-z]{2})$', loc)
        if abbr_match:
            abbr = next((g.lower() for g in abbr_match.groups() if g is not None), None)
            if abbr in us_state_abbr:
                return 'US', us_state_abbr[abbr].title()
        # 3. Große US-Städte
        for city in major_us_cities:
            if city == loc or loc.startswith(f"{city},") or loc.startswith(f"{city} "):
                return 'US', city.title()
        # 4. Länder-Aliase und Synonyme
        if loc in self.country_aliases:
            return self.country_aliases[loc], None
        # 5. Ländercode am Ende
        match = re.search(r'([A-Z]{2})$', loc.upper())
        if match and match.group(1).lower() in self.country_codes:
            return self.country_codes[match.group(1).lower()], None
        # 6. Mehrere Länder im String
        countries = [c for c in self.country_codes if c in loc]
        if len(countries) > 1:
            return None, None
        return None, None

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
