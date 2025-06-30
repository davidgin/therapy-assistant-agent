"""
Configuration for free clinical data sources
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

class DataSourceType(Enum):
    """Types of data sources"""
    API = "api"
    DOWNLOAD = "download"
    RSS = "rss"
    WEB_SCRAPE = "web_scrape"

class DataFormat(Enum):
    """Data formats"""
    JSON = "json"
    XML = "xml"
    PDF = "pdf"
    CSV = "csv"
    HTML = "html"
    TEXT = "text"

@dataclass
class DataSource:
    """Configuration for a clinical data source"""
    name: str
    description: str
    url: str
    source_type: DataSourceType
    data_format: DataFormat
    api_key_required: bool = False
    rate_limit: Optional[int] = None  # requests per minute
    update_frequency: str = "daily"  # daily, weekly, monthly
    reliability_score: float = 1.0  # 0.0 to 1.0
    categories: List[str] = None
    
    def __post_init__(self):
        if self.categories is None:
            self.categories = []

# Free Clinical Data Sources Configuration
FREE_CLINICAL_DATA_SOURCES = {
    
    # DSM-5-TR and Clinical Guidelines
    "apa_practice_guidelines": DataSource(
        name="APA Practice Guidelines",
        description="American Psychological Association evidence-based treatment guidelines",
        url="https://www.apa.org/practice/guidelines",
        source_type=DataSourceType.WEB_SCRAPE,
        data_format=DataFormat.PDF,
        reliability_score=0.95,
        categories=["guidelines", "treatment", "evidence-based"]
    ),
    
    "nimh_rdoc": DataSource(
        name="NIMH Research Domain Criteria",
        description="Research Domain Criteria framework for mental health research",
        url="https://www.nimh.nih.gov/research/research-funded-by-nimh/rdoc",
        source_type=DataSourceType.WEB_SCRAPE,
        data_format=DataFormat.HTML,
        reliability_score=0.95,
        categories=["research", "classification", "neuroscience"]
    ),
    
    # WHO and ICD-11 Resources
    "who_icd11": DataSource(
        name="WHO ICD-11 Classification",
        description="World Health Organization International Classification of Diseases 11th Revision",
        url="https://icd.who.int/ct11/icd11_mms/en/release",
        source_type=DataSourceType.API,
        data_format=DataFormat.JSON,
        reliability_score=1.0,
        categories=["classification", "diagnosis", "international"]
    ),
    
    "who_clinical_descriptions": DataSource(
        name="WHO Clinical Descriptions",
        description="Clinical descriptions and diagnostic guidelines from WHO",
        url="https://icd.who.int/docs",
        source_type=DataSourceType.DOWNLOAD,
        data_format=DataFormat.PDF,
        reliability_score=0.95,
        categories=["diagnosis", "clinical", "guidelines"]
    ),
    
    # Research Databases
    "pubmed_central_oa": DataSource(
        name="PubMed Central Open Access",
        description="Freely available full-text articles from PubMed Central",
        url="https://www.ncbi.nlm.nih.gov/pmc/tools/openftlist/",
        source_type=DataSourceType.API,
        data_format=DataFormat.XML,
        api_key_required=True,  # NCBI API key recommended
        rate_limit=10,  # 10 requests per second with API key
        reliability_score=0.90,
        categories=["research", "evidence", "peer-reviewed"]
    ),
    
    "clinical_trials": DataSource(
        name="ClinicalTrials.gov",
        description="Public database of clinical trials worldwide",
        url="https://clinicaltrials.gov/api/query/full_studies",
        source_type=DataSourceType.API,
        data_format=DataFormat.JSON,
        rate_limit=20,  # 20 requests per minute
        reliability_score=0.85,
        categories=["trials", "treatment", "research"]
    ),
    
    # Government Health Resources
    "samhsa_data": DataSource(
        name="SAMHSA Data and Reports",
        description="Substance Abuse and Mental Health Services Administration data",
        url="https://www.samhsa.gov/data/",
        source_type=DataSourceType.WEB_SCRAPE,
        data_format=DataFormat.CSV,
        reliability_score=0.90,
        categories=["epidemiology", "treatment", "statistics"]
    ),
    
    "cdc_mental_health": DataSource(
        name="CDC Mental Health Data",
        description="Centers for Disease Control mental health surveillance data",
        url="https://www.cdc.gov/mentalhealth/data_publications/",
        source_type=DataSourceType.DOWNLOAD,
        data_format=DataFormat.CSV,
        reliability_score=0.90,
        categories=["epidemiology", "public-health", "surveillance"]
    ),
    
    "nimh_statistics": DataSource(
        name="NIMH Mental Health Statistics",
        description="National Institute of Mental Health statistics and fact sheets",
        url="https://www.nimh.nih.gov/health/statistics/",
        source_type=DataSourceType.WEB_SCRAPE,
        data_format=DataFormat.HTML,
        reliability_score=0.95,
        categories=["statistics", "epidemiology", "fact-sheets"]
    ),
    
    # Medical Education Resources
    "medlineplus_mental_health": DataSource(
        name="MedlinePlus Mental Health",
        description="NIH consumer health information on mental health topics",
        url="https://medlineplus.gov/mentalhealth.html",
        source_type=DataSourceType.WEB_SCRAPE,
        data_format=DataFormat.HTML,
        reliability_score=0.85,
        categories=["patient-education", "consumer-health", "topics"]
    ),
    
    # Drug and Treatment Information
    "dailymed": DataSource(
        name="DailyMed Drug Information",
        description="FDA drug labeling information including psychiatric medications",
        url="https://dailymed.nlm.nih.gov/dailymed/",
        source_type=DataSourceType.API,
        data_format=DataFormat.XML,
        reliability_score=0.95,
        categories=["medications", "prescribing", "drug-labels"]
    ),
    
    # Mental Health Screening Tools
    "phq_gad_tools": DataSource(
        name="Public Domain Screening Tools",
        description="Freely available mental health screening instruments",
        url="https://www.phqscreeners.com/",
        source_type=DataSourceType.WEB_SCRAPE,
        data_format=DataFormat.PDF,
        reliability_score=0.90,
        categories=["screening", "assessment", "tools"]
    ),
    
    # International Guidelines
    "nice_guidelines": DataSource(
        name="NICE Mental Health Guidelines",
        description="UK National Institute for Health and Care Excellence guidelines",
        url="https://www.nice.org.uk/guidance/mental-health-and-behavioural-conditions",
        source_type=DataSourceType.WEB_SCRAPE,
        data_format=DataFormat.HTML,
        reliability_score=0.90,
        categories=["guidelines", "international", "evidence-based"]
    ),
    
    # Open Access Datasets
    "openneuro_mental_health": DataSource(
        name="OpenNeuro Mental Health Studies",
        description="Open neuroimaging datasets related to mental health",
        url="https://openneuro.org/",
        source_type=DataSourceType.API,
        data_format=DataFormat.JSON,
        reliability_score=0.80,
        categories=["neuroimaging", "research-data", "open-science"]
    ),
    
    # Professional Organization Resources
    "apa_divisions": DataSource(
        name="APA Division Resources",
        description="American Psychological Association division-specific resources",
        url="https://www.apa.org/about/division/",
        source_type=DataSourceType.WEB_SCRAPE,
        data_format=DataFormat.HTML,
        reliability_score=0.85,
        categories=["professional", "specialty", "resources"]
    )
}

# Categories for organizing data sources
DATA_CATEGORIES = {
    "guidelines": "Clinical practice guidelines and recommendations",
    "research": "Peer-reviewed research articles and studies", 
    "classification": "Diagnostic classification systems",
    "treatment": "Treatment protocols and interventions",
    "evidence-based": "Evidence-based practices and protocols",
    "epidemiology": "Population health and epidemiological data",
    "statistics": "Mental health statistics and prevalence data",
    "screening": "Assessment and screening tools",
    "medications": "Psychiatric medication information",
    "patient-education": "Patient and consumer education materials",
    "international": "International guidelines and standards",
    "research-data": "Raw research datasets",
    "professional": "Professional organization resources"
}

def get_sources_by_category(category: str) -> List[DataSource]:
    """Get all data sources for a specific category"""
    return [
        source for source in FREE_CLINICAL_DATA_SOURCES.values()
        if category in source.categories
    ]

def get_high_reliability_sources(min_score: float = 0.90) -> List[DataSource]:
    """Get data sources with reliability score above threshold"""
    return [
        source for source in FREE_CLINICAL_DATA_SOURCES.values()
        if source.reliability_score >= min_score
    ]

def get_api_sources() -> List[DataSource]:
    """Get data sources that provide APIs"""
    return [
        source for source in FREE_CLINICAL_DATA_SOURCES.values()
        if source.source_type == DataSourceType.API
    ]

def get_downloadable_sources() -> List[DataSource]:
    """Get data sources that provide direct downloads"""
    return [
        source for source in FREE_CLINICAL_DATA_SOURCES.values()
        if source.source_type == DataSourceType.DOWNLOAD
    ]