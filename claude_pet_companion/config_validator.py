"""
Configuration Validation System

Provides robust configuration validation with:
- Type checking and conversion
- Range validation
- Schema validation
- Environment variable support
- Configuration migration
"""
import os
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Type, TypeVar, Callable
from dataclasses import dataclass, field, is_dataclass
from enum import Enum
import re
import logging

from .config import PetConfig

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ValidationError(Exception):
    """Raised when configuration validation fails."""

    def __init__(self, field: str, message: str, value: Any = None):
        self.field = field
        self.message = message
        self.value = value
        super().__init__(f"Validation error for '{field}': {message}")


class ValidationWarning(Exception):
    """Raised when a non-critical validation issue is found."""

    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"Validation warning for '{field}': {message}")


@dataclass
class FieldSpec:
    """Specification for a configuration field."""
    name: str
    type: Type
    required: bool = True
    default: Any = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    allowed_values: Optional[List[Any]] = None
    pattern: Optional[str] = None
    env_var: Optional[str] = None
    description: str = ""


class ConfigSchema:
    """Schema definition for configuration validation."""

    def __init__(self):
        self.fields: Dict[str, FieldSpec] = {}

    def add_field(self, spec: FieldSpec):
        """Add a field specification to the schema."""
        self.fields[spec.name] = spec

    def add_fields(self, specs: List[FieldSpec]):
        """Add multiple field specifications to the schema."""
        for spec in specs:
            self.add_field(spec)

    def get_field(self, name: str) -> Optional[FieldSpec]:
        """Get a field specification by name."""
        return self.fields.get(name)

    def has_field(self, name: str) -> bool:
        """Check if a field exists in the schema."""
        return name in self.fields


class ConfigValidator:
    """
    Validates configuration data against a schema.

    Features:
    - Type checking with automatic conversion
    - Range validation for numeric values
    - Pattern matching for strings
    - Enum value validation
    - Environment variable override
    - Default value injection
    """

    def __init__(self, schema: ConfigSchema = None):
        self.schema = schema or ConfigSchema()
        self.warnings: List[ValidationWarning] = []

    def validate(self, config: Dict[str, Any], strict: bool = False) -> Tuple[bool, List[str]]:
        """
        Validate a configuration dictionary.

        Args:
            config: Configuration data to validate
            strict: If True, reject unknown fields

        Returns:
            Tuple of (is_valid, error_messages)
        """
        self.warnings.clear()
        errors = []

        # Check all required fields
        for field_name, spec in self.schema.fields.items():
            try:
                self._validate_field(field_name, config, spec)
            except ValidationError as e:
                errors.append(str(e))

        # Check for unknown fields in strict mode
        if strict:
            for field_name in config:
                if not self.schema.has_field(field_name):
                    errors.append(f"Unknown field: '{field_name}'")

        return len(errors) == 0, errors

    def validate_and_fix(self, config: Dict[str, Any]) -> Tuple[bool, Dict[str, Any], List[str]]:
        """
        Validate configuration and fix issues where possible.

        Returns:
            Tuple of (is_valid, fixed_config, warning_messages)
        """
        self.warnings.clear()
        fixed = {}
        warnings = []

        for field_name, spec in self.schema.fields.items():
            value = config.get(field_name)

            # Try to get from environment
            if spec.env_var:
                env_value = os.environ.get(spec.env_var)
                if env_value is not None:
                    try:
                        value = self._convert_type(env_value, spec.type)
                    except (ValueError, TypeError):
                        warnings.append(f"Failed to convert env var {spec.env_var} for {field_name}")

            # Apply default if missing and not required
            if value is None:
                if spec.required:
                    if spec.default is not None:
                        value = spec.default
                    else:
                        warnings.append(f"Required field '{field_name}' is missing")
                        continue
                else:
                    value = spec.default

            # Validate and convert
            try:
                fixed[field_name] = self._validate_value(field_name, value, spec)
            except ValidationError as e:
                if spec.default is not None:
                    fixed[field_name] = spec.default
                    warnings.append(str(e))
                else:
                    warnings.append(str(e))

        # Copy unknown fields as-is
        for field_name, value in config.items():
            if field_name not in fixed:
                fixed[field_name] = value

        return True, fixed, warnings

    def _validate_field(self, field_name: str, config: Dict[str, Any], spec: FieldSpec):
        """Validate a single field."""
        value = config.get(field_name)

        # Check required
        if value is None:
            if spec.required:
                raise ValidationError(field_name, "Required field is missing", value)
            return  # Optional field with None value is OK

        # Validate type
        value = self._validate_value(field_name, value, spec)

        # Update config with converted value
        config[field_name] = value

    def _validate_value(self, field_name: str, value: Any, spec: FieldSpec) -> Any:
        """Validate and convert a value."""
        # Type conversion
        try:
            value = self._convert_type(value, spec.type)
        except (ValueError, TypeError) as e:
            raise ValidationError(field_name, f"Type conversion failed: {e}", value)

        # Range validation for numbers
        if isinstance(value, (int, float)):
            if spec.min_value is not None and value < spec.min_value:
                raise ValidationError(
                    field_name,
                    f"Value {value} is below minimum {spec.min_value}",
                    value
                )
            if spec.max_value is not None and value > spec.max_value:
                raise ValidationError(
                    field_name,
                    f"Value {value} exceeds maximum {spec.max_value}",
                    value
                )

        # Pattern validation for strings
        if spec.pattern and isinstance(value, str):
            if not re.match(spec.pattern, value):
                raise ValidationError(
                    field_name,
                    f"Value '{value}' does not match pattern '{spec.pattern}'",
                    value
                )

        # Allowed values validation
        if spec.allowed_values and value not in spec.allowed_values:
            raise ValidationError(
                field_name,
                f"Value '{value}' not in allowed values: {spec.allowed_values}",
                value
            )

        return value

    def _convert_type(self, value: Any, target_type: Type) -> Any:
        """Convert a value to the target type."""
        if value is None:
            return None

        # Already the right type
        if isinstance(value, target_type):
            return value

        # Bool special handling
        if target_type is bool:
            if isinstance(value, str):
                return value.lower() in ('true', '1', 'yes', 'on', 'enabled')
            return bool(value)

        # Numeric types
        if target_type is int:
            return int(value)
        if target_type is float:
            return float(value)

        # String
        if target_type is str:
            return str(value)

        # List
        if target_type is list:
            if isinstance(value, str):
                # Comma-separated list
                return [item.strip() for item in value.split(',')]
            return list(value)

        # Dict
        if target_type is dict:
            if isinstance(value, str):
                return json.loads(value)
            return dict(value)

        raise TypeError(f"Cannot convert to type {target_type}")


