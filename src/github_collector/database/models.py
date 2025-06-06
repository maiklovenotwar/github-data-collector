"""Datenbankmodelle für GitHub-Daten."""

from datetime import datetime
from typing import Optional, List
import os
import logging

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime,
    ForeignKey, Text, create_engine, func, desc
)
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.orm import relationship, declarative_base, sessionmaker

logger = logging.getLogger(__name__)

Base = declarative_base()

class Contributor(Base):
    """Contributor-Modell für GitHub-Benutzer."""
    __tablename__ = 'contributors'
    
    id = Column(Integer, primary_key=True)
    login = Column(String(255), nullable=False, unique=True)
    name = Column(String(255))
    email = Column(String(255))
    type = Column(String(50))
    avatar_url = Column(String(255))
    company = Column(String(255))
    blog = Column(String(255))
    location = Column(String(255))
    country_code = Column(String(2))  # ISO-Ländercode
    region = Column(String(100))  # Region innerhalb des Landes oder Kontinents
    bio = Column(Text)
    twitter_username = Column(String(50))
    public_repos = Column(Integer)
    public_gists = Column(Integer)
    followers = Column(Integer)
    following = Column(Integer)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    
    # Beziehungen
    owned_repositories = relationship('Repository', foreign_keys='Repository.owner_id', back_populates='owner')

class Organization(Base):
    """Organisations-Modell für GitHub-Organisationen."""
    __tablename__ = 'organizations'
    
    id = Column(Integer, primary_key=True)
    login = Column(String(255), nullable=False, unique=True)
    name = Column(String(255))
    email = Column(String(255))
    type = Column(String(50))
    avatar_url = Column(String(255))
    company = Column(String(255))
    blog = Column(String(255))
    location = Column(String(255))
    country_code = Column(String(2))  # ISO-Ländercode
    region = Column(String(100))  # Region innerhalb des Landes oder Kontinents
    bio = Column(Text)
    twitter_username = Column(String(50))
    public_repos = Column(Integer)
    public_gists = Column(Integer)
    followers = Column(Integer)
    following = Column(Integer)
    public_members = Column(Integer)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    
    # Beziehungen
    repositories = relationship('Repository', back_populates='organization')

class Repository(Base):
    """Repository-Modell für GitHub-Repositories."""
    __tablename__ = 'repositories'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False, unique=True)
    owner_id = Column(Integer, ForeignKey('contributors.id'), nullable=False)
    organization_id = Column(Integer, ForeignKey('organizations.id'))
    
    # Metadaten
    description = Column(Text().with_variant(LONGTEXT(), "mysql"), nullable=True)
    homepage = Column(String(255))
    language = Column(String(100))
    private = Column(Boolean, default=False)
    fork = Column(Boolean, default=False)
    default_branch = Column(String(100))
    size = Column(Integer)
    
    # GitHub API-Statistiken
    stargazers_count = Column(Integer, default=0)
    watchers_count = Column(Integer, default=0)
    forks_count = Column(Integer, default=0)
    open_issues_count = Column(Integer, default=0)
    
    # Zusätzliche Statistiken
    contributors_count = Column(Integer)
    commits_count = Column(Integer)
    pull_requests_count = Column(Integer)
    
    # Zeitstempel
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    pushed_at = Column(DateTime)
    
    # Beziehungen
    owner = relationship('Contributor', foreign_keys=[owner_id], back_populates='owned_repositories')
    organization = relationship('Organization', back_populates='repositories')
