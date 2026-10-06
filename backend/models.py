from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime, timezone
import uuid


class Product(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    product_code: str
    name: str
    slug: str
    category: str
    tagline: str = ""
    description: str = ""
    pixel_pitch: str = ""
    resolution: str = ""
    brightness: str = ""
    application: str = ""
    key_specs: List[Dict[str, str]] = []
    image_url: str = ""
    gallery: List[str] = []
    featured: bool = False
    trending: bool = False
    new_arrival: bool = False
    status: str = "published"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Inspiration(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    slug: str
    category: str
    description: str = ""
    image_url: str
    featured: bool = False
    status: str = "published"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Project(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    slug: str
    client_name: str = ""
    location: str = ""
    sector: str = ""
    screen_size: str = ""
    description: str = ""
    image_url: str
    gallery: List[str] = []
    technologies_used: List[str] = []
    metrics: List[Dict[str, str]] = []
    featured: bool = False
    status: str = "published"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Lead(BaseModel):
    name: str
    company: Optional[str] = None
    email: str
    phone: str = ""
    city: Optional[str] = None
    application: str = ""
    product_interest: Optional[str] = None
    timeline: Optional[str] = None
    budget: Optional[str] = None
    message: Optional[str] = None
    source: str = "contact_form"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    # Honeypot fields — hidden from users, filled by bots
    website: Optional[str] = None
    fax: Optional[str] = None


class AdminLogin(BaseModel):
    email: str
    password: str


class AdminPasswordChange(BaseModel):
    current_password: str
    new_password: str


class AdminProductCreate(BaseModel):
    product_code: str
    name: str
    slug: Optional[str] = None
    category: str
    tagline: str = ""
    description: str = ""
    pixel_pitch: str = ""
    resolution: str = ""
    brightness: str = ""
    application: str = ""
    key_specs: List[Dict[str, str]] = []
    image_url: str = ""
    gallery: List[str] = []
    featured: bool = False
    trending: bool = False
    new_arrival: bool = False
    status: str = "published"


class AdminProductUpdate(BaseModel):
    product_code: Optional[str] = None
    name: Optional[str] = None
    slug: Optional[str] = None
    category: Optional[str] = None
    series: Optional[str] = None
    tagline: Optional[str] = None
    description: Optional[str] = None
    pixel_pitch: Optional[str] = None
    resolution: Optional[str] = None
    brightness: Optional[str] = None
    application: Optional[str] = None
    key_specs: Optional[List[Dict[str, str]]] = None
    image_url: Optional[str] = None
    gallery: Optional[List[str]] = None
    featured: Optional[bool] = None
    trending: Optional[bool] = None
    new_arrival: Optional[bool] = None
    status: Optional[str] = None


class AdminInspirationCreate(BaseModel):
    title: str
    slug: Optional[str] = None
    category: str
    description: str = ""
    image_url: str = ""
    featured: bool = False
    status: str = "published"


class AdminProjectCreate(BaseModel):
    title: str
    slug: Optional[str] = None
    client_name: str = ""
    location: str = ""
    sector: str = ""
    screen_size: str = ""
    description: str = ""
    image_url: str = ""
    gallery: List[str] = []
    technologies_used: List[str] = []
    metrics: List[Dict[str, str]] = []
    featured: bool = False
    status: str = "published"