class PetConfigSchema(ConfigSchema):
    """Schema for PetConfig validation."""

    def __init__(self):
        super().__init__()
        self._build_schema()

    def _build_schema(self):
        """Build the schema with all PetConfig fields."""
        fields = [
            # Window settings
            FieldSpec('width', int, default=240, min_value=100, max_value=1920,
                     env_var='PET_WIDTH', description='Window width in pixels'),
            FieldSpec('height', int, default=280, min_value=100, max_value=1080,
                     env_var='PET_HEIGHT', description='Window height in pixels'),
            FieldSpec('dpi_scale', float, default=1.5, min_value=0.5, max_value=3.0,
                     env_var='PET_DPI_SCALE', description='DPI scaling factor'),

            # Animation settings
            FieldSpec('animation_speed', float, default=1.0, min_value=0.1, max_value=5.0,
                     description='Animation speed multiplier'),
            FieldSpec('float_amplitude', float, default=3.0, min_value=0.0, max_value=20.0,
                     description='Floating animation amplitude'),
            FieldSpec('float_speed', float, default=0.08, min_value=0.01, max_value=0.5,
                     description='Floating animation speed'),
            FieldSpec('breathing_speed', float, default=0.05, min_value=0.01, max_value=0.3,
                     description='Breathing animation speed'),
            FieldSpec('breathing_amplitude', float, default=0.03, min_value=0.0, max_value=0.2,
                     description='Breathing animation amplitude'),

            # Pet info
            FieldSpec('pet_name', str, default='Claude', max_length=50,
                     pattern=r'^[a-zA-Z0-9_\u4e00-\u9fff\s-]+$',
                     env_var='PET_NAME', description='Pet name'),

            # Decay rates
            FieldSpec('hunger_decay', float, default=0.5, min_value=0.0, max_value=10.0,
                     description='Hunger decay per second'),
            FieldSpec('happiness_decay', float, default=0.3, min_value=0.0, max_value=10.0,
                     description='Happiness decay per second'),
            FieldSpec('energy_recovery', float, default=2.0, min_value=0.0, max_value=20.0,
                     description='Energy recovery during sleep'),

            # Theme
            FieldSpec('theme', str, default='default',
                     allowed_values=['default', 'dark', 'light', 'pastel', 'retro'],
                     env_var='PET_THEME', description='Visual theme'),

            # Sound
            FieldSpec('sound_enabled', bool, default=False,
                     env_var='PET_SOUND', description='Enable sound effects'),

            # Particles
            FieldSpec('max_particles', int, default=25, min_value=0, max_value=200,
                     env_var='PET_MAX_PARTICLES', description='Maximum particles'),
            FieldSpec('particle_fade_speed', float, default=1.0, min_value=0.1, max_value=5.0,
                     description='Particle fade speed'),

            # Performance
            FieldSpec('target_fps', int, default=40, min_value=10, max_value=120,
                     env_var='PET_FPS', description='Target frame rate'),
            FieldSpec('enable_performance_mode', bool, default=False,
                     env_var='PET_PERFORMANCE_MODE', description='Enable performance mode'),

            # Warning thresholds
            FieldSpec('hunger_warning', int, default=30, min_value=0, max_value=100,
                     description='Hunger warning threshold'),
            FieldSpec('happiness_warning', int, default=30, min_value=0, max_value=100,
                     description='Happiness warning threshold'),
            FieldSpec('energy_warning', int, default=30, min_value=0, max_value=100,
                     description='Energy warning threshold'),

            # Daemon/IPC
            FieldSpec('daemon_enabled', bool, default=True,
                     env_var='PET_DAEMON', description='Enable daemon mode'),
            FieldSpec('ipc_host', str, default='127.0.0.1',
                     pattern=r'^[\d\.]+$|^localhost$',
                     env_var='PET_IPC_HOST', description='IPC server host'),
            FieldSpec('ipc_port', int, default=15340, min_value=1024, max_value=65535,
                     env_var='PET_IPC_PORT', description='IPC server port'),
            FieldSpec('single_instance', bool, default=True,
                     description='Allow only one instance'),

            # Conversation
            FieldSpec('conversation_enabled', bool, default=True,
                     env_var='PET_CONVERSATIONS', description='Enable conversations'),
            FieldSpec('conversation_auto_save', bool, default=True,
                     description='Auto-save conversations'),
            FieldSpec('max_conversations', int, default=1000, min_value=10, max_value=100000,
                     description='Maximum stored conversations'),
        ]

        # Add max_length validator for strings
        for field in fields:
            if hasattr(field, 'max_length'):
                # Store it for validation
                field._max_length = getattr(field, 'max_length', None)

        self.add_fields(fields)


