# storyjupyter/services/brand.py
import hashlib
from dataclasses import asdict
from datetime import datetime, UTC
from typing import Sequence, TypeVar, Optional
from ..core.models import Brand
from ..core.protocols import BrandManager

T = TypeVar("T")

class DeterministicBrandManager(BrandManager):
    """Implements deterministic brand name generation"""
    
    def __init__(self, seed: int | None = None) -> None:
        self.seed = seed
        self._prefix_pool = [
            "Neo", "Tech", "Cyber", "Data", "Smart", "AI", 
            "Quantum", "Cloud", "Meta", "Omni"
        ]
        self._suffix_pool = [
            "Corp", "Tech", "Systems", "Solutions", "Labs", 
            "Logic", "Dynamics", "Network", "Flow"
        ]
        self._brands: dict[str, Brand] = {}

    def _generate_hash(self, name: str) -> str:
        """Generate deterministic hash for name"""
        seed_str = f"{self.seed}:{name}" if self.seed else name
        return hashlib.blake2b(
            seed_str.encode(), 
            digest_size=8
        ).hexdigest()

    def _create_brand_name(self, hash_val: str) -> str:
        """Create brand name from hash"""
        prefix_idx = int(hash_val[:4], 16) % len(self._prefix_pool)
        suffix_idx = int(hash_val[4:], 16) % len(self._suffix_pool)
        
        return f"{self._prefix_pool[prefix_idx]}{self._suffix_pool[suffix_idx]}"

    def get_brand(self, real_name: str, default: Optional[T] = None) -> Brand | T:
        """Get or generate brand name"""
        if real_name in self._brands:
            return self._brands[real_name]
            
        if default is not None:
            return default
            
        hash_val = self._generate_hash(real_name)
        story_name = self._create_brand_name(hash_val)
        
        brand = Brand(
            real_name=real_name,
            story_name=story_name,
            created_at=datetime.now(UTC)
        )
        self._brands[real_name] = brand
        return brand

    def batch_generate(self, names: Sequence[str]) -> Sequence[Brand]:
        """Generate multiple brand names at once"""
        return [self.get_brand(name) for name in names]

    def validate_name(self, name: str) -> tuple[bool, str]:
        """Validate a brand name"""
        # Simple validation rules
        if len(name) < 3:
            return False, "Name too short"
        if len(name) > 30:
            return False, "Name too long"
        if not name[0].isalpha():
            return False, "Must start with letter"
        if not name.replace(" ", "").isalnum():
            return False, "Only letters, numbers, and spaces allowed"
        return True, "Valid name"