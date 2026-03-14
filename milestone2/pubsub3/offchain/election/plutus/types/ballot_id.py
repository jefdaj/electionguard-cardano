import re
from pydantic.v1 import validator

type BallotId = bytes

class BallotIdHelper:
    """
    Helper class for working with ballot IDs.
    Stores as bytes internally (for PlutusData), but provides string conversion.
    """

    # TODO any need for variants like spoiled-?
    REGEX = re.compile(
        r'^ballot-[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$'
    )

    @staticmethod
    def from_string(ballot_id: str) -> bytes:
        if not BallotIdHelper.validate(ballot_id):
            raise ValueError(
                f"Invalid ballot ID format. Expected 'ballot-<uuid>', got: {ballot_id}"
            )

        return ballot_id.encode('utf-8')

    @staticmethod
    def to_string(ballot_id_bytes: bytes) -> str:
        try:
            decoded = ballot_id_bytes.decode('utf-8')
            if not BallotIdHelper.validate(decoded):
                raise ValueError(f"Decoded ballot ID has invalid format: {decoded}")
            return decoded
        except UnicodeDecodeError as e:
            raise ValueError(f"Invalid UTF-8 bytes for ballot ID: {e}")

    @staticmethod
    def validate(ballot_id: str) -> bool:
        return BallotIdHelper.REGEX.match(ballot_id) is not None

class BallotIdMixin:
    """Mixin that provides ballot_id validation via BallotIdHelper."""

    # TODO any other field names?
    @validator('ballot_id', 'spoiled_id', allow_reuse=True)
    def validate_ballot_id_field(cls, v):
        """Validate any ballot ID field."""
        try:
            ballot_str = v.decode('utf-8')
            if not BallotIdHelper.validate(ballot_str):
                raise ValueError(f"Invalid ballot ID format: {ballot_str}")
        except UnicodeDecodeError:
            raise ValueError("ballot_id must be valid UTF-8")
        return v

# from typing import Optional
# from pycardano import PlutusData
# from pydantic.v1 import validator
#
# # Example PlutusData class using ballot IDs
# class BallotDatum(PlutusData):
#     """
#     Example datum containing a ballot ID.
#     """
#     CONSTR_ID = 0
# 
#     ballot_id: bytes  # Stored as bytes for Plutus
#     # ... other fields
# 
#     @validator('ballot_id')
#     def validate_ballot_id(cls, v):
#         """Validate ballot_id bytes represent a valid ballot ID."""
#         try:
#             ballot_str = v.decode('utf-8')
#             if not BallotIdHelper.validate(ballot_str):
#                 raise ValueError(f"Invalid ballot ID format: {ballot_str}")
#         except UnicodeDecodeError:
#             raise ValueError("ballot_id must be valid UTF-8")
#         return v
# 
#     def get_ballot_id_str(self) -> str:
#         """Helper to get ballot ID as a string."""
#         return BallotIdHelper.to_string(self.ballot_id)
# 
# 
# # Usage examples
# if __name__ == "__main__":
#     import uuid
# 
#     # Generate a UUID and create ballot ID
#     uuid_v1 = uuid.uuid1()
#     full_id = f"ballot-{uuid_v1}"
# 
#     # Convert to bytes
#     ballot_id_bytes = BallotIdHelper.from_string(full_id)
#     print(f"Created ballot ID (bytes): {ballot_id_bytes}")
#     print(f"As string: {BallotIdHelper.to_string(ballot_id_bytes)}")
# 
#     # Create datum
#     datum = BallotDatum(ballot_id=ballot_id_bytes)
#     print(f"\nDatum ballot ID: {datum.get_ballot_id_str()}")
# 
#     # Validation examples
#     print(f"\nValidation tests:")
#     print(f"Valid: {BallotIdHelper.validate('ballot-550e8400-e29b-41d4-a716-446655440000')}")
#     print(f"Invalid (no prefix): {BallotIdHelper.validate('550e8400-e29b-41d4-a716-446655440000')}")
#     print(f"Invalid (wrong format): {BallotIdHelper.validate('ballot-invalid-uuid')}")