def validate_pet_config(config: Dict[str, Any], strict: bool = False) -> Tuple[bool, Dict[str, Any], List[str]]:
    """
    Validate and fix a PetConfig dictionary.

    Args:
        config: Configuration data
        strict: If True, reject unknown fields

    Returns:
        Tuple of (is_valid, fixed_config, messages)
    """
    schema = PetConfigSchema()
    validator = ConfigValidator(schema)

    is_valid, fixed, warnings = validator.validate_and_fix(config)

    # Add max_length validation for strings
    for field_name, value in fixed.items():
        spec = schema.get_field(field_name)
        if spec and isinstance(value, str) and hasattr(spec, '_max_length') and spec._max_length:
            if len(value) > spec._max_length:
                fixed[field_name] = value[:spec._max_length]
                warnings.append(f"Field '{field_name}' truncated to {spec._max_length} characters")

    return is_valid, fixed, warnings


def load_validated_config(path: Optional[Path] = None) -> PetConfig:
    """
    Load configuration with validation.

    Args:
        path: Path to config file, or None for default

    Returns:
        Validated PetConfig instance
    """
    if path is None:
        path = Path.home() / '.claude-pet-companion' / 'config.json'

    # Start with default config
    default_config = PetConfig()
    config_dict = {
        'width': default_config.width,
        'height': default_config.height,
        'dpi_scale': default_config.dpi_scale,
        'animation_speed': default_config.animation_speed,
        'float_amplitude': default_config.float_amplitude,
        'float_speed': default_config.float_speed,
        'breathing_speed': default_config.breathing_speed,
        'breathing_amplitude': default_config.breathing_amplitude,
        'pet_name': default_config.pet_name,
        'hunger_decay': default_config.hunger_decay,
        'happiness_decay': default_config.happiness_decay,
        'energy_recovery': default_config.energy_recovery,
        'theme': default_config.theme,
        'sound_enabled': default_config.sound_enabled,
        'max_particles': default_config.max_particles,
        'particle_fade_speed': default_config.particle_fade_speed,
        'target_fps': default_config.target_fps,
        'enable_performance_mode': default_config.enable_performance_mode,
        'hunger_warning': default_config.hunger_warning,
        'happiness_warning': default_config.happiness_warning,
        'energy_warning': default_config.energy_warning,
        'daemon_enabled': default_config.daemon_enabled,
        'ipc_host': default_config.ipc_host,
        'ipc_port': default_config.ipc_port,
        'single_instance': default_config.single_instance,
        'conversation_enabled': default_config.conversation_enabled,
        'conversation_auto_save': default_config.conversation_auto_save,
        'max_conversations': default_config.max_conversations,
    }

    # Load from file if exists
    if path.exists():
        try:
            with open(path, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
                config_dict.update(loaded)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load config from {path}: {e}")

    # Validate and fix
    is_valid, fixed, warnings = validate_pet_config(config_dict)

    for warning in warnings:
        logger.warning(f"Config validation: {warning}")

    # Create PetConfig from fixed dict
    return PetConfig(**fixed)


class ConfigMigration:
    """Handles configuration migration between versions."""

    VERSIONS = {
        '1.0': 1,
        '2.0': 2,
        '2.3': 3,
        '3.0': 4,
    }

    MIGRATIONS = {
        1: [
            # Migration from version 1.0 to 2.0
            lambda config: _migrate_1_to_2(config)
        ],
        2: [
            # Migration from version 2.0 to 2.3
            lambda config: _migrate_2_to_3(config)
        ],
        3: [
            # Migration from version 2.3 to 3.0
            lambda config: _migrate_3_to_4(config)
        ],
    }

    @classmethod
    def migrate(cls, config: Dict[str, Any], from_version: str, to_version: str = '3.0') -> Dict[str, Any]:
        """
        Migrate configuration from one version to another.

        Args:
            config: Configuration dictionary
            from_version: Source version string
            to_version: Target version string

        Returns:
            Migrated configuration dictionary
        """
        from_ver = cls.VERSIONS.get(from_version, 1)
        to_ver = cls.VERSIONS.get(to_version, 4)

        for version in range(from_ver, to_ver):
            migrations = cls.MIGRATIONS.get(version, [])
            for migration in migrations:
                config = migration(config)

        config['config_version'] = to_version
        return config


def _migrate_1_to_2(config: Dict[str, Any]) -> Dict[str, Any]:
    """Migrate from version 1.0 to 2.0."""
    # Add new fields with defaults
    config.setdefault('daemon_enabled', True)
    config.setdefault('ipc_host', '127.0.0.1')
    config.setdefault('ipc_port', 15340)
    config.setdefault('single_instance', True)
    return config


def _migrate_2_to_3(config: Dict[str, Any]) -> Dict[str, Any]:
    """Migrate from version 2.0 to 2.3."""
    # Add conversation settings
    config.setdefault('conversation_enabled', True)
    config.setdefault('conversation_auto_save', True)
    config.setdefault('max_conversations', 1000)
    return config


def _migrate_3_to_4(config: Dict[str, Any]) -> Dict[str, Any]:
    """Migrate from version 2.3 to 3.0."""
    # Add new performance and security settings
    config.setdefault('enable_performance_mode', False)
    config.setdefault('max_particles', min(config.get('max_particles', 25), 200))

    # Ensure theme is valid
    valid_themes = ['default', 'dark', 'light', 'pastel', 'retro']
    if config.get('theme') not in valid_themes:
        config['theme'] = 'default'

    return config


if __name__ == "__main__":
    # Test configuration validation
    print("Testing Configuration Validation")

    test_config = {
        'width': 300,
        'height': 400,
        'pet_name': 'TestPet',
        'animation_speed': 1.5,
        'invalid_field': 'should_warn_in_strict_mode',
    }

    is_valid, fixed, warnings = validate_pet_config(test_config)

    print(f"Valid: {is_valid}")
    print(f"Fixed config: {fixed}")
    print(f"Warnings: {warnings}")

    # Test migration
    old_config = {'width': 200, 'height': 250, 'pet_name': 'OldPet'}
    migrated = ConfigMigration.migrate(old_config.copy(), '1.0', '3.0')
    print(f"\nMigrated config: {migrated}")
